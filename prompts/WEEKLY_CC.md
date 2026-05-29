# Knowledge Base — Weekly Scan Claude Code

**Wersja:** 2.2 | **Data:** 2026-05-19 | **Tryb:** WEEKLY (co poniedziałek 10:00)

**Przeznaczenie:** Wklej w sesji `claude` (CLI) co tydzień. Skanuje ostatnie 7 dni: Claude Code JSONL + Gmail + Slack + Drive.

**Wymagania:** Bootstrap wykonany wcześniej (`BOOTSTRAP_CC.md`).

---

## PROMPT WEEKLY — skopiuj i wklej w `claude`:

```
# WEEKLY KNOWLEDGE BASE SCAN v2.2 — Claude Code

Przeprowadź cotygodniowy skan Knowledge Base — ostatnie 7 dni.

Uruchom skill `knowledge-base` z repozytorium `msm-glitch/knowledge-base` w trybie `weekly`.

## PHASE 0: PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 2 pytania. **Nie przechodzę dalej dopóki nie odpiszesz — nie zakładam żadnych wartości domyślnych.**

Sprawdź `git config user.email` i `~/.claude/projects/*/memory/user_profile.md`, następnie wyświetl:

---

**[1/2] Twoje dane**
Wykryto: `[email z git config lub "nieznany"]`, imię: `[z memory lub "nieznane"]`
→ Potwierdź lub popraw: "Tak, to ja" / "Poprawiam: [imię, email]"

*Jeśli dane nieznane — wymagam jawnego wpisu przed kontynuowaniem.*

---

**[2/2] Potwierdzenie zakresu**
Skanem objęte: ostatnie 7 dni (Claude Code JSONL + Gmail + Slack + Drive).
Token strategy: Light (szybki weekly scan).
Czy jest coś co chcesz wyłączyć lub zawęzić?
→ Odpowiedz: OK lub podaj wyjątki

---

⛔ **Czekam na Twoje odpowiedzi [1], [2] — dopiero potem zaczynam skan.**

## PHASE 0.5: CROSS-CUTTING CONCERNS (Claude Code — Weekly)
**Gate konfiguracji (item #1) — STOP jeśli niepełna:**
Jeśli masz terminal/repo: `python3 scripts/kb_setup.py validate` (exit≠0 → pokaż błędy, `resolve`, STOP).
W Chat/Cowork sprawdź ręcznie, że `config/notion.yaml → users` i `config/sources.yaml → slack.channel_ids`
nie są puste — jeśli są, STOP i uzupełnij (inaczej zła atrybucja / martwe kanały).


**Budget cap:** ~200K tokenów. Weekly używa token strategy Light domyślnie.
Jeśli cap osiągnięty: zakończ bieżące źródło, zapisz drafty, zaraportuj "Budget cap reached".

**Rate limity MCP:** max 10 wywołań/min. Przy 429: backoff 2s→4s→8s (max 3 próby).

**BEZ SQLite / BEZ /runs/ na dysk.** (item #4: lekki stan w `state/` — ledger kandydatów + watermarki, scripts/kb_state.py) Drafty in-memory → Notion. Odrzucone → `Status = Rejected`.

Po odpowiedziach załaduj config:
- `config/notion.yaml`, `config/sources.yaml`
- Sesje JSONL: filtruj po `timestamp >= [TYDZIEŃ_TEMU]`
- Gmail/Slack/Drive: query_spec.weekly (lookback 7d)

## PHASE 1: SCAN — Claude Code (ostatnie 7 dni)

Glob `~/.claude/projects/**/*.jsonl` → filtruj po `timestamp >= [TYDZIEŃ_TEMU]`.
Sprawdź memory: `knowledge-base: last_run` → nie duplikuj odkryć z poprzedniego tygodnia.

## PHASE 2-4: Gmail + Slack + Drive (ostatnie 7 dni)

- Gmail: `config/sources.yaml → gmail.query_spec.weekly` (newer_than:7d)
- Slack: `config/sources.yaml → slack`, lookback 7d, użyj `channel_ids`
- Drive: pliki zmienione w ostatnich 7 dniach

## PHASE 5: KLASYFIKACJA — rozłączne drzewo 4-krokowe

Tylko NOWE wzorce (sprawdź Notion KB czy już istnieje podobny wpis).

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
[ ] Source URL = JSONL path + session ID / User = autor (git email → Notion ID)
[ ] Date = timestamp JSONL (nie dziś) / Title [NEW|FIX|BUG] / Summary z konkretem + "Next: ___"
[ ] Jeśli Type=Skill lub n8n: Parent SOP wskazany (slug lub "—")
[ ] Occurrence ≥ progu per typ
```

**✅ DOBRY:** `[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' [5× miss, JSONL path]. Parent SOP: —`
**❌ ZŁY:** meta-wpisy, Skill <3×, User=skanujący (gdy autor=inny), Date=dziś, n8n bez Error handling

---

## PHASE 5.5b: QUALITY GATES

❌ **NIE ZAPISUJ jeśli:** meta-wpisy (knowledge-base, WSD), "stan istniejącego skilla" bez konkretu, poniżej progu.

✅ **Title prefix:** `[NEW]` / `[FIX]` / `[BUG]`
✅ **Source URL WYMAGANE** (JSONL path + session ID, lub `—`)
✅ **User = autor wzorca, NIE skanujący**
✅ **Date = data ORYGINALNEGO zdarzenia**, nie dziś
✅ **Parent SOP** = slug dla Skill/n8n, lub `—`
✅ **n8n MUSI mieć** Error handling

---

## PHASE 6: ZAPIS DO NOTION

Scan type: **Weekly**, Week: `{ISO_YEAR}-W{AKTUALNY_TYDZIEŃ}`, Status: New.

**Pola wspólne:** Title, Type, Source, Date, Week, Summary, Priority, User (Notion Person ID), Source URL, Source examples, Occurrences, Sources count, Time saved, Implementation size, **Owner**, **Parent SOP**, ROI score.

**Pola per Type:** (identyczne jak BOOTSTRAP — patrz SKILL.md Schema 4A/4B/4C)

## PHASE 7: OUTPUT

```
🔄 Knowledge Base Weekly — [Imię] — [Data] (W{X})

Przeskanowano (ostatnie 7 dni):
  • Claude Code:  X sesji / Y nowych odkryć
  • Gmail:        X wątków / Y nowych odkryć
  • Slack:        X wiadomości / Y nowych odkryć
  • Drive:        X plików / Y nowych odkryć

🎯 Nowe wpisy: Z → Notion
  • SOP: N  • Skill: N  • n8n: N
  • Pominięto: N (poniżej progu / brak powtarzalności)

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

Jeśli 0 nowych odkryć: "Brak nowych odkryć w tym tygodniu. Następny scan: [DATA+7]"
Jeśli ≥1 odkrycie High priority → wyślij Slack post do #ai-feedback.

## PHASE 8: MEMORY UPDATE

```
knowledge-base: last_run={DATE}, mode=weekly, discoveries={N}, week={ISO_WEEK},
  by_type={SOP:N, Skill:N, n8n:N}, rejected={N}
```
```

---

*Prompt: WEEKLY_CC.md v2.2 · knowledge-base · msm-glitch/knowledge-base*
