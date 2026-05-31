#!/usr/bin/env python3
"""
sop_schema — walidator artefaktów wykonywalnych (SOP / Skill / n8n).

Problem: reguły z artifacts/*/SCHEMA.md żyły dotąd jako proza + jednorazowy check
w sesji. Nic ich nie egzekwowało — następny wygenerowany albo ręcznie poprawiony
artefakt mógł po cichu złamać kontrakt (np. niezgodne io SOP↔skill, albo flow
external-send BEZ bramki approval w SOP). To jest gate: utrwala te checki w
testowanym rdzeniu, tak jak kb_setup.py jest gatem dla configu.

Sprawdza (deterministycznie, te same dane → ten sam wynik):
  • strukturę: slug kebab-case + unikalny, kroki SOPa mają unikalne id
  • binding:   automatable:true ⇒ tool≠null; tool ma znany prefiks (mcp:/skill:/n8n:/script:)
  • spójność:  io SOP↔skill↔n8n zgadza się po nazwach (krok woła zdolność)
  • SAFETY:    zdolność external-send / irreversible ⇒ krok MUSI być w guardrails.irreversible_actions
  • integralność: każde id w irreversible_actions istnieje w steps
  • grounding (jeśli config/ obecny): typy węzłów n8n ∈ config/n8n_nodes.yaml; binding
                mcp:<conn>/<fn> ∈ config/connectors.yaml — łapie zhalucynowane node/funkcje

Komendy:
  python3 scripts/sop_schema.py validate                # raport czytelny (domyślnie artifacts/)
  python3 scripts/sop_schema.py validate --json          # maszynowo, exit!=0 gdy błędy
  python3 scripts/sop_schema.py validate path/do/artifacts

Wymaga PyYAML. Uruchamiać z roota repo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOOL_PREFIXES = ("mcp:", "skill:", "n8n:", "script:")

SIDE_EFFECTS = {"read-only", "writes-internal", "external-send"}
SKILL_AUTONOMY = {"autonomous", "supervised", "human-review-output"}
GATE_AUTONOMY = {"autonomous", "supervised", "human-gated"}
SOP_TRIGGER = {"event", "schedule", "request", "webhook"}
N8N_TRIGGER = {"cron", "webhook", "form", "db-change"}
SOP_STATUS = {"draft", "validated", "implemented"}
N8N_STATUS = {"draft", "deployed", "active"}
SOP_EXECUTOR = {"human", "ai", "auto", "hybrid"}
STEP_EXECUTOR = {"human", "ai", "auto"}


# --------------------------------------------------------------------------- #
# Parsowanie
# --------------------------------------------------------------------------- #
def _parse_frontmatter(path: Path):
    """Zwraca dict frontmattera (YAML między pierwszymi dwoma '---') lub None."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    return yaml.safe_load("\n".join(lines[1:end])) or {}


def _io_names(io, key) -> list[str]:
    """Lista nazw z io.input / io.output (lista dictów {name,...})."""
    return [str(d.get("name")) for d in (io or {}).get(key, []) or [] if isinstance(d, dict)]


def _required_inputs(io) -> set[str]:
    return {str(d.get("name")) for d in (io or {}).get("input", []) or []
            if isinstance(d, dict) and d.get("required")}


