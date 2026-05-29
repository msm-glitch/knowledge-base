# Knowledge Base — Bootstrap Chat (lifetime scan)

**Wersja:** 2.2 | **Data:** 2026-05-19 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w Claude Chat (claude.ai) jednorazowo — lifetime scan historii rozmów + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_CHAT.md`.

**Wymagania:**
- Konto claude.ai (Pro/Team)
- ⚠️ **"Search and reference chats" OBOWIĄZKOWO włączone** (Settings → Privacy)
- Dostęp do Gmail, Slack #ai-feedback, Google Drive OFF

**Czas:** ~20-30 min

---

## PROMPT BOOTSTRAP — skopiuj i wklej w Claude Chat:

```
# BOOTSTRAP KNOWLEDGE BASE v2.2 — LIFETIME SCAN (Chat)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan mojej historii rozmów z Claude.

## PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 3 pytania. **Nie przechodzę dalej dopóki nie odpiszesz na wszystkie — nie zakładam żadnych wartości domyślnych.**

Wyświetl poniższy formularz i czekaj:

---

**[1/3] Search & reference chats**
Czy masz włączone "Search and reference chats" w Settings → Privacy?
→ Odpowiedz: TAK / NIE

*Jeśli NIE: przerwij i napisz "Włącz 'Search and reference chats' w claude.ai → Settings → Privacy, potem wróć z tym promptem."*

---

**[2/3] Twoje dane**
Podaj imię i email @off.org.pl.
→ Odpowiedz np.: "Maciek, maciek@off.org.pl"

*Nie zgaduję ani nie zakładam danych — wymagam jawnego wpisu.*

---

**[3/3] Zakres skanu**
Które rozmowy skanować?
→ Wybierz i odpisz literę:
(a) Wszystkie rozmowy (lifetime — od pierwszej do dziś)
(b) Tylko OFF-related (pomijam rozmowy prywatne/osobiste)
(c) Wybiórczo — dopisz zakres dat lub tematy np. "od 2026-01-01"

---

⛔ **Czekam na Twoje odpowiedzi [1], [2], [3] — dopiero potem zaczynam skan.**

