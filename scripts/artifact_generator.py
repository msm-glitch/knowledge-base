#!/usr/bin/env python3
"""
artifact_generator — Krok 4.5 knowledge-base.

Generuje artefakty (SOP / Skill / n8n) z wpisu KB (JSON) zgodnie z SCHEMA.md.
Wynik (JSON na stdout) zawiera:
  - notion_fields  : pola właściwości strony Notion (do notion-create-pages)
  - body_content   : treść bloku code (yaml/json) do wklejenia jako body strony
  - body_language  : "yaml" | "json"
  - artifact_type  : "sop" | "skill" | "n8n"
  - slug           : kebab-case slug
  - errors         : lista błędów blokujących (needs_slug, unknown-type, …)
  - warnings       : lista ostrzeżeń nieblokujących (TBD fields, unknown systems, …)

Bez zależności zewnętrznych w logice rdzenia (stdlib). YAML ładowany tylko w CLI
(ten sam wzorzec co kb_lib.py).

Użycie CLI:
  python3 scripts/artifact_generator.py generate \\
      --entry entry.json \\
      [--connectors config/connectors.yaml] \\
      [--n8n-nodes  config/n8n_nodes.yaml] \\
      [--date 2026-06-10]

  python3 scripts/artifact_generator.py generate \\
      --entries entries.json   # batch: lista wpisów KB

Format wejścia (entry.json) — pola wymagane i opcjonalne:
  title           str   "[NEW] 2026-05-10 · Autor · slug — opis"
  type            str   "SOP" | "Skill Backlog" | "n8n Automation"
  summary         str   do 500 znaków (auto-truncated)
  owner           str   imię lub email
  kb_entry_url    str   URL strony KB w Notion
  date            str   ISO date "YYYY-MM-DD"
  # SOP
  trigger         str   opis triggera
  steps           list|str   lista kroków lub tekst (newline-separated)
  frequency       str   "weekly" | "monthly" | ...
  parent_sop      str|null   slug SOPa nadrzędnego
  # Skill
  description     str   rozwinięcie summary
  trigger_phrases list  min 5 fraz triggerujących skill
  # n8n
  trigger         str   opis triggera (cron/webhook/form/…)
  data_sources    list|str   źródła danych (comma-separated lub list)
  destinations    list|str   miejsca zapisu/wysyłki
  transformations str   opis transformacji
  error_handling  str   opis obsługi błędów
  priority        str   "High" | "Medium" | "Low"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date as _date
from typing import Any

# --- text utils ---------------------------------------------------------------

_PREFIX_RE = re.compile(r"^\s*\[(NEW|FIX|BUG)\]\s*", re.I)
_DATE_SEG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text)
                   if not unicodedata.combining(c))


def _norm(text: str) -> str:
    """Lowercase + bez akcentów (ł→l jawnie, NFKD go nie rozkłada)."""
    return _strip_accents((text or "").lower().replace("ł", "l"))


def slugify(title: str) -> str:
    """'[NEW] 2026-05-10 · Michał · off-x — opis' → 'off-x'"""
    t = _PREFIX_RE.sub("", title or "")
    t = re.split(r"\s[—\-]\s", t, maxsplit=1)[0]
    parts = [p.strip() for p in t.split("·") if p.strip()]
    parts = [p for p in parts if not _DATE_SEG_RE.match(p)]
    cand = parts[-1] if parts else t
    slug = re.sub(r"[^0-9a-ząćęłńóśźż\s\-]", "", _norm(cand))
    slug = re.sub(r"\s+", "-", slug.strip()).strip("-")
    return slug or "tbd"


def _display_title(title: str) -> str:
    """Usuwa prefix [NEW/FIX/BUG]."""
    return _PREFIX_RE.sub("", title or "").strip()


def _trunc(text: str | None, n: int = 500) -> str:
    t = (text or "").strip()
    return t[:n] + "…" if len(t) > n else t


def _steps_to_list(raw: Any) -> list[str]:
    """Normalizuje steps (list lub str) do listy niepustych stringów."""
    if isinstance(raw, list):
        result = [str(s).strip() for s in raw if str(s).strip()]
    elif isinstance(raw, str) and raw.strip():
        # próbuj newline, potem średnik
        parts = [s.strip() for s in raw.splitlines() if s.strip()]
        if len(parts) <= 1:
            parts = [s.strip() for s in raw.split(";") if s.strip()]
        result = parts
    else:
        result = []
    return result or ["[TBD: opisz kroki procesu]"]


# --- config loading (tylko CLI; testy przekazują dicts) -----------------------

def _load_yaml(path: str) -> dict:
    import yaml  # tylko CLI; testy nie wymagają yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_connectors(path: str = "config/connectors.yaml") -> dict:
    return _load_yaml(path).get("connectors", {})


def load_n8n_nodes(path: str = "config/n8n_nodes.yaml") -> dict:
    data = _load_yaml(path)
    return {
        "systems":  data.get("systems", {}),
        "triggers": data.get("triggers", {}),
        "logic":    data.get("logic", {}),
        "error":    data.get("error", {}),
    }


# --- resolucja systemów / konektorów ------------------------------------------

def resolve_n8n_system(text: str, systems: dict) -> dict | None:
    """Dopasowanie nazwy systemu (substring alias) → info węzła n8n."""
    t = (text or "").lower()
    for sys_key, info in systems.items():
        for alias in info.get("aliases", []):
            if alias.lower() in t or (len(t) >= 3 and t in alias.lower()):
                return {
                    "key":        sys_key,
                    "node":       info.get("node", "TBD"),
                    "credential": info.get("credential", "TBD"),
                    "connector":  info.get("connector"),
                }
    return None


def resolve_trigger_node(trigger_text: str, triggers: dict) -> str:
    """Mapuje opis triggera na typ węzła n8n."""
    t = _norm(trigger_text)
    if any(k in t for k in ("cron", "harmonogram", "weekly", "monthly", "daily",
                             "quarterly", "co tydzien", "co miesiac", "co ")):
        return triggers.get("schedule", {}).get("node", "n8n-nodes-base.scheduleTrigger")
    if any(k in t for k in ("webhook", "http request", "api call")):
        return triggers.get("webhook", {}).get("node", "n8n-nodes-base.webhook")
    if any(k in t for k in ("form", "formularz", "submit")):
        return triggers.get("form", {}).get("node", "n8n-nodes-base.formTrigger")
    if any(k in t for k in ("recznie", "manual", "test")):
        return triggers.get("manual", {}).get("node", "n8n-nodes-base.manualTrigger")
    if any(k in t for k in ("sop", "sub-resource", "called by", "wołany")):
        return triggers.get("called_by_sop", {}).get("node", "n8n-nodes-base.executeWorkflowTrigger")
    return triggers.get("schedule", {}).get("node", "n8n-nodes-base.scheduleTrigger")


def _detect_trigger_type_sop(trigger_text: str) -> str:
    """SOP trigger type: event | schedule | request | webhook."""
    t = _norm(trigger_text)
    if any(k in t for k in ("cron", "harmonogram", "weekly", "monthly", "daily",
                             "quarterly", "co tydzien", "co ")):
        return "schedule"
    if any(k in t for k in ("webhook", "http", "api")):
        return "webhook"
    if any(k in t for k in ("na zadanie", "request", "wniosek", "prosba")):
        return "request"
    return "event"


def _detect_trigger_type_n8n(trigger_text: str) -> str:
    """n8n trigger meta.trigger.type: cron | webhook | form | db-change."""
    t = _norm(trigger_text)
    if any(k in t for k in ("cron", "harmonogram", "weekly", "monthly", "daily",
                             "quarterly", "co tydzien", "co ")):
        return "cron"
    if any(k in t for k in ("webhook", "http")):
        return "webhook"
    if any(k in t for k in ("form", "formularz")):
        return "form"
    if any(k in t for k in ("db", "database", "baza", "zmiana w bazie")):
        return "db-change"
    return "cron"


def _resolve_connector_binding(action: str, systems: dict, connectors: dict) -> str | None:
    """Próbuje dopasować akcję do mcp:{connector}/{function}.
    Zwraca binding lub None jeśli brak pewnego dopasowania.
    """
    # Znajdź system przez alias
    matched_conn_key = None
    for _sys_key, info in systems.items():
        conn_key = info.get("connector")
        if not conn_key:
            continue
        for alias in info.get("aliases", []):
            if alias.lower() in action.lower():
                matched_conn_key = conn_key
                break
        if matched_conn_key:
            break

    if not matched_conn_key or matched_conn_key not in connectors:
        return None

    functions: list[str] = connectors[matched_conn_key].get("functions", [])
    if not functions:
        return None

    # Słowa kluczowe akcji → podpowiedź nazwy funkcji
    a = _norm(action)
    hints: list[tuple[str, list[str]]] = [
        ("pobierz",     ["get", "list", "search", "read", "query", "fetch"]),
        ("lista",       ["list", "get"]),
        ("szukaj",      ["search"]),
        ("zapisz",      ["create", "update", "write"]),
        ("stworz",      ["create"]),
        ("zaktualizuj", ["update", "change"]),
        ("wyslij",      ["send", "create_draft"]),
        ("wysylaj",     ["send", "create_draft"]),
        ("notyfikuj",   ["create_notification", "send_message", "slack_send"]),
        ("powiadom",    ["create_notification", "send_message", "slack_send"]),
        ("usun",        ["delete", "remove"]),
        ("eksportuj",   ["export", "download"]),
        ("importuj",    ["import", "upload"]),
    ]
    for kw, fn_hints in hints:
        if kw in a:
            for fn in functions:
                if any(h in fn.lower() for h in fn_hints):
                    return f"mcp:{matched_conn_key}/{fn}"
            break

    # Fallback: pierwszy konektor
    return f"mcp:{matched_conn_key}/{functions[0]}"


# --- SOP generation -----------------------------------------------------------

def _build_sop_step(idx: int, action: str, systems: dict, connectors: dict,
                    irreversible_ids: list[str]) -> dict:
    """Buduje jeden krok SOP z tekstu akcji."""
    human_kws = ["ocen", "zdecyduj", "przejrzyj", "sprawdz", "zweryfikuj",
                 "zatwierdz", "approve", "review", "evaluate", "choose", "wybierz",
                 "nadzoruj", "zadecyduj"]
    needs_human = any(_norm(kw) in _norm(action) for kw in human_kws)

    binding: str | None = None
    if not needs_human:
        binding = _resolve_connector_binding(action, systems, connectors)

    automatable = bool(binding)
    executor = "human" if needs_human else ("auto" if automatable else "human")

    # Sprawdź side_effects bindingu → irreversible
    if binding:
        conn_key = binding.split("/")[0].removeprefix("mcp:")
        if connectors.get(conn_key, {}).get("side_effects") == "external-send":
            irreversible_ids.append(str(idx))

    step: dict = {
        "id":             idx,
        "action":         action,
        "automatable":    automatable,
        "executor":       executor,
        "tool":           binding if binding else "null",
        "inputs":         "[TBD]",
        "outputs":        "[TBD]",
        "preconditions":  "null",
        "postconditions": "null",
        "on_error":       "retry" if automatable else "escalate",
    }
    if needs_human:
        step["requires_human"] = "[TBD: opisz powód wymagania człowieka]"
    return step


def _render_step_yaml(s: dict) -> str:
    lines = [f"  - id: {s['id']}"]
    lines.append(f"    action: \"{s['action']}\"")
    lines.append(f"    automatable: {str(s['automatable']).lower()}")
    lines.append(f"    executor: {s['executor']}")
    lines.append(f"    tool: {s['tool']}")
    lines.append(f"    inputs: {s['inputs']}")
    lines.append(f"    outputs: {s['outputs']}")
    lines.append(f"    preconditions: {s['preconditions']}")
    lines.append(f"    postconditions: {s['postconditions']}")
    lines.append(f"    on_error: {s['on_error']}")
    if "requires_human" in s:
        lines.append(f"    requires_human: \"{s['requires_human']}\"")
    return "\n".join(lines)


def generate_sop(entry: dict, systems: dict, connectors: dict, today: str) -> dict:
    """Generuje artefakt SOP z wpisu KB."""
    errors: list[str] = []
    warnings: list[str] = []

    slug = slugify(entry.get("title", ""))
    if slug == "tbd":
        errors.append("needs_slug: nie można wyciągnąć sluga z title")

    display = _display_title(entry.get("title", slug))
    owner = entry.get("owner") or "[TBD]"
    trigger_text = entry.get("trigger") or "[TBD: opisz trigger]"
    summary = _trunc(entry.get("summary"), 500)
    frequency = entry.get("frequency") or "[TBD]"
    parent_sop = entry.get("parent_sop") or "null"
    kb_url = entry.get("kb_entry_url") or ""

    trigger_type = _detect_trigger_type_sop(trigger_text)
    step_texts = _steps_to_list(entry.get("steps"))

    irreversible_ids: list[str] = []
    built_steps = [
        _build_sop_step(i + 1, a, systems, connectors, irreversible_ids)
        for i, a in enumerate(step_texts)
    ]

    auto_steps = [s for s in built_steps if s["automatable"]]
    auto_text = "; ".join(f"{s['id']}. {s['action']}" for s in auto_steps)
    if not auto_text:
        auto_text = "[brak kroków automatyzowalnych]"
        warnings.append("no-automatable-steps: wszystkie kroki wymagają człowieka")

    # executor_overall heurystyka
    if all(s["executor"] == "auto" for s in built_steps):
        executor_overall = "auto"
    elif all(s["executor"] == "human" for s in built_steps):
        executor_overall = "human"
    else:
        executor_overall = "hybrid"

    irrev_block = "[" + ", ".join(irreversible_ids) + "]" if irreversible_ids else "[]"
    steps_block = "\n".join(_render_step_yaml(s) for s in built_steps)

    frontmatter = (
        f"---\n"
        f"slug: {slug}\n"
        f"version: 1\n"
        f"status: draft\n"
        f"owner: {owner}\n"
        f'source_url: "{kb_url}"\n'
        f"parent_sop: {parent_sop}\n"
        f"trigger:\n"
        f"  type: {trigger_type}\n"
        f'  spec: "{trigger_text}"\n'
        f'  description: "{trigger_text}"\n'
        f"executor_overall: {executor_overall}\n"
        f"frequency: {frequency}\n"
        f"inputs:\n"
        f'  - name: "[TBD]"\n'
        f'    type: "[TBD]"\n'
        f'    source: "[TBD]"\n'
        f"    required: true\n"
        f"outputs:\n"
        f'  - name: "[TBD]"\n'
        f'    type: "[TBD]"\n'
        f'    destination: "[TBD]"\n'
        f"steps:\n"
        f"{steps_block}\n"
        f"guardrails:\n"
        f"  autonomy_level: supervised\n"
        f"  irreversible_actions: {irrev_block}\n"
        f'  pii_handling: "redact via script:scripts/compliance.py"\n'
        f"  escalation: \"{owner}\"\n"
        f"  anti_ai_clause: false\n"
        f"acceptance_criteria:\n"
        f'  - "[TBD: opisz kryterium sukcesu]"\n'
        f"metrics:\n"
        f'  log_to: "state/runs.jsonl"\n'
        f"  fields: [slug, started_at, completed_at, outcome]\n"
        f"---"
    )

    steps_md = "\n".join(
        f"{s['id']}. {s['action']} — {s['executor']} / {s['tool']} / "
        f"automatable={str(s['automatable']).lower()}"
        for s in built_steps
    )

    body = (
        f"{frontmatter}\n\n"
        f"# {display}\n\n"
        f"> Auto-gen {today} · Owner: {owner} · Status: Wersja robocza\n\n"
        f"## Trigger\n{trigger_text}\n\n"
        f"## Steps\n{steps_md}\n\n"
        f"## Decisions\n[TBD: opisz decyzje i kryteria]\n\n"
        f"## Definition of Done\n- [ ] {summary or '[TBD: opisz kryteria ukończenia]'}\n\n"
        f"<!-- Auto-generated {today}. Schema: artifacts/sops/SCHEMA.md -->"
    )

    notion_fields = {
        "Nazwa procesu": display,
        "Trigger procesu": trigger_text,
        "Opis procesu": summary,
        "Punkty automatyzacji": auto_text,
        "Select": "Wersja robocza",
        "Wersja": 1,
        "Link do całego procesu": kb_url,
        "Owner": owner,
    }

    return {
        "artifact_type": "sop",
        "slug": slug,
        "notion_fields": notion_fields,
        "body_content": body,
        "body_language": "yaml",
        "errors": errors,
        "warnings": warnings,
    }


# --- Skill generation ---------------------------------------------------------

def generate_skill(entry: dict, today: str) -> dict:
    """Generuje artefakt Skill z wpisu KB."""
    errors: list[str] = []
    warnings: list[str] = []

    slug = slugify(entry.get("title", ""))
    if slug == "tbd":
        errors.append("needs_slug: nie można wyciągnąć sluga z title")

    owner = entry.get("owner") or "[TBD]"
    summary = _trunc(entry.get("summary"), 500)
    description = entry.get("description") or summary or "[TBD: opisz skill]"
    parent_sop = entry.get("parent_sop") or "null"
    kb_url = entry.get("kb_entry_url") or ""
    trigger_text = entry.get("trigger") or "[TBD]"

    phrases = list(entry.get("trigger_phrases") or [])
    while len(phrases) < 5:
        phrases.append(f'[TBD: trigger phrase {len(phrases) + 1}]')
    if len(phrases) < 5:
        warnings.append("triggers: mniej niż 5 trigger phrases — uzupełnij")

    triggers_block = "\n".join(f'  - "{p}"' for p in phrases)

    frontmatter = (
        f"---\n"
        f"name: {slug}\n"
        f"version: 1\n"
        f"status: draft\n"
        f'description: "{description}"\n'
        f"parent_sop: {parent_sop}\n"
        f'source_url: "{kb_url}"\n'
        f"triggers:\n"
        f"{triggers_block}\n"
        f"io:\n"
        f"  input:\n"
        f'    - name: "[TBD]"\n'
        f'      type: "[TBD]"\n'
        f"      required: true\n"
        f"  output:\n"
        f'    - name: "[TBD]"\n'
        f'      type: "[TBD]"\n'
        f"capabilities:\n"
        f"  allow:\n"
        f'    - "[TBD: wpisz dozwolone narzędzia]"\n'
        f"  deny:\n"
        f'    - "gmail/*"\n'
        f'    - "slack/slack_send_message"\n'
        f"side_effects: read-only\n"
        f"autonomy: human-review-output\n"
        f"guardrails:\n"
        f'  pii_handling: "redact via script:scripts/compliance.py"\n'
        f"  requires_human_review: true\n"
        f"evals:\n"
        f"  - id: 1\n"
        f'    input_ref: "examples#1"\n'
        f'    assert: "[TBD: predykat sprawdzający output]"\n'
        f"---"
    )

    body = (
        f"{frontmatter}\n\n"
        f"# {slug}\n\n"
        f"## Kontekst\n{description}\n\n"
        f"## Input format\n[TBD: opisz format wejścia]\n\n"
        f"## Output format\n[TBD: opisz format wyjścia]\n\n"
        f"## Examples\n[TBD: 2-3 pary input/output]\n\n"
        f"## Style guide\n[TBD: persona, ton, styl OFF]\n\n"
        f"## Edge cases\n[TBD: brzegowe przypadki i co robić]\n\n"
        f"## Related skills\n[TBD: powiązane skille]\n\n"
        f"<!-- Auto-generated {today}. Schema: artifacts/skills/SCHEMA.md -->"
    )

    priority = entry.get("priority") or "Medium"
    priority_map = {"High": "P0", "Medium": "P1", "Low": "P2"}

    notion_fields = {
        "Name": slug,
        "Priority": priority_map.get(priority, "P1"),
        "Status": "Idea",
        "Type": "Skill",
        "Notes": summary,
        "Owner": owner,
    }

    return {
        "artifact_type": "skill",
        "slug": slug,
        "notion_fields": notion_fields,
        "body_content": body,
        "body_language": "yaml",
        "errors": errors,
        "warnings": warnings,
    }


# --- n8n generation -----------------------------------------------------------

def generate_n8n(entry: dict, systems: dict, connectors: dict,
                 triggers_catalog: dict, logic_catalog: dict,
                 error_catalog: dict, today: str) -> dict:
    """Generuje artefakt n8n automation z wpisu KB."""
    errors: list[str] = []
    warnings: list[str] = []

    slug = slugify(entry.get("title", ""))
    if slug == "tbd":
        errors.append("needs_slug: nie można wyciągnąć sluga z title")

    owner = entry.get("owner") or "[TBD]"
    summary = _trunc(entry.get("summary"), 500)
    trigger_text = entry.get("trigger") or "[TBD]"
    parent_sop = entry.get("parent_sop")
    kb_url = entry.get("kb_entry_url") or ""

    trigger_node_type = resolve_trigger_node(trigger_text, triggers_catalog)
    trigger_meta_type = _detect_trigger_type_n8n(trigger_text)

    def _to_list(raw: Any) -> list[str]:
        if isinstance(raw, list):
            return [str(s).strip() for s in raw if str(s).strip()]
        if isinstance(raw, str) and raw.strip():
            return [s.strip() for s in raw.split(",") if s.strip()]
        return []

    data_sources = _to_list(entry.get("data_sources"))
    destinations = _to_list(entry.get("destinations"))

    credentials_required: list[str] = []
    manual_steps: list[str] = [
        "Uzupełnij parametry węzłów w n8n cloud",
        "Skonfiguruj credentials",
    ]
    nodes: list[dict] = []

    nodes.append({
        "name":       "Trigger",
        "type":       trigger_node_type,
        "notes":      trigger_text,
        "parameters": {},
    })

    for src in data_sources:
        info = resolve_n8n_system(src, systems)
        if info:
            node_type = info["node"]
            cred = info["credential"]
            if cred not in credentials_required:
                credentials_required.append(cred)
            note = cred
        else:
            node_type = "TBD"
            note = "[TBD: nieznany system — wpisz typ węzła ręcznie]"
            manual_steps.append(f"Wskaż typ węzła n8n dla źródła: {src}")
            warnings.append(f"unknown-system: '{src}' → type: TBD")
        nodes.append({
            "name":       f"Source: {src}",
            "type":       node_type,
            "notes":      note,
            "parameters": {},
        })

    transformations = (entry.get("transformations") or "").strip()
    if transformations:
        transform_node = logic_catalog.get("transform", {}).get("node", "n8n-nodes-base.code")
        nodes.append({
            "name":       "Transform",
            "type":       transform_node,
            "notes":      _trunc(transformations, 200),
            "parameters": {},
        })

    side_effects = "read-only"
    for dst in destinations:
        info = resolve_n8n_system(dst, systems)
        if info:
            node_type = info["node"]
            cred = info["credential"]
            if cred not in credentials_required:
                credentials_required.append(cred)
            note = cred
            conn_key = info.get("connector")
            if conn_key and connectors.get(conn_key, {}).get("side_effects") == "external-send":
                side_effects = "external-send"
            elif side_effects == "read-only":
                side_effects = "writes-internal"
        else:
            node_type = "TBD"
            note = "[TBD: nieznany system — wpisz typ węzła ręcznie]"
            manual_steps.append(f"Wskaż typ węzła n8n dla destination: {dst}")
            warnings.append(f"unknown-system: '{dst}' → type: TBD")
        nodes.append({
            "name":       f"Destination: {dst}",
            "type":       node_type,
            "notes":      note,
            "parameters": {},
        })

    error_text = (entry.get("error_handling") or "Alert na #ai-feedback do ownera").strip()
    error_node = error_catalog.get("alert", {}).get("node", "n8n-nodes-base.slack")
    nodes.append({
        "name":       "Error handler",
        "type":       error_node,
        "notes":      error_text,
        "parameters": {},
    })
    if "slack_api" not in credentials_required:
        credentials_required.append("slack_api")

    if not data_sources and not destinations:
        warnings.append("no-systems: brak data_sources i destinations — węzły TBD")

    meta = {
        "slug":                  slug,
        "version":               1,
        "status":                "draft",
        "capability_ref":        f"n8n:{slug}",
        "io": {
            "input":  [{"name": "[TBD]", "type": "[TBD]", "required": True}],
            "output": [{"name": "[TBD]", "type": "[TBD]"}],
        },
        "trigger": {
            "type": trigger_meta_type,
            "spec": trigger_text,
        },
        "side_effects":          side_effects,
        "credentials_required":  credentials_required,
        "guardrails": {
            "autonomy":    "supervised",
            "irreversible": side_effects == "external-send",
        },
        "verification": {
            "test_plan":   "[TBD: opisz test plan]",
            "healthcheck": "[TBD: sygnał że flow żyje]",
        },
        "manual_steps_remaining": "; ".join(manual_steps),
        "parent_sop":             parent_sop,
        "notion_entry":           _display_title(entry.get("title") or slug),
        "source_url":             kb_url,
    }

    artifact = {"name": slug, "nodes": nodes, "connections": {}, "meta": meta}

    priority = entry.get("priority") or "Medium"
    priority_map = {"High": "P0", "Medium": "P1", "Low": "P2"}

    notion_fields = {
        "Name": slug,
        "Priority": priority_map.get(priority, "P1"),
        "Status": "Idea",
        "Type": "Automation",
        "Notes": summary,
        "Owner": owner,
    }

    return {
        "artifact_type": "n8n",
        "slug": slug,
        "notion_fields": notion_fields,
        "body_content": json.dumps(artifact, ensure_ascii=False, indent=2),
        "body_language": "json",
        "errors": errors,
        "warnings": warnings,
    }


# --- dispatch -----------------------------------------------------------------

def generate(entry: dict, connectors: dict, n8n_nodes: dict, today: str) -> dict:
    """Dispatch na właściwy generator wg entry['type']."""
    entry_type = (entry.get("type") or "").strip()
    systems = n8n_nodes.get("systems", {})

    if entry_type == "SOP":
        return generate_sop(entry, systems, connectors, today)
    if entry_type == "Skill Backlog":
        return generate_skill(entry, today)
    if entry_type == "n8n Automation":
        return generate_n8n(
            entry, systems, connectors,
            n8n_nodes.get("triggers", {}),
            n8n_nodes.get("logic", {}),
            n8n_nodes.get("error", {}),
            today,
        )
    return {
        "artifact_type": "unknown",
        "slug": slugify(entry.get("title", "")),
        "notion_fields": {},
        "body_content": "",
        "body_language": "yaml",
        "errors": [
            f"unknown-type: '{entry_type}' — oczekiwano: SOP | Skill Backlog | n8n Automation"
        ],
        "warnings": [],
    }


def generate_batch(entries: list[dict], connectors: dict, n8n_nodes: dict,
                   today: str) -> list[dict]:
    return [generate(e, connectors, n8n_nodes, today) for e in entries]


# --- CLI ----------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="artifact_generator — Krok 4.5 knowledge-base")
    sub = p.add_subparsers(dest="cmd", required=True)

    pg = sub.add_parser("generate", help="generuj artefakt z wpisu KB")
    pg.add_argument("--entry",      help="ścieżka do JSON (jeden wpis)")
    pg.add_argument("--entries",    help="ścieżka do JSON (lista wpisów, batch)")
    pg.add_argument("--connectors", default="config/connectors.yaml",
                    help="ścieżka do connectors.yaml")
    pg.add_argument("--n8n-nodes",  default="config/n8n_nodes.yaml",
                    help="ścieżka do n8n_nodes.yaml")
    pg.add_argument("--date",       default=str(_date.today()),
                    help="data generacji ISO YYYY-MM-DD")

    args = p.parse_args(argv)

    if args.cmd != "generate":
        return 1

    connectors: dict = {}
    n8n_nodes: dict = {"systems": {}, "triggers": {}, "logic": {}, "error": {}}

    try:
        connectors = load_connectors(args.connectors)
    except Exception as exc:
        print(json.dumps({"error": f"connectors load failed: {exc}"}), file=sys.stderr)

    try:
        n8n_nodes = load_n8n_nodes(getattr(args, "n8n_nodes", "config/n8n_nodes.yaml"))
    except Exception as exc:
        print(json.dumps({"error": f"n8n_nodes load failed: {exc}"}), file=sys.stderr)

    today = args.date

    if args.entry:
        with open(args.entry, encoding="utf-8") as f:
            entry = json.load(f)
        print(json.dumps(generate(entry, connectors, n8n_nodes, today),
                         ensure_ascii=False, indent=2))
    elif args.entries:
        with open(args.entries, encoding="utf-8") as f:
            entries = json.load(f)
        print(json.dumps(generate_batch(entries, connectors, n8n_nodes, today),
                         ensure_ascii=False, indent=2))
    else:
        print('{"error": "podaj --entry lub --entries"}', file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