# --------------------------------------------------------------------------- #
# Grounded katalogi (config/) — opcjonalne; brak → checki pominięte
# --------------------------------------------------------------------------- #
def _collect_node_types(obj) -> set[str]:
    """Rekurencyjnie zbiera stringi wyglądające jak realny node n8n (n8n-nodes-base.* / @n8n/*)."""
    out: set[str] = set()
    if isinstance(obj, dict):
        for v in obj.values():
            out |= _collect_node_types(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= _collect_node_types(v)
    elif isinstance(obj, str) and (obj.startswith("n8n-nodes-base.") or obj.startswith("@n8n/")):
        out.add(obj)
    return out


def _load_catalogs(config_dir):
    """Zwraca (known_node_types:set, connectors:dict). Brak pliku → pusto (check pominięty)."""
    known_nodes: set[str] = set()
    connectors: dict = {}
    if not config_dir:
        return known_nodes, connectors
    cdir = Path(config_dir)
    nodes_f = cdir / "n8n_nodes.yaml"
    if nodes_f.exists():
        known_nodes = _collect_node_types(yaml.safe_load(nodes_f.read_text(encoding="utf-8")) or {})
    conn_f = cdir / "connectors.yaml"
    if conn_f.exists():
        data = yaml.safe_load(conn_f.read_text(encoding="utf-8")) or {}
        connectors = data.get("connectors") or {}
    return known_nodes, connectors


# --------------------------------------------------------------------------- #
# Discovery + walidacja per-plik
# --------------------------------------------------------------------------- #
def _discover_sops(root: Path, errors, warnings) -> dict:
    out = {}
    for p in sorted(root.glob("sops/**/*.md")):
        if p.name in ("SCHEMA.md", "README.md"):
            continue
        fm = _parse_frontmatter(p)
        rel = p.relative_to(root)
        if fm is None:
            errors.append(f"SOP {rel}: brak frontmattera YAML")
            continue
        slug = str(fm.get("slug", "")).strip()
        if not slug:
            errors.append(f"SOP {rel}: brak pola 'slug'")
            continue
        if not SLUG_RE.match(slug):
            errors.append(f"SOP {rel}: slug '{slug}' nie jest kebab-case")
        if slug in out:
            errors.append(f"SOP slug '{slug}' zduplikowany ({rel} i {out[slug]['_rel']})")
        if p.stem != slug and "examples" not in p.parts:
            warnings.append(f"SOP {rel}: nazwa pliku != slug ('{slug}')")
        fm["_rel"] = str(rel)
        _validate_sop(slug, fm, errors, warnings)
        out[slug] = fm
    return out


def _validate_sop(slug, fm, errors, warnings):
    rel = fm["_rel"]
    if fm.get("executor_overall") not in SOP_EXECUTOR:
        warnings.append(f"SOP {slug}: executor_overall '{fm.get('executor_overall')}' spoza enum")
    if str(fm.get("status", "")) not in SOP_STATUS:
        warnings.append(f"SOP {slug}: status '{fm.get('status')}' spoza enum")
    trig = (fm.get("trigger") or {}).get("type")
    if trig not in SOP_TRIGGER:
        warnings.append(f"SOP {slug}: trigger.type '{trig}' spoza enum")

    steps = fm.get("steps") or []
    if not steps:
        errors.append(f"SOP {slug}: brak kroków (steps)")
        return
    seen = set()
    step_ids = set()
    for s in steps:
        sid = s.get("id")
        step_ids.add(sid)
        if sid in seen:
            errors.append(f"SOP {slug}: zduplikowane id kroku {sid}")
        seen.add(sid)
        tool = s.get("tool")
        if s.get("automatable") is True and not tool:
            errors.append(f"SOP {slug} krok {sid}: automatable:true, ale brak 'tool' (binding)")
        if tool and not str(tool).startswith(TOOL_PREFIXES):
            errors.append(f"SOP {slug} krok {sid}: tool '{tool}' bez znanego prefiksu {TOOL_PREFIXES}")
        if s.get("executor") == "human" and s.get("automatable") is True:
            warnings.append(f"SOP {slug} krok {sid}: executor:human, ale automatable:true (sprzeczność)")
        if s.get("executor") and s.get("executor") not in STEP_EXECUTOR:
            warnings.append(f"SOP {slug} krok {sid}: executor '{s.get('executor')}' spoza enum")

    irr = (fm.get("guardrails") or {}).get("irreversible_actions") or []
    for aid in irr:
        if aid not in step_ids:
            errors.append(f"SOP {slug}: irreversible_actions zawiera id {aid}, którego nie ma w steps")


def _discover_skills(root: Path, errors, warnings) -> dict:
    out = {}
    for p in sorted(root.glob("skills/**/SKILL.md")):
        fm = _parse_frontmatter(p)
        rel = p.relative_to(root)
        if fm is None:
            errors.append(f"Skill {rel}: brak frontmattera YAML")
            continue
        name = str(fm.get("name", "")).strip()
        if not name:
            errors.append(f"Skill {rel}: brak pola 'name'")
            continue
        if not SLUG_RE.match(name):
            errors.append(f"Skill {rel}: name '{name}' nie jest kebab-case")
        if name in out:
            errors.append(f"Skill name '{name}' zduplikowany ({rel} i {out[name]['_rel']})")
        if p.parent.name != name and "examples" not in p.parts:
            warnings.append(f"Skill {rel}: katalog != name ('{name}')")
        fm["_rel"] = str(rel)
        _validate_skill(name, fm, errors, warnings)
        out[name] = fm
    return out


def _validate_skill(name, fm, errors, warnings):
    io = fm.get("io") or {}
    if not io.get("input") or not io.get("output"):
        errors.append(f"Skill {name}: brak io.input lub io.output (kontrakt I/O)")
    if fm.get("side_effects") not in SIDE_EFFECTS:
        warnings.append(f"Skill {name}: side_effects '{fm.get('side_effects')}' spoza enum")
    if fm.get("autonomy") not in SKILL_AUTONOMY:
        warnings.append(f"Skill {name}: autonomy '{fm.get('autonomy')}' spoza enum")
    if len(fm.get("triggers") or []) < 5:
        warnings.append(f"Skill {name}: <5 trigger phrases (zalecane ≥5)")


def _discover_n8n(root: Path, errors, warnings, known_nodes=None) -> dict:
    out = {}
    for p in sorted(root.glob("n8n/**/*.json")):
        rel = p.relative_to(root)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"n8n {rel}: niepoprawny JSON ({e})")
            continue
        meta = data.get("meta") or {}
        slug = str(meta.get("slug", "")).strip()
        if not slug:
            errors.append(f"n8n {rel}: brak meta.slug")
            continue
        if not SLUG_RE.match(slug):
            errors.append(f"n8n {rel}: slug '{slug}' nie jest kebab-case")
        if slug in out:
            errors.append(f"n8n slug '{slug}' zduplikowany ({rel} i {out[slug]['_rel']})")
        if p.stem != slug and "examples" not in p.parts:
            warnings.append(f"n8n {rel}: nazwa pliku != slug ('{slug}')")
        meta["_rel"] = str(rel)
        _validate_n8n(slug, meta, errors, warnings)
        _check_n8n_nodes(slug, data.get("nodes"), known_nodes, warnings)
        out[slug] = meta
    return out


