---
name: off-reaktywacja-partnera
version: 1
status: draft
description: "Pisze mail otwierający do uśpionego partnera w brand voice OFF — ciepły, konkretny, z odniesieniem do wspólnej historii."
parent_sop: partner-reaktywacja
triggers:
  - "napisz mail do partnera"
  - "reaktywacja partnera"
  - "odezwij się do partnera"
  - "mail otwierający do partnera"
  - "wznów kontakt z partnerem"

# === KONTRAKT I/O (binding z krokiem 3 SOPa partner-reaktywacja) ===
io:
  input:
    - { name: qualified_partners, type: list<partner>, required: true }
  output:
    - { name: draft_emails, type: list<email_draft> }

# === CAPABILITIES + BEZPIECZEŃSTWO ===
capabilities:
  allow:
    - "skill:off-brand-voice"          # ton OFF
    - "script:scripts/compliance.py"   # redakcja PII przed zwrotem draftu
  deny:
    - "mcp:gmail/*"                     # skill DRAFUJE, nie wysyła (wysyłka = krok 4 / n8n)
side_effects: read-only
autonomy: supervised
guardrails:
  pii_handling: "redact via script:scripts/compliance.py; must_block=true → zwróć błąd, nie draft"
  requires_human_review: false

# === EVALS (golden set — samo-test) ===
evals:
  - { id: 1, input_ref: "examples#1", assert: "output: ton OFF AND zawiera imię partnera AND odniesienie do wspólnej historii AND 0 PII" }
  - { id: 2, input_ref: "examples#2", assert: "output: brak fraz korpo z off-brand-voice deny-listy AND CTA na rozmowę" }
---

# off-reaktywacja-partnera

## Kontekst
Skill dla SOPa `partner-reaktywacja` (krok 3). Dostaje listę partnerów zakwalifikowanych ręcznie
do reaktywacji (krok 2) i dla każdego pisze krótki mail otwierający w tonie OFF. Nie wysyła —
zwraca drafty, które krok 4 (`n8n:mass-send-with-tracking`) wyśle za bramką approval.

## Input format
`qualified_partners`: lista obiektów partnera (nazwa, osoba kontaktowa, ostatni wspólny projekt,
data ostatniego kontaktu). Co najmniej `name` + `contact_person`.

## Output format
`draft_emails`: lista draftów (`to`, `subject`, `body`) — bez nagłówków technicznych, gotowe do
wysyłki. Body 4-6 zdań, jeden konkretny CTA (propozycja rozmowy).

## Examples
**#1 — partner z historią projektową:**
- input: `{name: "Fundacja X", contact_person: "Anna", last_project: "warsztaty 2024", last_contact: "2024-11"}`
- output: mail nawiązujący do warsztatów 2024, ciepły ton, CTA na 20-min call.

**#2 — partner instytucjonalny:**
- input: `{name: "Urząd Y", contact_person: "dyr. Kowalski", last_project: "patronat PM"}`
- output: ton formalny ale ciepły, bez korpo-żargonu, CTA na spotkanie.

## Style guide
Brand voice OFF (delegacja do `skill:off-brand-voice`): bezpośrednio, ciepło, bez korpo-frazesów.
Per-osoba, nie masowo brzmiące.

## Edge cases
- Brak `last_project` → mail ogólny „chcemy wrócić do współpracy", bez wymyślania historii.
- Partner pod NDA z klauzulą anty-AI → zwróć błąd `anti_ai_clause` (SOP zrobi STOP).

## Related skills
`off-brand-voice` (ton), w łańcuchu SOPa po nim: `n8n:mass-send-with-tracking` (wysyłka).

---
<!-- Przykład wzorcowy dla artifacts/skills/SCHEMA.md. io zgodne z krokiem 3 SOPa partner-reaktywacja. -->
