# Knowledge Base — Weekly Scan Chat

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** WEEKLY (co poniedziałek 10:00)

**Przeznaczenie:** Cotygodniowy skan w Claude Chat — ostatnie 7 dni.

**Setup:** Ustaw przypomnienie Google Calendar co poniedziałek 10:00. Chat nie ma scheduled task — manual.

---

## PROMPT WEEKLY — skopiuj i wklej w Claude Chat:

```
# WEEKLY KNOWLEDGE BASE SCAN v1.0 — Chat

Przeprowadź cotygodniowy skan Knowledge Base — ostatnie 7 dni.

Tryb: weekly

## PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 3 pytania. **Nie przechodzę dalej dopóki nie odpiszesz na wszystkie — nie zakładam żadnych wartości domyślnych.**

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

Zakres: ostatnie 7 dni (od [DATA_TYDZIEŃ_TEMU] do dziś)

## PHASE 1: SCAN — Chat (ostatnie 7 dni)

Używając "Search and reference chats" przejrzyj moje rozmowy z ostatnich 7 dni.

Dla każdej:
- Data, temat, cel, wynik
- Czy zadanie się powtarzało (vs poprzednie tygodnie)?
- Czy Claude nie poradził sobie → kandydat na automatyzację?

## PHASE 2-4: Gmail + Slack + Drive (ostatnie 7 dni)

- Gmail: `(decyzja OR SOP OR automatyzacja OR pipeline) newer_than:7d`
- Slack: ostatnie 7 dni w kanałach OFF (#general, #ai-feedback, #brand-team, #planer-dnia)
- Drive: pliki zmienione w ostatnich 7 dniach

## PHASE 5: KLASYFIKACJA

Tylko NOWE wzorce (sprawdź Notion KB czy już istnieje podobny wpis):

| Sygnał | Type |
|---|---|
| Powtarzalny proces ≥2× | SOP |
| Claude proszony wielokrotnie | Skill Backlog |
| Trigger + sekwencja narzędzi | n8n Automation |
| Jednorazowe | POMIŃ |

## PHASE 5.5: QUALITY GATES (sprawdź PRZED zapisem)

❌ **NIE ZAPISUJ jeśli:** meta-wpisy (knowledge-base, WSD), "stan istniejącego skilla" bez konkretu, jednorazowe momenty.

✅ **Title prefix:** `[NEW]` nowy / `[FIX]` poprawka / `[BUG]` bug
✅ **Source URL WYMAGANE** (link do oryginału lub `—`)
✅ **User = autor wzorca, NIE skanujący** (mapuj email na Notion Person ID z config/notion.yaml)
✅ **Date = data oryginalnego zdarzenia, NIE dziś**
✅ **1 wpis = 1 dominujący Type** (drugi aspekt w Summary)

---

## PHASE 6: ZAPIS DO NOTION

- DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Scan type: Weekly, Week: {ISO_YEAR}-W{ISO_WEEK}
- User: Notion Person ID (sprawdź config/notion.yaml → users)

## PHASE 7: OUTPUT

```
🔄 Knowledge Base Weekly — [Imię] — [Data]

Przeskanowano (7 dni): Chat: X | Gmail: X | Slack: X | Drive: X
Nowe odkrycia: Z (SOP: N | Skill: N | n8n: N | Pominięto: N)
📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

Jeśli ≥1 High priority → wyślij post do Slack #ai-feedback.
```

---

*Prompt: WEEKLY_CHAT.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