## PHASE 0.5: CROSS-CUTTING CONCERNS (Chat)
**Gate konfiguracji (item #1) — STOP jeśli niepełna:**
Jeśli masz terminal/repo: `python3 scripts/kb_setup.py validate` (exit≠0 → pokaż błędy, `resolve`, STOP).
W Chat/Cowork sprawdź ręcznie, że `config/notion.yaml → users` i `config/sources.yaml → slack.channel_ids`
nie są puste — jeśli są, STOP i uzupełnij (inaczej zła atrybucja / martwe kanały).


**Budget cap:** ~80K tokenów (Chat nie ma lokalnych JSONL — skanujemy tylko Chat history + MCP sources).
Jeśli cap osiągnięty: zakończ bieżące źródło, zapisz zebrane drafty, zaraportuj "Budget cap reached".

**Model:** modele per pass wg `config/sources.yaml → models` (Sonnet: skan · Haiku: token strategy Light · Opus: bootstrap Deep na żądanie).

**Rate limity MCP:** max 10 wywołań/min na źródło. Przy 429: backoff 2s→4s→8s (max 3 próby). Po 3 fail: `source_error`, kontynuuj.

**Error handling:**
- MCP timeout → retry 2× → `needs_enrichment = true`
- Notion write fail → retry 1× → log
- Anti-AI clause → STOP natychmiast

**BEZ lokalnego SQLite / BEZ /runs/ na dysk.** (item #4: lekki stan w `state/` — ledger kandydatów + watermarki, scripts/kb_state.py) Drafty in-memory → Notion. Odrzucone → `Status = Rejected`.

## PHASE 1: SCAN — Claude Chat history

Użyj "Search and reference chats" żeby przeskanować pełną historię moich rozmów.

Dla każdej rozmowy odnotuj:
- Data, temat/tytuł
- Cel zadania i wynik
- Domena: PM / Mini Granty / Marketing / Ops / Legal / Inne
- Czy zawierała PII? → REDACT summary
- Czy zadanie się powtarzało w innych rozmowach?
- Skille/triggery użyte (jeśli widoczne)
- Czy Claude nie poradził sobie → potencjalna automatyzacja?

⚠️ Auto-skip:
- Rozmowy z tagiem legal/private (akta-kcs, UDIP, KRS)
- Rozmowy z NDA → FLAG w raporcie, nie cytuj
- Rozmowy osobiste (poza OFF) → skip lub user confirm
- Klauzula anty-AI → STOP

## PHASE 2: SCAN — Gmail

Przez Gmail MCP, użyj `config/sources.yaml → gmail.query_spec.bootstrap`:
- Query: `(decyzja OR pipeline OR powtarzalny OR automatyzacja OR SOP OR procedura) -label:SPAM -label:TRASH`
- Lookback: 90 dni
- SKIP: wątki z PESEL, NIP → REDACT

## PHASE 3: SCAN — Slack

Przez Slack MCP, użyj `config/sources.yaml → slack`, lookback 90 dni:
- Kanały: #general, #ai-feedback (C0AS00SNGQZ), #planer-dnia, #brand-team, #mini-granty
- Szukaj: pytania powtarzające się, frustracje, decyzje
- SKIP: hasła, tokeny

## PHASE 4: SCAN — Google Drive

Przez Drive MCP, pliki OFF zmienione w ostatnich 90 dniach:
- Odnotuj instrukcje, szablony, procedury → SOP candidates

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

**Pass 1 (draft):** Zbierz wszystkie kandydatów w pamięci. NIE zapisuj jeszcze do Notion.

**Pass 2 (weryfikacja):** Dla każdego draftu przejdź checklist:
```
[ ] Skip rules: nie meta, nie "stan skilla bez konkretu", poniżej progu → odrzuć
[ ] Cross-check z config/skills_catalog.yaml:
    - fuzzy match nazwy → [FIX]; skip_meta → POMIŃ
[ ] Source URL wypełniony (lub jawnie "—")
[ ] User = autor wzorca (nie skanujący), mapuj email→Notion Person ID
[ ] Date = data oryginalnego zdarzenia, nie dziś
[ ] Title z prefiksem [NEW]/[FIX]/[BUG]
[ ] Summary: liczba × + dowód + konkret + "Next: ___"
[ ] Jeśli Type=Skill lub n8n: Parent SOP wskazany (slug lub "—")
[ ] Occurrence ≥ progu per typ
```

### Few-shot — naucz się z prawdziwych przypadków:

**✅ DOBRY [FIX]:**
```
[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' do triggerów
Priority: High (5× miss = intra-source intensity)
Source: [Claude Chat] | URL: https://claude.ai/chat/abc | Date: 2026-05-11
Summary: 5× ręczne przepisanie 5-11.05. Fix: dodać do triggerKeywords. Next: Wojciech.
Parent SOP: —
```

**✅ DOBRY [NEW] n8n:**
```
[NEW] 2026-05-15 · Maciek · Masowy outreach do MR — szablon ×10+
Priority: High (10+ wystąpień + cross-source 2)
Source: [Gmail, Chat] | URL: https://mail.google.com/.../thread-xyz | Date: 2026-05-15
Summary: 10+ maili do MR identycznym szablonem. n8n: lista→personalizacja→auto-send. ~2h/kampanię. Next: Maciek buduje flow.
Parent SOP: mr-mass-outreach
```

**❌ ZŁE — odrzucaj/poprawiaj:**
- `Weekly Knowledge Scan` → META, POMIŃ
- `Skill — nowy-mail` ale 2× → poniżej progu min=3 → POMIŃ, flag candidate_skill
- `User: Maciek` dla Slack-post Michała → wrong attribution
- `Date: dziś` → powinno być data oryginalnego zdarzenia
- n8n bez pola Error handling → obowiązkowe

---

## PHASE 5.5b: QUALITY GATES

❌ **NIE ZAPISUJ jeśli:**
- Wpis dotyczy `knowledge-base`, `weekly-discovery`, `team-knowledge-base`, `WSD`
- "Stan istniejącego skilla" bez konkretnej poprawki
- Poniżej progu: Skill<3, SOP<2, n8n<2

✅ **Title prefix:** `[NEW]` nowy / `[FIX]` poprawka / `[BUG]` bug
✅ **Source URL WYMAGANE** (link do oryginału lub `—`)
✅ **User = autor wzorca, NIE skanujący** (mapuj email na Notion Person ID)
✅ **Date = data oryginalnego zdarzenia** (nie dziś)
✅ **Parent SOP** = slug dla Skill/n8n, lub `—`
✅ **n8n MUSI mieć** Error handling (retry + dead letter + Slack alert)

---

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ):
- Notion Knowledge Base DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Scan type: Bootstrap

**Pola wspólne:** Title, Type, Source, Date, Week, Summary, Priority, Status=New, User (Notion Person ID z `config/notion.yaml`), Source URL, Source examples, Occurrences, Sources count, Time saved, Implementation size, **Owner**, **Parent SOP**, ROI score.

**Pola per Type:**
- SOP: Process slug, Trigger, Inputs, Outputs, Steps (N. Imperatyw. Executor. Output.), Decisions, Definition of Done, Edge cases, Executor overall, Frequency, Related skills, Related n8n
- Skill: Skill name, Description, Trigger phrases (≥5 DOSŁOWNIE z source), Input/Output format, Examples (pary input+output), Persona/style guide, Edge cases
- n8n: Flow name, Trigger, Data sources, Transformations, Destinations, **Error handling** (retry+dead letter+alert OBOWIĄZKOWE), Volume estimate, Manual steps remaining, **Credentials**, **Dependencies**, **Test plan**

## PHASE 7: OUTPUT

Po zapisie wydrukuj:
```
📊 Knowledge Base Bootstrap — [Imię] — [Data]

Przeskanowano:
  • Chat:   X rozmów / Y odkryć
  • Gmail:  X wątków / Y odkryć
  • Slack:  X wiadomości / Y odkryć
  • Drive:  X plików / Y odkryć

🎯 Łącznie: Z odkryć → Notion
  • SOP: N  • Skill: N  • n8n: N
  • Pominięto: N (poniżej progu / brak powtarzalności)

🏆 Top 3: 1. [High]... 2. [High]... 3. [Medium]...

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

## PHASE 8: POST-BOOTSTRAP

1. Wyślij post do Slack #ai-feedback (C0AS00SNGQZ)
2. Przypomnij: ustaw przypomnienie Google Calendar co poniedziałek 10:00 z `WEEKLY_CHAT.md`
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap, discoveries={N}, by_type={SOP:N, Skill:N, n8n:N}, rejected={N}`
```

---

*Prompt: BOOTSTRAP_CHAT.md v2.2 · knowledge-base · msm-glitch/knowledge-base*
