#!/usr/bin/env python3
"""
skill_manifest — gate instalowalności skilla w Claude.

Problem: żeby `SKILL.md` dał się wgrać do Claude jako skill, MUSI mieć poprawny
frontmatter YAML (`name` + `description`) zgodny ze specyfikacją Agent Skills.
Bez tego instalacja się nie powiedzie po cichu. To odpowiednik `kb_setup.py`
(gate configu), ale dla samego manifestu skilla — deterministyczny, testowalny.

Reguły (spec Claude Agent Skills):
  • frontmatter YAML na początku pliku, wydzielony liniami `---`.
  • `name`  — wymagany, kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`), 1..64 znaków.
             Powinien zgadzać się z nazwą katalogu skilla (ostrzeżenie).
  • `description` — wymagany, niepusty, ≤ 1024 znaki. Powinien mówić CO robi
             i KIEDY użyć (ostrzeżenie, jeśli bardzo krótki).
  • dozwolone klucze top-level: name, description, license, allowed-tools,
             metadata (inne → ostrzeżenie).

Komendy:
  python3 scripts/skill_manifest.py validate            # raport czytelny
  python3 scripts/skill_manifest.py validate --json      # maszynowo, exit!=0 gdy błędy
  python3 scripts/skill_manifest.py validate --file path/to/SKILL.md

Wymaga PyYAML. Uruchamiać z roota repo.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import yaml

DEFAULT_SKILL = "SKILL.md"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESC_MAX = 1024
DESC_MIN_WARN = 40
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}


def split_frontmatter(text: str):
    """Zwraca (frontmatter_str | None, body). Frontmatter = blok między dwoma `---`
    na samym początku pliku (dozwolony BOM / puste linie przed pierwszym `---`)."""
    stripped = text.lstrip("﻿")
    if not stripped.startswith("---"):
        return None, text
    lines = stripped.splitlines()
    # pierwsza linia to '---' (może mieć trailing spaces)
    if lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:])
            return fm, body
    return None, text  # brak domykającego `---`


def validate(path: str = DEFAULT_SKILL) -> dict:
    """Zwraca {ok, errors[], warnings[], summary}."""
    errors: list[str] = []
    warnings: list[str] = []

    if not os.path.exists(path):
        return {"ok": False, "errors": [f"Brak pliku {path}"], "warnings": []}

    with open(path, encoding="utf-8") as f:
        text = f.read()

    fm_str, _ = split_frontmatter(text)
    if fm_str is None:
        return {
            "ok": False,
            "errors": [f"{path}: brak frontmattera YAML (`---` ... `---`) — skill NIE wgra się do Claude"],
            "warnings": [],
        }

    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError as exc:
        return {"ok": False, "errors": [f"{path}: frontmatter to niepoprawny YAML ({exc})"], "warnings": []}

    if not isinstance(fm, dict):
        return {"ok": False, "errors": [f"{path}: frontmatter musi być mapą klucz→wartość"], "warnings": []}

    name = fm.get("name")
    desc = fm.get("description")

    # name
    if not name or not str(name).strip():
        errors.append("frontmatter → name: brak (wymagany)")
    else:
        name = str(name).strip()
        if not NAME_RE.match(name):
            errors.append(f"frontmatter → name '{name}': musi być kebab-case (^[a-z0-9]+(-[a-z0-9]+)*$)")
        if len(name) > NAME_MAX:
            errors.append(f"frontmatter → name: {len(name)} znaków (max {NAME_MAX})")
        # zgodność z nazwą katalogu skilla
        skill_dir = os.path.basename(os.path.dirname(os.path.abspath(path))) or ""
        if skill_dir and skill_dir not in (".", "/") and name != skill_dir:
            warnings.append(f"name '{name}' != nazwa katalogu '{skill_dir}' "
                            "(Claude oczekuje zgodności przy instalacji katalogowej)")

    # description
    if not desc or not str(desc).strip():
        errors.append("frontmatter → description: brak (wymagany)")
    else:
        desc = str(desc).strip()
        if len(desc) > DESC_MAX:
            errors.append(f"frontmatter → description: {len(desc)} znaków (max {DESC_MAX})")
        elif len(desc) < DESC_MIN_WARN:
            warnings.append(f"description krótki ({len(desc)} zn.) — dodaj CO robi i KIEDY użyć (triggery)")

    # nieznane klucze
    unknown = sorted(set(fm.keys()) - ALLOWED_KEYS)
    if unknown:
        warnings.append("nietypowe klucze top-level frontmattera (Claude może je zignorować): "
                        + ", ".join(unknown))

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "name": fm.get("name"),
            "description_len": len(str(desc)) if desc else 0,
            "keys": sorted(fm.keys()),
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="skill_manifest — gate instalowalności skilla")
    sub = p.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("validate")
    pv.add_argument("--json", action="store_true")
    pv.add_argument("--file", default=DEFAULT_SKILL, help="ścieżka do SKILL.md (domyślnie ./SKILL.md)")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        res = validate(args.file)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"SKILL.md — gate instalowalności ({args.file})\n")
            s = res.get("summary", {})
            if s:
                print(f"  name             : {s.get('name')}")
                print(f"  description (zn.): {s.get('description_len')}/{DESC_MAX}")
                print(f"  klucze           : {', '.join(s.get('keys', [])) or '—'}")
            print()
            for e in res["errors"]:
                print(f"  ❌ BŁĄD: {e}")
            for w in res["warnings"]:
                print(f"  ⚠️  {w}")
            if res["ok"]:
                print("\n  ✅ Skill instalowalny w Claude (frontmatter poprawny).")
            else:
                print("\n  ⛔ Skill NIE wgra się do Claude — napraw błędy powyżej.")
        return 0 if res["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
