#!/usr/bin/env python3
"""
kb_lib — deterministyczny rdzeń skilla knowledge-base.

Logika, która MUSI być powtarzalna (a nie "policz w głowie" przez LLM):
  - similarity / decyzja anti-duplicate (Pass 3)
  - ROI score
  - normalizacja priorytetów (Pass 4, anty-inflacja)
  - fuzzy match nazwy do skills_catalog (Pass 2 → [FIX] vs [NEW])
  - progi wystąpień per typ

Bez zależności zewnętrznych (tylko stdlib). Skill woła te funkcje przez
`python3 scripts/kb_lib.py <komenda> ...` albo importuje w teście.

Użycie CLI (zwraca JSON na stdout):
  python3 scripts/kb_lib.py dedup   --draft draft.json --existing existing.json
  python3 scripts/kb_lib.py roi      --occurrences 10 --sources 2 --time-saved 120 --impl M
  python3 scripts/kb_lib.py catalog  --name nowy-mail --catalog config/skills_catalog.yaml
  python3 scripts/kb_lib.py normalize --entries entries.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

# --- Stałe (lustro config/sources.yaml → classification_thresholds) -----------

# Progi minimalne wystąpień per typ. Trzymane też w config/sources.yaml;
# tu jako fallback gdy config niepodany. Źródłem prawdy jest config.
DEFAULT_THRESHOLDS: dict[str, int] = {
    "SOP": 2,
    "Skill Backlog": 3,
    "n8n Automation": 2,
}

# Faktor wielkości wdrożenia do ROI (Krok 4 SKILL.md).
IMPL_FACTOR: dict[str, int] = {"S": 1, "M": 4, "L": 12}

# Wagi similarity (Pass 3 anti-duplicate, SKILL.md Krok 3).
W_TITLE = 0.4
W_SKILL_NAME = 0.4
W_USER = 0.2

# Progi decyzji dedup.
MERGE_AT = 0.75
FLAG_AT = 0.55

TITLE_PREFIX_RE = re.compile(r"^\s*\[(NEW|FIX|BUG)\]\s*", re.IGNORECASE)
# token "słowo" — litery (z polskimi), cyfry, myślnik wewnątrz slugów
_TOKEN_RE = re.compile(r"[0-9a-ząćęłńóśźż\-]+", re.UNICODE)


# --- Normalizacja tekstu ------------------------------------------------------

def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Lowercase + bez akcentów (ł→l ręcznie, bo NFKD go nie rozkłada)."""
    text = (text or "").lower().replace("ł", "l")
    return _strip_accents(text)


def tokenize(text: str) -> set[str]:
    """Zbiór tokenów do Jaccarda. Pomija daty ISO i prefiksy [NEW]/[FIX]/[BUG]."""
    text = TITLE_PREFIX_RE.sub("", text or "")
    text = normalize(text)
    # usuń daty YYYY-MM-DD i samodzielny separator "·"
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)
    toks = set(_TOKEN_RE.findall(text))
    # odfiltruj jednoznakowe i czysty separator
    return {t for t in toks if len(t) > 1}


# --- Jaccard / similarity (Pass 3) -------------------------------------------

def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def skill_name_from_title(title: str) -> str:
    """Wyciąga slug z Title: '[FIX] 2026-05-11 · Michał · off-brand-voice — opis'
    → 'off-brand-voice'. Heurystyka: segment po ostatnim '·' przed '—'."""
    t = TITLE_PREFIX_RE.sub("", title or "")
    # odetnij opis po myślniku em/zwykłym
    t = re.split(r"\s[—-]\s", t, maxsplit=1)[0]
    parts = [p.strip() for p in t.split("·") if p.strip()]
    if not parts:
        return ""
    cand = parts[-1]
    # pomiń jeśli to data
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cand) and len(parts) >= 2:
        cand = parts[-2]
    return normalize(cand).strip()


def similarity(draft: dict, existing: dict) -> float:
    """similarity = 0.4*jaccard(titles) + 0.4*skill_name_match + 0.2*user_match.
    draft/existing: dict z kluczami 'title' i 'user' (user opcjonalny)."""
    j = jaccard(tokenize(draft.get("title", "")), tokenize(existing.get("title", "")))
    n1 = skill_name_from_title(draft.get("title", ""))
    n2 = skill_name_from_title(existing.get("title", ""))
    name_match = 1.0 if (n1 and n1 == n2) else (0.0 if not (n1 and n2) else jaccard(n1.split("-"), n2.split("-")))
    u1 = normalize(str(draft.get("user", "") or ""))
    u2 = normalize(str(existing.get("user", "") or ""))
    user_match = 1.0 if (u1 and u1 == u2) else 0.0
    return round(W_TITLE * j + W_SKILL_NAME * name_match + W_USER * user_match, 4)


def dedup_action(sim: float) -> str:
    """≥0.75 MERGE · 0.55-0.74 FLAG · <0.55 CREATE."""
    if sim >= MERGE_AT:
        return "MERGE"
    if sim >= FLAG_AT:
        return "FLAG"
    return "CREATE"


def best_match(draft: dict, candidates: list[dict]) -> dict:
    """Znajdź najbardziej podobny istniejący wpis. Zwraca dict z decyzją."""
    best = None
    best_sim = -1.0
    for c in candidates:
        s = similarity(draft, c)
        if s > best_sim:
            best_sim, best = s, c
    return {
        "similarity": max(best_sim, 0.0),
        "action": dedup_action(best_sim) if best is not None else "CREATE",
        "match": best,
    }


# --- Fuzzy match do skills_catalog (Pass 2 → [FIX]/[NEW]/POMIŃ) --------------

