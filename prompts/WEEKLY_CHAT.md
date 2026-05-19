# Knowledge Base — Weekly Scan Chat

**Wersja:** 1.1 | **Data:** 2026-05-19 | **Tryb:** WEEKLY (co poniedziałek 10:00)

**Przeznaczenie:** Cotygodniowy skan w Claude Chat — ostatnie 7 dni.

**Setup:** Ustaw przypomnienie Google Calendar co poniedziałek 10:00. Chat nie ma scheduled task — manual.

---

## PROMPT WEEKLY — skopiuj i wklej w Claude Chat:

```
# WEEKLY KNOWLEDGE BASE SCAN v1.1 — Chat

Przeprowadź cotygodniowy skan Knowledge Base — ostatnie 7 dni.

Tryb: weekly

## PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 3 pytania. **Nie przechodzę dalej dopóki nie odpiszesz — nie zakładam żadnych wartości domyślnych.**

---

**[1/3] Search & reference chats**
Czy masz włączone "Search and reference chats" w Settings → Privacy?
→ Odpowiedz: TAK / NIE

*Jeśli NIE: przerwij i napisz instrukcję jak włączyć.*

---

**[2/3] Twoje dane**
Podaj imię i email @off.org.pl.
→ Odpowiedz np.: "Maciek, maciek@off.org.pl"

*Nie zgaduję ani nie zakładam danych — wymagam jawnego wpisu.*

---

**[3/3] Potwierdzenie zakresu**
Skanem objęte: ostatnie 7 dni (Chat + Gmail + Slack + Drive).
Czy jest coś co chcesz wyłączyć lub zawęzić?
→ Odpowiedz: OK lub podaj wyjątki

---

⛔ **Czekam na Twoje odpowiedzi [1], [2], [3] — dopiero potem zaczynam skan.**

## PHASE 0.5: CROSS-CUTTING CONCERNS (Chat — Weekly)

**Budget cap:** ~80K tokenów. Chat nie ma lokalnych JSONL.
Jeśli cap osiągnięty: zakończ bieżące źródło, zapisz drafty, zaraportuj "Budget cap reached".

**Rate limity MCP:** max 10 wywołań/min. Przy 429: backoff 2s→4s→8s (max 3 próby).

**BEZ SQLite / BEZ /runs/ na dysk.** Drafty in-memory → Notion.

Zakres: ostatnie 7 dni (od [DATA_TYDZIEŃ_TEMU] do dziś)

## PHASE 1: SCAN — Chat (ostatnie 7 dni)

Używając "Search and reference chats" przejrzyj rozmowy z ostatnich 7 dni.

Dla każdej:
- Data, temat, cel, wynik
- Czy zadanie powtarzało się (vs poprzednie tygodnie)?
- Czy Claude nie poradził sobie → kandydat na automatyzację?

## PHASE 2-4: Gmail + Slack + Drive (ostatnie 7 dni)

- Gmail: `config/sources.yaml → gmail.query_spec.weekly` (newer_than:7d)
- Slack: `config/sources.yaml → slack`, lookback 7d, kanały z `channel_ids`
- Drive: pliki zmienione w ostatnich 7 dniach

## PHASE 5: KLASYFIKACJA — rozłączne drzewo 4-krokowe

Tylko NOWE wzorce (sprawdź Notion KB):

```
1. Merytoryczny + powtarzalny + jasny input/output?
   NIE → POMIŃ
   TAK → pytanie 2

2. Wymaga ludzkiego osądu / decyzji / accountability?
   TAK → SOP (Human/Hybrid) → Related skills / n8n
   NIE → pytanie 3

3. Output kreatywny / wariantowy / brand voice OFF?
   TAK → Skill Backlog (WYMAGANE: ≥3 wystąpienia)
   NIE → pytanie 4

4. Jasny deterministyczny trigger + pipeline?
   TAK → n8n Automation (WYMAGANE: ≥2 wystąpienia)
   NIE → SOP (Human)
```

**Progi:** SOP ≥2 | Skill ≥3 | n8n ≥2. Poniżej → `candidate_{type}`, NIE do Notion.

## PHASE 5.5: DUAL-PASS + QUALITY GATES

**Pass 1:** Zbierz drafty w pamięci. **Pass 2:** Checklist przed zapisem:
```
[ ] Skip: meta / "stan skilla" / poniżej progu → odrzuć
[ ] Cross-check z config/skills_catalog.yaml — match? → [FIX]; skip_meta? → POMIŃ
[ ] Source URL / User=autor / Date=oryginał / Title [NEW|FIX|BUG] / Summary + "Next: ___"
[ ] Jeśli Type=Skill lub n8n: Parent SOP wskazany (slug lub "—")
[ ] Occurrence ≥ progu per typ
```

**✅ DOBRY:** `[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' [5× miss, Chat-link]. Parent SOP: —`
**❌ ZŁY:** meta-wpisy, Skill <3×, "stan skilla", User=skanujący, Date=dziś, n8n bez Error handling

---

## PHASE 5.5b: QUALITY GATES

❌ **NIE ZAPISUJ jeśli:** meta-wpisy (knowledge-base, WSD), "stan istniejącego skilla" bez konkretu, poniżej progu.

✅ **Title prefix:** `[NEW]` / `[FIX]` / `[BUG]`
✅ **Source URL WYMAGANE** (link do oryginału lub `—`)
✅ **User = autor wzorca, NIE skanujący**
✅ **Date = data ORYGINALNEGO zdarzenia, NIE dziś**
✅ **Parent SOP** = slug dla Skill/n8n, lub `—`
✅ **n8n MUSI mieć** Error handling (retry + dead letter + Slack alert)

---

## PHASE 6: ZAPIS DO NOTION

- DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Scan type: Weekly, Week: `{ISO_YEAR}-W{ISO_WEEK}`, Status: New
- User: Notion Person ID (z `config/notion.yaml`)
- Dodaj pola: **Owner**, **Parent SOP**
- Per Type (SOP/Skill/n8n): dodaj pola z Schema 4A/4B/4C (patrz SKILL.md)
- n8n: **Error handling**, **Credentials**, **Dependencies**, **Test plan** — obowiązkowe

## PHASE 7: OUTPUT

```
🔄 Knowledge Base Weekly — [Imię] — [Data]

Przeskanowano (7 dni): Chat: X | Gmail: X | Slack: X | Drive: X
Nowe odkrycia: Z (SOP: N | Skill: N | n8n: N | Pominięto: N)
📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

Jeśli ≥1 High priority → wyślij post do Slack #ai-feedback (C0AS00SNGQZ).
Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=weekly, discoveries={N}, by_type={SOP:N, Skill:N, n8n:N}`
```

---

*Prompt: WEEKLY_CHAT.md v1.1 · knowledge-base · msm-glitch/knowledge-base*
