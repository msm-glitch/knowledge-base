# Knowledge Base — Bootstrap Cowork (lifetime scan)

**Wersja:** 2.2 | **Data:** 2026-05-19 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w sesji Claude Cowork jednorazowo — lifetime scan wszystkich sesji Cowork + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_COWORK.md`.

**Dla kogo:** Wszyscy członkowie zespołu OFF używający Cowork (11 osób).

**Czas:** ~30-45 min

---

## PROMPT BOOTSTRAP — skopiuj i wklej w Cowork:

```
# BOOTSTRAP KNOWLEDGE BASE v2.2 — LIFETIME SCAN (Cowork)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan.

## PHASE 0: PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 2 pytania. **Nie przechodzę dalej dopóki nie odpiszesz — nie zakładam żadnych wartości domyślnych.**

---

**[1/2] Twoje dane**
Podaj imię i email @off.org.pl.
→ Odpowiedz np.: "Maciek, maciek@off.org.pl"

*Nie zgaduję ani nie zakładam danych — wymagam jawnego wpisu.*

---

**[2/2] Zakres skanu**
Które sesje Cowork skanować?
→ Wybierz i odpisz literę:
(a) Wszystkie sesje (lifetime — od pierwszej do dziś)
(b) Tylko OFF-related (pomijam sesje prywatne/osobiste)
(c) Wybiórczo — dopisz zakres dat np. "od 2026-01-01"

---

⛔ **Czekam na Twoje odpowiedzi [1], [2] — dopiero potem zaczynam skan.**

