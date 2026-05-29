#!/usr/bin/env python3
"""
kb_state — trwała pamięć knowledge-base między uruchomieniami (item #4).

Rozwiązuje dwa braki "BEZ SQLite / BEZ /runs/":
  1. Akumulacja occurrences MIĘDZY skanami. Skill wymaga ≥3 wystąpień, ale
     wzorzec widziany 1×/tydzień nigdy nie zliczy się bez pamięci. Ledger
     kandydatów (state/candidates.json) przechowuje subprogowe wzorce i je
     dolicza, aż osiągną próg → wtedy promocja do Notion.
  2. Watermark per źródło (state/watermarks.json) — od kiedy skanować, żeby
     weekly nie czytał wszystkiego od nowa i nie produkował duplikatów.

Klucz kandydata = f"{type}::{slug}" (slug znormalizowany). To deterministyczne,
więc dwa skany tego samego wzorca trafią w ten sam wpis.

Pliki są commitowane do repo (małe, czytelne, audytowalne). Tylko stdlib.

CLI:
  python3 scripts/kb_state.py record --type "Skill Backlog" --slug off-x \
      --date 2026-05-20 --source "Claude Chat" --user Michał --url https://... \
      [--state state/candidates.json]
  python3 scripts/kb_state.py ready  --thresholds config/sources.yaml
  python3 scripts/kb_state.py promote --key "Skill Backlog::off-x"
  python3 scripts/kb_state.py get-watermark --source gmail
  python3 scripts/kb_state.py set-watermark --source gmail --ts 2026-05-20T10:00:00
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

CANDIDATES_DEFAULT = os.path.join("state", "candidates.json")
WATERMARKS_DEFAULT = os.path.join("state", "watermarks.json")

DEFAULT_THRESHOLDS = {"SOP": 2, "Skill Backlog": 3, "n8n Automation": 2}


def _slug(text: str) -> str:
    text = (text or "").lower().replace("ł", "l")
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text.strip())
    return re.sub(r"-{2,}", "-", text).strip("-")


def candidate_key(entry_type: str, slug: str) -> str:
    return f"{entry_type}::{_slug(slug)}"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Ledger kandydatów --------------------------------------------------------

def load_candidates(path: str = CANDIDATES_DEFAULT) -> dict:
    if not os.path.exists(path):
        return {"version": 1, "candidates": {}}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("candidates", {})
    return data


def save_candidates(data: dict, path: str = CANDIDATES_DEFAULT) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def record_occurrence(data: dict, entry_type: str, slug: str, date: str | None = None,
                      source: str | None = None, user: str | None = None,
                      url: str | None = None) -> dict:
    """Dolicza wystąpienie do kandydata (tworzy jeśli nie istnieje). Idempotentne
    względem (slug, url): ten sam url nie zwiększy occurrences dwa razy."""
    key = candidate_key(entry_type, slug)
    c = data["candidates"].get(key)
    if c is None:
        c = {"type": entry_type, "slug": _slug(slug), "occurrences": 0,
             "sources": [], "users": [], "source_urls": [],
             "first_seen": date or _now(), "last_seen": date or _now(),
             "promoted": False}
        data["candidates"][key] = c

    # idempotencja po URL (jeśli podany i już znany — nie licz ponownie)
    new_evidence = True
    if url:
        if url in c["source_urls"]:
            new_evidence = False
        else:
            c["source_urls"].append(url)

    if new_evidence:
        c["occurrences"] += 1
    if source and source not in c["sources"]:
        c["sources"].append(source)
    if user and user not in c["users"]:
        c["users"].append(user)
    if date:
        c["last_seen"] = max(c["last_seen"], date)
        c["first_seen"] = min(c["first_seen"], date)
    return c


def ready_to_promote(data: dict, thresholds: dict[str, int] | None = None) -> list[dict]:
    """Kandydaci którzy osiągnęli próg i nie są jeszcze wypromowani."""
    th = thresholds or DEFAULT_THRESHOLDS
    out = []
    for key, c in sorted(data["candidates"].items()):
        if c.get("promoted"):
            continue
        need = th.get(c["type"], 1)
        if c["occurrences"] >= need:
            out.append({"key": key, **c, "threshold": need})
    return out


def mark_promoted(data: dict, key: str) -> bool:
    c = data["candidates"].get(key)
    if not c:
        return False
    c["promoted"] = True
    c["promoted_at"] = _now()
    return True


# --- Watermarki per źródło ----------------------------------------------------

def load_watermarks(path: str = WATERMARKS_DEFAULT) -> dict:
    if not os.path.exists(path):
        return {"version": 1, "sources": {}}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("sources", {})
    return data


def save_watermarks(data: dict, path: str = WATERMARKS_DEFAULT) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def get_watermark(data: dict, source: str) -> str | None:
    return data["sources"].get(source)


def set_watermark(data: dict, source: str, ts: str) -> None:
    data["sources"][source] = ts


# --- threshold loader (z config/sources.yaml) --------------------------------

def load_thresholds(config_path: str | None) -> dict[str, int]:
    if not config_path or not os.path.exists(config_path):
        return dict(DEFAULT_THRESHOLDS)
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        ct = cfg.get("classification_thresholds", {}) or {}
        return {
            "SOP": int(ct.get("sop_min_occurrences", 2)),
            "Skill Backlog": int(ct.get("skill_min_occurrences", 3)),
            "n8n Automation": int(ct.get("n8n_min_occurrences", 2)),
        }
    except Exception:
        return dict(DEFAULT_THRESHOLDS)


# --- CLI ----------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="kb_state — ledger kandydatów + watermarki")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("record")
    pr.add_argument("--type", required=True, dest="etype")
    pr.add_argument("--slug", required=True)
    pr.add_argument("--date")
    pr.add_argument("--source")
    pr.add_argument("--user")
    pr.add_argument("--url")
    pr.add_argument("--state", default=CANDIDATES_DEFAULT)

    pq = sub.add_parser("ready")
    pq.add_argument("--thresholds", help="ścieżka do config/sources.yaml")
    pq.add_argument("--state", default=CANDIDATES_DEFAULT)

    pp = sub.add_parser("promote")
    pp.add_argument("--key", required=True)
    pp.add_argument("--state", default=CANDIDATES_DEFAULT)

    gw = sub.add_parser("get-watermark")
    gw.add_argument("--source", required=True)
    gw.add_argument("--state", default=WATERMARKS_DEFAULT)

    sw = sub.add_parser("set-watermark")
    sw.add_argument("--source", required=True)
    sw.add_argument("--ts", required=True)
    sw.add_argument("--state", default=WATERMARKS_DEFAULT)

    args = p.parse_args(argv)

    if args.cmd == "record":
        data = load_candidates(args.state)
        c = record_occurrence(data, args.etype, args.slug, args.date,
                              args.source, args.user, args.url)
        save_candidates(data, args.state)
        print(json.dumps(c, ensure_ascii=False, indent=2))
    elif args.cmd == "ready":
        data = load_candidates(args.state)
        th = load_thresholds(args.thresholds)
        print(json.dumps(ready_to_promote(data, th), ensure_ascii=False, indent=2))
    elif args.cmd == "promote":
        data = load_candidates(args.state)
        ok = mark_promoted(data, args.key)
        save_candidates(data, args.state)
        print(json.dumps({"promoted": ok, "key": args.key}, ensure_ascii=False))
    elif args.cmd == "get-watermark":
        data = load_watermarks(args.state)
        print(json.dumps({"source": args.source, "watermark": get_watermark(data, args.source)},
                         ensure_ascii=False))
    elif args.cmd == "set-watermark":
        data = load_watermarks(args.state)
        set_watermark(data, args.source, args.ts)
        save_watermarks(data, args.state)
        print(json.dumps({"source": args.source, "watermark": args.ts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
