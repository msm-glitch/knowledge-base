#!/usr/bin/env python3
"""
kb_setup — walidacja i pomoc w uzupełnieniu configu (item #1).

Problem: system "działa" z niedokończonym configem (puste Notion Person ID,
puste Slack channel_id) i po cichu produkuje złą atrybucję / nie skanuje
5 z 6 kanałów. To gate: PRE-FLIGHT skilla woła `validate` i NIE rusza
skanu, jeśli są błędy krytyczne (tylko ostrzega przy 'warn').

Komendy:
  python3 scripts/kb_setup.py validate            # raport czytelny
  python3 scripts/kb_setup.py validate --json      # maszynowo, exit!=0 gdy błędy
  python3 scripts/kb_setup.py resolve              # CO i SKĄD uzupełnić

`resolve` NIE odpytuje żywych usług (to robi LLM przez MCP). Wypisuje listę
brakujących pól + dokładną instrukcję skąd wziąć każdą wartość, plus gotowy
fragment YAML do wklejenia.

Wymaga PyYAML. Uruchamiać z roota repo.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import yaml

NOTION = os.path.join("config", "notion.yaml")
SOURCES = os.path.join("config", "sources.yaml")

# osoby świadomie bez konta Notion → fallback tekstowy (nie błąd)
FALLBACK_USERS = {"krzysztof", "roksana"}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate() -> dict:
    """Zwraca {ok, errors[], warnings[], summary}."""
    errors: list[str] = []
    warnings: list[str] = []

    if not os.path.exists(NOTION):
        errors.append(f"Brak {NOTION}")
    if not os.path.exists(SOURCES):
        errors.append(f"Brak {SOURCES}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    notion = _load(NOTION)
    sources = _load(SOURCES)

    # 1) Notion DB IDs muszą być wypełnione (krytyczne)
    dbs = notion.get("databases", {}) or {}
    for k in ("knowledge_base", "sops", "skills_backlog"):
        if not str(dbs.get(k, "")).strip():
            errors.append(f"notion.yaml → databases.{k} puste (krytyczne — bez tego brak zapisu)")

    # 2) Notion Person IDs — puste = ostrzeżenie (fallback zadziała, ale atrybucja słabsza)
    users = notion.get("users", {}) or {}
    missing_ids = [name for name, val in users.items()
                   if name not in FALLBACK_USERS and not str(val or "").strip()]
    if missing_ids:
        warnings.append("notion.yaml → users bez Person ID (wpisy trafią do User name fallback): "
                        + ", ".join(sorted(missing_ids)))
    fallback_marked = [n for n, v in users.items() if str(v).strip().upper() == "FALLBACK"]

    # 3) Slack channel_ids — kanał enabled bez ID = krytyczne (nie zeskanuje się)
    slack = (sources.get("sources", {}) or {}).get("slack", {}) or {}
    if slack.get("enabled"):
        ids = slack.get("channel_ids", {}) or {}
        declared = slack.get("channels", []) or []
        missing_ch = [ch for ch in declared if not str(ids.get(ch, "")).strip()]
        if missing_ch:
            errors.append("sources.yaml → slack.channel_ids puste dla kanałów "
                          f"(nie zostaną zeskanowane): {', '.join(missing_ch)}")

    # 4) progi obecne
    ct = sources.get("classification_thresholds", {}) or {}
    for k in ("sop_min_occurrences", "skill_min_occurrences", "n8n_min_occurrences"):
        if k not in ct:
            warnings.append(f"sources.yaml → classification_thresholds.{k} brak — użyję domyślnej")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "notion_users_with_id": sum(1 for v in users.values() if str(v or "").strip()
                                        and str(v).strip().upper() != "FALLBACK"),
            "notion_users_total": len(users),
            "notion_users_fallback": fallback_marked,
            "slack_channels_with_id": sum(1 for v in (slack.get("channel_ids", {}) or {}).values()
                                          if str(v or "").strip()),
        },
    }


def resolve() -> list[dict]:
    """Lista braków + skąd je wziąć (instrukcja dla człowieka/LLM)."""
    out: list[dict] = []
    notion = _load(NOTION) if os.path.exists(NOTION) else {}
    sources = _load(SOURCES) if os.path.exists(SOURCES) else {}

    users = notion.get("users", {}) or {}
    for name, val in sorted(users.items()):
        if name in FALLBACK_USERS:
            continue
        if not str(val or "").strip():
            out.append({
                "field": f"config/notion.yaml → users.{name}",
                "how": "Notion → Settings → My account → 'User ID' (osoby {n}). "
                       "Albo przez MCP: notion-get-users i dopasuj po imieniu/emailu.".format(n=name),
                "yaml": f'  {name}: "<NOTION_PERSON_ID>"',
            })

    slack = (sources.get("sources", {}) or {}).get("slack", {}) or {}
    ids = slack.get("channel_ids", {}) or {}
    for ch, val in ids.items():
        if not str(val or "").strip():
            out.append({
                "field": f"config/sources.yaml → slack.channel_ids.{ch}",
                "how": f"Slack: prawy klik na #{ch} → 'Copy link' → ID z URL (C...). "
                       f"Albo przez MCP: slack_search_channels query='{ch}'.",
                "yaml": f'    {ch}: "C........"',
            })
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="kb_setup — walidacja configu knowledge-base")
    sub = p.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("validate")
    pv.add_argument("--json", action="store_true")
    sub.add_parser("resolve")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        res = validate()
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("config/ — walidacja knowledge-base\n")
            s = res.get("summary", {})
            if s:
                print(f"  Notion users z ID : {s.get('notion_users_with_id')}/{s.get('notion_users_total')}"
                      f"  (fallback: {', '.join(s.get('notion_users_fallback', [])) or '—'})")
                print(f"  Slack kanały z ID : {s.get('slack_channels_with_id')}")
            print()
            for e in res["errors"]:
                print(f"  ❌ BŁĄD: {e}")
            for w in res["warnings"]:
                print(f"  ⚠️  {w}")
            if res["ok"]:
                print("\n  ✅ Config gotowy do skanu (brak błędów krytycznych).")
            else:
                print("\n  ⛔ Skan ZABLOKOWANY — napraw błędy krytyczne. Uruchom: "
                      "python3 scripts/kb_setup.py resolve")
        return 0 if res["ok"] else 1

    if args.cmd == "resolve":
        items = resolve()
        if not items:
            print("✅ Nic do uzupełnienia — config kompletny.")
            return 0
        print(f"Do uzupełnienia: {len(items)} pól\n")
        for it in items:
            print(f"• {it['field']}")
            print(f"    skąd: {it['how']}")
            print(f"    yaml: {it['yaml']}\n")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