## PHASE 0.5: CROSS-CUTTING CONCERNS (Cowork)
**Gate konfiguracji (item #1) — STOP jeśli niepełna:**
Jeśli masz terminal/repo: `python3 scripts/kb_setup.py validate` (exit≠0 → pokaż błędy, `resolve`, STOP).
W Chat/Cowork sprawdź ręcznie, że `config/notion.yaml → users` i `config/sources.yaml → slack.channel_ids`
nie są puste — jeśli są, STOP i uzupełnij (inaczej zła atrybucja / martwe kanały).


**Budget cap:** ~80K tokenów (Cowork nie ma lokalnych JSONL).
Jeśli cap osiągnięty: zakończ bieżące źródło, zapisz zebrane drafty, zaraportuj "Budget cap reached".

**Model:** modele per pass wg `config/sources.yaml → models` (Sonnet: skan · Haiku: token strategy Light · Opus: bootstrap Deep na żądanie).

**Rate limity MCP:** max 10 wywołań/min na źródło. Przy 429: backoff 2s→4s→8s (max 3 próby).

**Error handling:**
- MCP timeout → retry 2× → `needs_enrichment = true`
- Notion write fail → retry 1× → log
- Anti-AI clause → STOP natychmiast

**BEZ SQLite / BEZ /runs/ na dysk.** (item #4: lekki stan w `state/` — ledger kandydatów + watermarki, scripts/kb_state.py) Drafty in-memory → Notion. Odrzucone → `Status = Rejected`. Do wzbogacenia → `Status = Draft`.

## PHASE 1: SCAN — Cowork sessions

Pobierz pełną listę sesji:
- `list_sessions(all_time=true)` (bootstrap)

Dla każdej sesji odnotuj:
- Data, tytuł, główne zadanie
- Skille użyte (jeśli widoczne w transcript)
- Domena (Mini Granty / Marketing / PM / Ops / etc.)
- Czy zadanie się powtarzało?
- Czy Claude nie mógł sobie poradzić sam → potencjalna automatyzacja?

⚠️ Auto-skip:
- Sesje legal (akta-kcs, UDIP, KRS)
- Sesje z PII beneficjentów → REDACT summary

## PHASE 2: SCAN — Gmail

Przez Gmail MCP, użyj `config/sources.yaml → gmail.query_spec.bootstrap`:
- Query: `(decyzja OR pipeline OR powtarzalny OR automatyzacja OR SOP OR procedura) -label:SPAM -label:TRASH`
- Lookback: 90 dni
- SKIP: wątki z PESEL, NIP → REDACT

## PHASE 3: SCAN — Slack

Przez Slack MCP, użyj `config/sources.yaml → slack`, lookback 90 dni:
- Kanały: #general, #ai-feedback (C0AS00SNGQZ), #planer-dnia, #brand-team, #full-team
- ⛔ #mini-granty WYKLUCZONY (PII beneficjentów) — patrz `config/sources.yaml → slack.excluded_channels`
- Szukaj: pytania powtarzające się, prośby o pomoc, frustracje, decyzje
- SKIP: hasła, tokeny, dane poufne

## PHASE 4: SCAN — Google Drive

Przez Drive MCP, folder `1U10_VXe_qxoYOlrSyIpgQKXOUy-og1D-`, lookback 90 dni:
- Odnotuj: tytuły, typy dokumentów, czy sugerują powtarzalny proces

## PHASE 5: KLASYFIKACJA — rozłączne drzewo 4-krokowe

Dla każdego wzorca pytaj **po kolei**:

```
1. Merytoryczny + powtarzalny + jasny input/output?
   NIE → POMIŃ (jednorazowe, meta, preferencja osobista)
   TAK → pytanie 2

2. Wymaga ludzkiego osądu / decyzji / accountability?
   TAK → SOP (Executor: Human lub Hybrid)
       → Krok AI-kreatywny? → Related skills
       → Krok deterministyczny? → Related n8n
   NIE → pytanie 3

3. Output kreatywny / wariantowy / brand voice OFF?
   TAK → Skill Backlog (WYMAGANE: ≥3 wystąpienia)
       → skills_catalog.yaml: istnieje? → [FIX]
   NIE → pytanie 4

4. Jasny deterministyczny trigger + pipeline?
   TAK → n8n Automation (WYMAGANE: ≥2 wystąpienia)
   NIE → SOP (Human)
```

**Progi:** SOP ≥2 | Skill ≥3 | n8n ≥2. Poniżej → `candidate_{type}`, NIE do Notion.

## PHASE 5.5: DUAL-PASS + QUALITY GATES

**Pass 1 (draft):** Zbierz kandydatów w pamięci. NIE zapisuj.

**Pass 2 (weryfikacja) — checklist każdego draftu:**
```
[ ] Skip: nie meta, nie "stan skilla", nie poniżej progu → odrzuć
[ ] Cross-check z config/skills_catalog.yaml — match? → [FIX]; skip_meta? → POMIŃ
[ ] Source URL wypełniony lub "—"
[ ] User = autor wzorca (mapuj email→Notion Person ID)
[ ] Date = data oryginalnego zdarzenia
[ ] Title [NEW]/[FIX]/[BUG]
[ ] Summary: liczba × + dowód + konkret + "Next: ___"
[ ] Jeśli Type=Skill lub n8n: Parent SOP wskazany (slug lub "—")
[ ] Occurrence ≥ progu per typ
```

### Few-shot:

**✅ DOBRY:** `[NEW] 2026-05-15 · Maciek · Masowy outreach MR — ×10+, Gmail+Chat, ~2h/kampanię. Parent SOP: mr-mass-outreach`
**❌ ZŁY:** `Weekly Knowledge Scan` (meta) / `Skill 2×` (poniżej min=3) / `User: Maciek` dla problemu Michała / `Date: dziś` / n8n bez Error handling

---

## PHASE 5.5b: QUALITY GATES

❌ **NIE ZAPISUJ jeśli:**
- Meta-wpisy (knowledge-base, WSD, etc.)
- "Stan istniejącego skilla" bez konkretu
- Poniżej progu: Skill<3, SOP<2, n8n<2

✅ **Title prefix:** `[NEW]` nowy / `[FIX]` poprawka / `[BUG]` bug
✅ **Source URL WYMAGANE** (Cowork session ID lub `—`)
✅ **User = autor wzorca, NIE skanujący**
✅ **Date = data ORYGINALNEGO zdarzenia**
✅ **Parent SOP** = slug dla Skill/n8n, lub `—`
✅ **n8n MUSI mieć** Error handling (retry + dead letter + Slack alert)

---

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ):
- Notion Knowledge Base DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Scan type: Bootstrap, Status: New

**Pola wspólne:** Title, Type, Source, Date, Week, Summary, Priority, User (Notion Person ID z `config/notion.yaml`, fallback: `User name (fallback)` dla Krzysztofa i Roksany), Source URL, Source examples, Occurrences, Sources count, Time saved, Implementation size, **Owner**, **Parent SOP**, ROI score.

**Pola per Type:**
- SOP: Process slug, Trigger, Inputs, Outputs, Steps (N. Imperatyw. Executor. Output.), Decisions, Definition of Done, Edge cases, Executor overall, Frequency, Related skills, Related n8n
- Skill: Skill name, Description, Trigger phrases (≥5 DOSŁOWNIE z source), Input/Output format, Examples, Persona/style guide, Edge cases
- n8n: Flow name, Trigger, Data sources, Transformations, Destinations, **Error handling** (OBOWIĄZKOWE), Volume estimate, Manual steps remaining, **Credentials**, **Dependencies**, **Test plan**

## PHASE 7: OUTPUT

Po zapisie wydrukuj:
```
📊 Knowledge Base Bootstrap — [Imię] — [Data]

Przeskanowano:
  • Cowork:  X sesji / Y odkryć
  • Gmail:   X wątków / Y odkryć
  • Slack:   X wiadomości / Y odkryć
  • Drive:   X plików / Y odkryć

🎯 Łącznie: Z odkryć → Notion
  • SOP: N  • Skill Backlog: N  • n8n: N
  • Pominięto: N (poniżej progu / brak powtarzalności)

🏆 Top 3 priorytety:
1. [High] ... 2. [High] ... 3. [Medium] ...

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

## PHASE 8: POST-BOOTSTRAP

1. Wyślij post do Slack #ai-feedback (C0AS00SNGQZ)
2. Zaproponuj setup cotygodniowego scheduled task:
   - (a) Poniedziałek 10:00 [rekomendowane]
   - (b) Piątek 15:00
   - (c) Nie — uruchamiam manualnie
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap, discoveries={N}, by_type={SOP:N, Skill:N, n8n:N}, rejected={N}`
```

---

*Prompt: BOOTSTRAP_COWORK.md v2.2 · knowledge-base · msm-glitch/knowledge-base*
