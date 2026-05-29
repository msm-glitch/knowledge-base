# Knowledge Base — Weekly Scan Cowork

**Wersja:** 2.2 | **Data:** 2026-05-19 | **Tryb:** WEEKLY (co poniedziałek 10:00)

**Przeznaczenie:** Cotygodniowy skan w Cowork — ostatnie 7 dni. Zaplanuj jako scheduled task po bootstrapie.

---

## AKTYWACJA SCHEDULED TASK (jednorazowo po bootstrapie):

```
Zaplanuj cotygodniowe zadanie: Knowledge Base Weekly Scan.

Harmonogram: co poniedziałek o 10:00 (Europe/Warsaw).

---
# WEEKLY KNOWLEDGE BASE SCAN v2.2 — Cowork (Scheduled Task)

Przeprowadź cotygodniowy skan Knowledge Base — ostatnie 7 dni.

## PHASE 0: PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 2 pytania. **Nie przechodzę dalej dopóki nie odpiszesz — nie zakładam żadnych wartości domyślnych.**

---

**[1/2] Twoje dane**
Podaj imię i email @off.org.pl.
→ Odpowiedz np.: "Maciek, maciek@off.org.pl"

*Nie zgaduję ani nie zakładam danych — wymagam jawnego wpisu.*

---

**[2/2] Potwierdzenie zakresu**
Skanem objęte: ostatnie 7 dni (Cowork + Gmail + Slack + Drive).
Czy jest coś co chcesz wyłączyć lub zawęzić?
→ Odpowiedz: OK lub podaj wyjątki

---

⛔ **Czekam na Twoje odpowiedzi [1], [2] — dopiero potem zaczynam skan.**

## PHASE 0.5: CROSS-CUTTING CONCERNS (Cowork — Weekly)
**Gate konfiguracji (item #1) — STOP jeśli niepełna:**
Jeśli masz terminal/repo: `python3 scripts/kb_setup.py validate` (exit≠0 → pokaż błędy, `resolve`, STOP).
W Chat/Cowork sprawdź ręcznie, że `config/notion.yaml → users` i `config/sources.yaml → slack.channel_ids`
nie są puste — jeśli są, STOP i uzupełnij (inaczej zła atrybucja / martwe kanały).


**Budget cap:** ~80K tokenów. Cowork nie ma lokalnych JSONL.
Jeśli cap osiągnięty: zakończ bieżące źródło, zapisz drafty, zaraportuj "Budget cap reached".

**Rate limity MCP:** max 10 wywołań/min. Przy 429: backoff 2s→4s→8s (max 3 próby).

**BEZ SQLite / BEZ /runs/ na dysk.** (item #4: lekki stan w `state/` — ledger kandydatów + watermarki, scripts/kb_state.py) Drafty in-memory → Notion. Odrzucone → `Status = Rejected`.

Po odpowiedziach załaduj konfigurację:
- Notion DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- User: mapuj email na Notion Person ID z `config/notion.yaml`
- Zakres: ostatnie 7 dni

## PHASE 1: SCAN — Cowork sessions (ostatnie 7 dni)

`list_sessions(since="-7d")` — tylko nowe sesje od ostatniego scanu.

Dla każdej sesji:
- Data, tytuł, skille, domena
- Czy zadanie powtarzało się w poprzednich tygodniach? (sprawdź Notion KB)
- Czy wynik był nieoptymalny? → potencjalna automatyzacja

## PHASE 2-4: Gmail + Slack + Drive (ostatnie 7 dni)

- Gmail: `config/sources.yaml → gmail.query_spec.weekly` (newer_than:7d)
- Slack: `config/sources.yaml → slack`, lookback 7d, kanały z `channel_ids`
- Drive: pliki zmienione w ostatnich 7 dniach

## PHASE 5: KLASYFIKACJA — rozłączne drzewo 4-krokowe

Tylko NOWE wzorce (nie ma ich jeszcze w Notion Knowledge Base):

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

**✅ DOBRY:** `[NEW] 2026-05-15 · Maciek · Masowy outreach MR — ×10+, Gmail+Chat. Parent SOP: mr-mass-outreach`
**❌ ZŁY:** meta / Skill <3× / "wymaga doprecyzowania" / User=skanujący / n8n bez Error handling

---

## PHASE 5.5b: QUALITY GATES

❌ **NIE ZAPISUJ jeśli:** meta-wpisy (knowledge-base, WSD), "stan skilla" bez konkretu, poniżej progu.

✅ **Title prefix:** `[NEW]` / `[FIX]` / `[BUG]`
✅ **Source URL WYMAGANE** (Cowork session ID lub `—`)
✅ **User = autor wzorca, NIE skanujący**
✅ **Date = data ORYGINALNEGO zdarzenia, NIE dziś**
✅ **Parent SOP** = slug dla Skill/n8n, lub `—`
✅ **n8n MUSI mieć** Error handling (retry + dead letter + Slack alert)

---

## PHASE 6: ZAPIS DO NOTION

- Notion: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Scan type: Weekly, Week: `{ISO_YEAR}-W{ISO_WEEK}`, Status: New
- Dodaj pola: **Owner**, **Parent SOP**
- Per Type (SOP/Skill/n8n): dodaj pola z Schema 4A/4B/4C (patrz SKILL.md)
- n8n: **Error handling**, **Credentials**, **Dependencies**, **Test plan** — obowiązkowe

## PHASE 7: OUTPUT

Po zakończeniu:
1. Wydrukuj podsumowanie:
```
🔄 Knowledge Base Weekly — [Imię] — [Data] (W{X})

Przeskanowano (7 dni): Cowork: X | Gmail: X | Slack: X | Drive: X
Nowe odkrycia: Z (SOP: N | Skill: N | n8n: N | Pominięto: N)
📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```
2. Jeśli ≥1 odkrycie High priority → Slack post do #ai-feedback (C0AS00SNGQZ)
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=weekly, discoveries={N}, by_type={SOP:N, Skill:N, n8n:N}`

Jeśli 0 odkryć: cicha notyfikacja "Brak nowych odkryć — [DATA]"
```

---

## PROMPT MANUALNY (jeśli scheduled task nie zadziała):

```
Przeprowadź cotygodniowy skan knowledge-base — ostatnie 7 dni.

Imię: [Twoje imię]
Email: [Twój @off.org.pl]
Zakres: ostatnie 7 dni (Cowork + Gmail + Slack + Drive)
Mode: weekly
```

---

*Prompt: WEEKLY_COWORK.md v2.2 · knowledge-base · msm-glitch/knowledge-base*