def _check_n8n_nodes(slug, nodes, known_nodes, warnings):
    """Grounding: typ węzła ≠ TBD musi być realnym node z config/n8n_nodes.yaml.
    Pomijane, gdy katalog niewczytany (known_nodes puste)."""
    if not known_nodes:
        return
    for n in nodes or []:
        t = n.get("type")
        if not t or t == "TBD":
            continue
        if t not in known_nodes:
            warnings.append(f"n8n {slug} węzeł '{n.get('name')}': type '{t}' spoza "
                            f"config/n8n_nodes.yaml (zweryfikuj realność node lub dopisz do katalogu)")


def _validate_n8n(slug, meta, errors, warnings):
    cref = meta.get("capability_ref")
    if cref and cref != f"n8n:{slug}":
        errors.append(f"n8n {slug}: capability_ref '{cref}' != 'n8n:{slug}'")
    io = meta.get("io") or {}
    if not io.get("input") and not io.get("output"):
        errors.append(f"n8n {slug}: brak meta.io (kontrakt I/O)")
    if meta.get("side_effects") not in SIDE_EFFECTS:
        warnings.append(f"n8n {slug}: side_effects '{meta.get('side_effects')}' spoza enum")
    if str(meta.get("status", "")) not in N8N_STATUS:
        warnings.append(f"n8n {slug}: status '{meta.get('status')}' spoza enum")
    irr = (meta.get("guardrails") or {}).get("irreversible")
    if irr is not None and not isinstance(irr, bool):
        warnings.append(f"n8n {slug}: guardrails.irreversible nie jest bool")
    trig = (meta.get("trigger") or {}).get("type")
    if trig and trig not in N8N_TRIGGER:
        warnings.append(f"n8n {slug}: trigger.type '{trig}' spoza enum")


