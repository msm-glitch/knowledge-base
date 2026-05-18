# Knowledge Base — Weekly Scan Claude Code

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** WEEKLY (co poniedziałek 10:00)

**Przeznaczenie:** Wklej w sesji `claude` (CLI) co tydzień. Skanuje ostatnie 7 dni: Claude Code JSONL + Gmail + Slack + Drive.

**Wymagania:** Bootstrap wykonany wcześniej (`BOOTSTRAP_CC.md`).

---

## PROMPT WEEKLY — skopiuj i wklej w `claude`:

```
# WEEKLY KNOWLEDGE BASE SCAN v1.0 — Claude Code

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

*Skip list (legal/poufne) ładowana automatycznie z `config/sources.yaml`.*

Po odpowiedziach:
- Załaduj `config/notion.yaml` i `config/sources.yaml`
- Sesje JSONL: filtruj po `timestamp >= [TYDZIEŃ_TEMU]`
- Gmail/Slack/Drive: ostatnie 7 dni

## PHASE 1: SCAN — Claude Code (ostatnie 7 dni)

Glob `~/.claude/projects/**/*.jsonl` → filtruj po `timestamp >= [TYDZIEŃ_TEMU]`.

Dla każdej sesji:
- Wyciągnij: tytuł, datę, narzędzia, powtarzające się komendy
- Szukaj wzorców których nie było w poprzednich raportach
- Sprawdź memory: `knowledge-base: last_run` → nie duplikuj odkryć z poprzedniego tygodnia

## PHASE 2-4: Gmail + Slack + Drive (ostatnie 7 dni)

Identyczne jak w bootstrapie (PHASE 2-4), ale `since=-7d`.

## PHASE 5: KLASYFIKACJA (jak bootstrap)

Tylko NOWE wzorce nieobecne jeszcze w Notion Knowledge Base DB.

## PHASE 5.5: DUAL-PASS + QUALITY GATES

**Pass 1:** Zbierz drafty w pamięci. **Pass 2:** Checklist przed zapisem:
```
[ ] Skip: meta / "stan skilla" / jednorazowe → odrzuć
[ ] Cross-check z config/skills_catalog.yaml — match? → [FIX]; skip_meta? → POMIŃ
[ ] Source URL = JSONL path + session ID / User = autor (git email → Notion ID)
[ ] Date = timestamp JSONL (nie dziś) / Title [NEW|FIX|BUG] / Summary z konkretem
```

**✅ DOBRY:** `[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni'` + JSONL path
**❌ ZŁY:** meta-wpisy, User=skanujący (gdy autor=inny), Date=dziś

---

## PHASE 5.5b: QUALITY GATES (legacy)

❌ **NIE ZAPISUJ jeśli:** meta-wpisy (knowledge-base, WSD), "stan istniejącego skilla" bez konkretu, jednorazowe momenty.

✅ **Title prefix:** `[NEW]` nowy / `[FIX]` poprawka / `[BUG]` bug
✅ **Source URL WYMAGANE** (Slack permalink / Gmail link / Drive viewUrl / JSONL path)
✅ **User = autor wzorca, NIE skanujący** (mapuj email na Notion Person ID z config/notion.yaml)
✅ **Date = data oryginalnego zdarzenia (timestamp JSONL), NIE dziś**
✅ **1 wpis = 1 dominujący Type** (drugi aspekt w Summary)

---

## PHASE 6: ZAPIS DO NOTION

Identyczny jak bootstrap, ale:
- Scan type: **Weekly** (nie Bootstrap)
- Week: `{ISO_YEAR}-W{AKTUALNY_TYDZIEŃ}`

## PHASE 7: OUTPUT

```
🔄 Knowledge Base Weekly — [Imię] — [Data] (W{X})

Przeskanowano (ostatnie 7 dni):
  • Claude Code:  X sesji / Y nowych odkryć
  • Gmail:        X wątków / Y nowych odkryć
  • Slack:        X wiadomości / Y nowych odkryć
  • Drive:        X plików / Y nowych odkryć

🎯 Nowe wpisy: Z → Notion
  • SOP: N  • Skill: N  • n8n: N  • Pominięto: N

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

Jeśli 0 nowych odkryć: "Brak nowych odkryć w tym tygodniu. Następny scan: [DATA+7]"

Jeśli ≥1 odkrycie High priority → wyślij Slack post do #ai-feedback.

## PHASE 8: MEMORY UPDATE

```
knowledge-base: last_run={DATE}, mode=weekly, discoveries={N}, week={ISO_WEEK}
```
```

---

*Prompt: WEEKLY_CC.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