def levenshtein(a: str, b: str) -> int:
    a, b = normalize(a), normalize(b)
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def catalog_match(name: str, catalog_names: Iterable[str], max_distance: int = 3) -> dict:
    """Czy proponowana nazwa skilla istnieje już w katalogu?
    Match = substring LUB Levenshtein <= max_distance. Zwraca {matched, distance, reason}."""
    n = normalize(name)
    best = {"matched": None, "distance": 999, "reason": "none"}
    for cn in catalog_names:
        c = normalize(cn)
        # substring (np. 'ewidencja-godzinowa' ⊂ 'ewidencja-godzinowa-miesieczna');
        # próg min. długości chroni przed trywialnym dopasowaniem krótkich fragmentów
        if n and (n in c or c in n) and min(len(n), len(c)) >= 4:
            return {"matched": cn, "distance": 0, "reason": "substring"}
        d = levenshtein(n, c)
        if d < best["distance"]:
            best = {"matched": cn, "distance": d, "reason": "levenshtein"}
    if best["distance"] <= max_distance:
        return best
    return {"matched": None, "distance": best["distance"], "reason": "no-match"}


# --- ROI score (Krok 4) -------------------------------------------------------

def roi_score(occurrences: int, sources: int, time_saved_min: int, impl_size: str) -> float:
    """ROI = occurrences × sources × time_saved_min / impl_factor."""
    factor = IMPL_FACTOR.get((impl_size or "M").upper(), IMPL_FACTOR["M"])
    occ = max(int(occurrences or 0), 0)
    src = max(int(sources or 1), 1)
    ts = max(int(time_saved_min or 0), 0)
    return round(occ * src * ts / factor, 2)


# --- Progi wystąpień ----------------------------------------------------------

def meets_threshold(entry_type: str, occurrences: int, thresholds: dict[str, int] | None = None) -> bool:
    th = (thresholds or DEFAULT_THRESHOLDS).get(entry_type)
    if th is None:
        return True  # nieznany typ — nie blokuj tutaj
    return int(occurrences or 0) >= th


# --- Normalizacja priorytetów (Pass 4, anty-inflacja) ------------------------

@dataclass
class PriorityChange:
    id: str
    before: str
    after: str
    score: float


def normalize_priorities(entries: list[dict], high_cap: float = 0.35,
                         high_target: float = 0.20) -> dict:
    """Jeśli High% > high_cap → zostaw top (high_target × total) High'ów wg score,
    resztę zdegraduj do Medium. entries: [{id, priority, score}]. Mutuje kopie.
    Zwraca {entries, changes, high_pct_before, high_pct_after}."""
    out = [dict(e) for e in entries]
    total = len(out)
    if total == 0:
        return {"entries": out, "changes": [], "high_pct_before": 0.0, "high_pct_after": 0.0}

    highs = [e for e in out if str(e.get("priority", "")).lower() == "high"]
    high_before = len(highs) / total
    if high_before <= high_cap:
        return {"entries": out, "changes": [],
                "high_pct_before": round(high_before, 4), "high_pct_after": round(high_before, 4)}

    keep = max(1, round(total * high_target))
    highs_sorted = sorted(highs, key=lambda e: float(e.get("score", 0)), reverse=True)
    demote = highs_sorted[keep:]
    demote_ids = {id(e) for e in demote}
    changes: list[dict] = []
    for e in out:
        if id(e) in demote_ids:
            changes.append(PriorityChange(str(e.get("id", "")), "High", "Medium",
                                          float(e.get("score", 0))).__dict__)
            e["priority"] = "Medium"
    high_after = sum(1 for e in out if str(e.get("priority", "")).lower() == "high") / total
    return {"entries": out, "changes": changes,
            "high_pct_before": round(high_before, 4), "high_pct_after": round(high_after, 4)}


# --- CLI ----------------------------------------------------------------------

def _load_json_arg(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_catalog_names(path: str) -> list[str]:
    import yaml  # tylko w CLI; testy nie wymagają yaml
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    names: list[str] = []
    for section in ("base_off", "extended_uao", "extended_extra"):
        for item in data.get(section, []) or []:
            if isinstance(item, dict) and item.get("name"):
                names.append(item["name"])
    return names


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="kb_lib — deterministyczny rdzeń knowledge-base")
    sub = p.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("dedup", help="similarity draftu vs lista istniejących")
    pd.add_argument("--draft", required=True)
    pd.add_argument("--existing", required=True)

    pr = sub.add_parser("roi")
    pr.add_argument("--occurrences", type=int, required=True)
    pr.add_argument("--sources", type=int, required=True)
    pr.add_argument("--time-saved", type=int, required=True)
    pr.add_argument("--impl", required=True)

    pc = sub.add_parser("catalog", help="czy nazwa istnieje w skills_catalog → [FIX]")
    pc.add_argument("--name", required=True)
    pc.add_argument("--catalog", required=True)
    pc.add_argument("--max-distance", type=int, default=3)

    pn = sub.add_parser("normalize")
    pn.add_argument("--entries", required=True)

    args = p.parse_args(argv)

    if args.cmd == "dedup":
        draft = _load_json_arg(args.draft)
        existing = _load_json_arg(args.existing)
        if isinstance(existing, dict):
            existing = [existing]
        print(json.dumps(best_match(draft, existing), ensure_ascii=False, indent=2))
    elif args.cmd == "roi":
        print(json.dumps({"roi_score": roi_score(args.occurrences, args.sources,
                                                  args.time_saved, args.impl)}, ensure_ascii=False))
    elif args.cmd == "catalog":
        names = _load_catalog_names(args.catalog)
        res = catalog_match(args.name, names, args.max_distance)
        res["prefix_hint"] = "[FIX]" if res["matched"] else "[NEW]"
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "normalize":
        entries = _load_json_arg(args.entries)
        print(json.dumps(normalize_priorities(entries), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