# --------------------------------------------------------------------------- #
# Cross-artefaktowe checki (sedno — binding + safety)
# --------------------------------------------------------------------------- #
def _cross_checks(sops, skills, n8n, errors, warnings):
    for slug, sop in sops.items():
        irr = set((sop.get("guardrails") or {}).get("irreversible_actions") or [])
        for s in sop.get("steps") or []:
            tool = s.get("tool")
            if not tool or ":" not in str(tool):
                continue
            kind, ref = str(tool).split(":", 1)
            step_in = set(s.get("inputs") or [])
            step_out = set(s.get("outputs") or [])
            sid = s.get("id")

            if kind == "skill":
                dep = skills.get(ref)
                if dep is None:
                    warnings.append(f"SOP {slug} krok {sid}: woła skill:{ref}, którego nie ma w artifacts/")
                    continue
                _check_binding(slug, sid, f"skill:{ref}", step_in, step_out, dep.get("io"), errors)
                if dep.get("side_effects") == "external-send" and sid not in irr:
                    errors.append(f"SAFETY: SOP {slug} krok {sid} woła skill:{ref} (external-send), "
                                  f"ale kroku NIE ma w guardrails.irreversible_actions")
                if dep.get("parent_sop") not in (slug, None):
                    warnings.append(f"SOP {slug} krok {sid}: skill:{ref}.parent_sop='{dep.get('parent_sop')}' != '{slug}'")

            elif kind == "n8n":
                dep = n8n.get(ref)
                if dep is None:
                    warnings.append(f"SOP {slug} krok {sid}: woła n8n:{ref}, którego nie ma w artifacts/")
                    continue
                _check_binding(slug, sid, f"n8n:{ref}", step_in, step_out, dep.get("io"), errors)
                ext = dep.get("side_effects") == "external-send"
                irrev = (dep.get("guardrails") or {}).get("irreversible") is True
                if (ext or irrev) and sid not in irr:
                    errors.append(f"SAFETY: SOP {slug} krok {sid} woła n8n:{ref} "
                                  f"({'external-send' if ext else ''}{'/irreversible' if irrev else ''}), "
                                  f"ale kroku NIE ma w guardrails.irreversible_actions")
                if dep.get("parent_sop") not in (slug, None):
                    warnings.append(f"SOP {slug} krok {sid}: n8n:{ref}.parent_sop='{dep.get('parent_sop')}' != '{slug}'")


def _check_binding(slug, sid, ref, step_in, step_out, dep_io, errors):
    """Wejścia wymagane przez zdolność ⊆ wejścia kroku; wyjścia kroku == wyjścia zdolności."""
    req_in = _required_inputs(dep_io)
    dep_out = set(_io_names(dep_io, "output"))
    missing = req_in - step_in
    if missing:
        errors.append(f"SOP {slug} krok {sid}: {ref} wymaga wejść {sorted(missing)}, "
                      f"których krok nie przekazuje (krok ma {sorted(step_in)})")
    if dep_out and step_out != dep_out:
        errors.append(f"SOP {slug} krok {sid}: wyjścia kroku {sorted(step_out)} != "
                      f"wyjścia {ref} {sorted(dep_out)}")


