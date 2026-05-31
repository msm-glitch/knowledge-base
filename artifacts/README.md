# artifacts/ — schematy i przykłady kanoniczne (referencja, nie generator)

Katalog zawiera **specyfikacje formatów** (SCHEMA.md) i **wzorcowe przykłady** artefaktów
SOP / n8n / Skill. Są referencją dla agenta i dla przeglądu kodu — nie są generowane tutaj
podczas skanu.

> **Gdzie trafiają wygenerowane artefakty?** Bezpośrednio do Notion (Krok 4.5 SKILL.md):
> - SOP → `🪩 Baza SOPs` (`config/notion.yaml → databases.sops`)
> - n8n / Skill → `🛠️ Skills & Automation Backlog` (`databases.skills_backlog`)

## Struktura

```
artifacts/
├── sops/
│   ├── SCHEMA.md                          # specyfikacja formatu SOP (agent-executable)
│   └── examples/partner-reaktywacja.md    # wzorzec kanoniczny
├── n8n/
│   ├── SCHEMA.md                          # specyfikacja kontraktu meta{} n8n
│   └── examples/
│       ├── mass-send-with-tracking.json   # wzorzec: external-send + guardrails
│       └── crm-stale-partners.json        # wzorzec: read-only query
└── skills/
    ├── SCHEMA.md                          # specyfikacja kontraktu SKILL.md
    └── examples/
        └── off-reaktywacja-partnera/SKILL.md  # wzorzec: io + capabilities
```

## Cykl życia artefaktu (Notion-based)

| Stan | Co się dzieje | Kto |
|---|---|---|
| **Draft** | Krok 4.5 tworzy stronę w Notion (Select: "Wersja robocza" / Status: "Idea") | skill (auto) |
| **Review** | Owner edytuje pola `[TBD]`, weryfikuje io/guardrails | owner |
| **Zatwierdzony** | Owner zmienia Select → "Zatwierdzony" (SOP) / Status → "Spec" (Skill/n8n) | owner |
| **Implemented** | Po wdrożeniu: Status → "Shipped" (Skill/n8n) / wpis KB → "Implemented" | owner |
| **Odrzucony** | Owner usuwa stronę lub zmienia status; wpis KB → "Rejected" | owner |

## Walidacja formatu (skrypty)

Przykłady w `examples/` przechodzą przez walidator przy każdym `git push`:

```bash
python3 scripts/sop_schema.py validate          # sprawdź spójność artifacts/
python3 -m unittest discover -s scripts/tests -v
```

`scripts/sop_schema.py` weryfikuje: slug kebab-case, unikalność, binding io SOP↔skill↔n8n,
SAFETY gate (external-send/irreversible ⇒ w guardrails.irreversible_actions).

## Dodawanie nowych wzorców

Wzorce kanoniczne (`examples/`) umieszczaj ręcznie po merge zaakceptowanego artefaktu z Notion.
Pomagają agentowi podczas generacji (adaptacyjny template z Krok 4.5).
