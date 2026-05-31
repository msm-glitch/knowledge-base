---
# === IDENTYFIKACJA ===
slug: partner-reaktywacja
version: 1
status: draft
owner: author
source_url: "https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1"
parent_sop: null                       # root entity

# === WYZWALANIE ===
trigger:
  type: schedule
  spec: quarterly
  description: "Kwartalny przegląd partnerów bez kontaktu >90 dni i próba reaktywacji"
executor_overall: hybrid
frequency: quarterly

# === KONTRAKT I/O (typowany) ===
inputs:
  - name: stale_partners
    type: list<partner>
    source: "mcp:monday/get_board_items_page"
    required: true
outputs:
  - name: reactivation_emails_sent
    type: list<email_ref>
    destination: "mcp:gmail/create_draft"

# === KROKI (rdzeń wykonywalny) ===
steps:
  - id: 1
    action: "Pobierz z CRM partnerów bez kontaktu >90 dni"
    automatable: true
    executor: auto
    tool: "n8n:crm-stale-partners"
    implements: crm-stale-partners
    inputs: []
    outputs: [stale_partners]
    preconditions:
      - "dostęp do board CRM (board_id w config dostępny)"
    postconditions:
      - "stale_partners != null"
    on_error:
      retry: 2
      backoff: "2s,4s"
      escalate_to: maciek
      rollback: null

  - id: 2
    action: "Zweryfikuj dopasowanie (fit) każdego partnera do aktywnych programów"
    automatable: false
    executor: human
    tool: null
    requires_human: "ocena strategiczna — czy partner pasuje do programu w tym kwartale"
    inputs: [stale_partners]
    outputs: [qualified_partners]
    decision:
      criterion: "partner.fit_score >= 0.6 AND program_aktywny == true"
      options: [reactivate, skip, defer]
      decider: author
      fallback: defer
    on_error:
      retry: 0
      escalate_to: author
      rollback: null

  - id: 3
    action: "Napisz mail otwierający w brand voice OFF dla każdego qualified partnera"
    automatable: true
    executor: ai
    tool: "skill:off-reaktywacja-partnera"
    implements: off-reaktywacja-partnera
    inputs: [qualified_partners]
    outputs: [draft_emails]
    preconditions:
      - "skill off-reaktywacja-partnera dostępny w rejestrze zdolności"
    postconditions:
      - "draft_emails.length == qualified_partners.length"
      - "każdy draft przeszedł script:scripts/compliance.py (0 PII must_block)"
    on_error:
      retry: 1
      backoff: "2s"
      escalate_to: maciek
      rollback: null

  - id: 4
    action: "Wyślij maile, zapisz kontakt w CRM, ustaw follow-up +7 dni"
    automatable: true
    executor: auto
    tool: "n8n:mass-send-with-tracking"
    implements: mass-send-with-tracking
    inputs: [draft_emails]
    outputs: [reactivation_emails_sent]
    preconditions:
      - "draft_emails zatwierdzone przez ownera (guardrails.irreversible_actions)"
    postconditions:
      - "każdy wysłany mail ma wpis w CRM (crm_logged == true)"
      - "każdy wysłany mail ma zaplanowany follow-up (followup_scheduled == true)"
    on_error:
      retry: 1
      backoff: "4s"
      escalate_to: maciek
      rollback: "oznacz niewysłane jako pending; NIE wysyłaj duplikatów do już wysłanych"

# === DECYZJE (zbiorczo, dla czytelności) ===
decisions:
  - id: fit-check
    step: 2
    criterion: "partner.fit_score >= 0.6 AND program_aktywny == true"
    decider: author
    fallback: defer

# === GUARDRAILS (granice władzy agenta) ===
guardrails:
  autonomy_level: supervised
  irreversible_actions: [4]                  # krok 4 = wysyłka outbound (nieodwracalna)
  pii_handling: "redact via script:scripts/compliance.py przed każdym outputem; must_block=true → STOP"
  escalation: wojciech
  anti_ai_clause: "STOP jeśli którykolwiek partner jest pod NDA z klauzulą anty-AI"

# === KRYTERIA AKCEPTACJI (maszynowo sprawdzalne) ===
acceptance_criteria:
  - "reactivation_emails_sent.length == count(qualified_partners where decision == reactivate)"
  - "0 maili wysłanych do partnerów z decision ∈ {skip, defer}"
  - "wszystkie wysłane maile: crm_logged == true AND followup_scheduled == true"

# === FEEDBACK LOOP (co agent loguje po wykonaniu) ===
metrics:
  log_to: "state/runs.jsonl"
  fields: [run_id, started_at, stale_count, qualified_count, emails_sent, human_interventions, errors, duration_s]
---

# Partner-reaktywacja

> Auto-gen 2026-05-31 (PRZYKŁAD wzorcowy, redagowany ręcznie — ilustruje
> [`../SCHEMA.md`](../SCHEMA.md)) · Owner: autor wzorca · Status: Draft · Executor: Hybrid

Kwartalny proces odzyskiwania uśpionych partnerów. Demonstruje SOP jako encję root z trzema
sub-resources: `crm-stale-partners` (n8n), `off-reaktywacja-partnera` (skill),
`mass-send-with-tracking` (n8n).

## Trigger
Kwartalnie (`schedule`) — przegląd partnerów bez kontaktu od >90 dni.

## Steps

| # | Akcja | Executor | Tool (binding) | Automatable |
|---|---|---|---|---|
| 1 | Pobierz uśpionych partnerów z CRM | auto | `n8n:crm-stale-partners` | ✅ tak |
| 2 | Zweryfikuj fit do aktywnych programów | human | — | ❌ nie (osąd) |
| 3 | Napisz mail otwierający (brand voice OFF) | ai | `skill:off-reaktywacja-partnera` | ✅ tak |
| 4 | Wyślij + zapisz w CRM + follow-up | auto | `n8n:mass-send-with-tracking` | ✅ tak (za bramką) |

3/4 kroki są automatyzowalne; jedyny `automatable: false` to krok 2 (osąd strategiczny).

## Decisions
- **fit-check** (krok 2): `fit_score >= 0.6 AND program_aktywny` → `reactivate` / `skip` / `defer`.
  Decydent: autor. Fallback: `defer`.

## Guardrails
- Poziom autonomii: **supervised** (agent działa sam, ale loguje i da się cofnąć).
- Krok 4 (wysyłka outbound) = **nieodwracalny** → wymaga approval ownera przed wykonaniem.
- PII: redakcja przez `scripts/compliance.py` przed każdym outputem; `must_block` → STOP.
- STOP, jeśli partner pod NDA z klauzulą anty-AI (eskalacja: Wojciech).

## Definition of Done
- [ ] Liczba wysłanych maili == liczba partnerów z decyzją `reactivate`.
- [ ] 0 maili do partnerów z decyzją `skip`/`defer`.
- [ ] Każdy wysłany mail ma wpis w CRM i zaplanowany follow-up.

---
<!-- Przykład wzorcowy dla artifacts/sops/SCHEMA.md. NIE jest to artefakt z realnego skanu. -->