# --------------------------------------------------------------------------- #
# Grounded checki — binding mcp:<conn>/<fn> ∈ config/connectors.yaml
# --------------------------------------------------------------------------- #
def _collect_mcp(val, where, refs):
    if isinstance(val, str) and val.startswith("mcp:"):
        refs.append((where, val))


def _catalog_checks(sops, skills, connectors, warnings):
    """Każde mcp:<conn>/<fn> w SOP/Skill musi wskazywać realny konektor i funkcję z katalogu.
    Pomijane, gdy connectors puste (katalog niewczytany)."""
    if not connectors:
        return
    refs: list = []
    for slug, sop in sops.items():
        for s in sop.get("steps") or []:
            _collect_mcp(s.get("tool"), f"SOP {slug} krok {s.get('id')}", refs)
        for i in sop.get("inputs") or []:
            _collect_mcp(i.get("source"), f"SOP {slug} input {i.get('name')}", refs)
        for o in sop.get("outputs") or []:
            _collect_mcp(o.get("destination"), f"SOP {slug} output {o.get('name')}", refs)
    for name, sk in skills.items():
        caps = sk.get("capabilities") or {}
        for c in (caps.get("allow") or []) + (caps.get("deny") or []):
            _collect_mcp(c, f"Skill {name} capability", refs)

    for where, ref in refs:
        conn, _, fn = ref[len("mcp:"):].partition("/")
        if conn not in connectors:
            warnings.append(f"{where}: konektor '{conn}' w '{ref}' spoza config/connectors.yaml")
            continue
        if fn and fn != "*" and fn not in (connectors[conn].get("functions") or []):
            warnings.append(f"{where}: funkcja '{fn}' w '{ref}' spoza connectors.yaml[{conn}] "
                            f"(zweryfikuj nazwę lub dopisz do katalogu)")


# --------------------------------------------------------------------------- #
# API + CLI
# --------------------------------------------------------------------------- #
def validate(root="artifacts", config_dir=None) -> dict:
    """Zwraca {ok, errors[], warnings[], summary}.

    config_dir: katalog z grounded katalogami (n8n_nodes.yaml, connectors.yaml). Gdy None,
    próbuje {root}/../config. Brak → checki groundingu pominięte (nie błąd)."""
    rootp = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    if not rootp.exists():
        return {"ok": False, "errors": [f"Brak katalogu {root}"], "warnings": []}

    if config_dir is None:
        guess = rootp.parent / "config"
        config_dir = str(guess) if guess.exists() else None
    known_nodes, connectors = _load_catalogs(config_dir)

    sops = _discover_sops(rootp, errors, warnings)
    skills = _discover_skills(rootp, errors, warnings)
    n8n = _discover_n8n(rootp, errors, warnings, known_nodes)
    _cross_checks(sops, skills, n8n, errors, warnings)
    _catalog_checks(sops, skills, connectors, warnings)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {"sops": len(sops), "skills": len(skills), "n8n": len(n8n),
                    "errors": len(errors), "warnings": len(warnings)},
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="sop_schema — walidator artefaktów wykonywalnych")
    sub = p.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("validate")
    pv.add_argument("path", nargs="?", default="artifacts")
    pv.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        res = validate(args.path)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            s = res.get("summary", {})
            print("artifacts/ — walidacja artefaktów wykonywalnych\n")
            if s:
                print(f"  SOP: {s.get('sops')} · Skill: {s.get('skills')} · n8n: {s.get('n8n')}\n")
            for e in res["errors"]:
                print(f"  ❌ BŁĄD: {e}")
            for w in res["warnings"]:
                print(f"  ⚠️  {w}")
            if res["ok"]:
                print("\n  ✅ Artefakty spójne — kontrakty bezpieczne do oddania agentowi.")
            else:
                print(f"\n  ⛔ {len(res['errors'])} naruszeń — artefakty NIE są gotowe dla agenta.")
        return 0 if res["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
