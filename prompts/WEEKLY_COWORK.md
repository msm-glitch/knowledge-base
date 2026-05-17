# Knowledge Base — Weekly Scan Cowork

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** WEEKLY (co poniedziałek 10:00)

**Przeznaczenie:** Cotygodniowy skan w Cowork — ostatnie 7 dni. Zaplanuj jako scheduled task po bootstrapie.

---

## AKTYWACJA SCHEDULED TASK (jednorazowo po bootstrapie):

```
Zaplanuj cotygodniowe zadanie: Knowledge Base Weekly Scan.

Harmonogram: co poniedziałek o 10:00 (Europe/Warsaw).

---
# WEEKLY KNOWLEDGE BASE SCAN v1.0 — Cowork (Scheduled Task)

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

Po odpowiedziach załaduj konfigurację:
- Notion DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- User: mapuj email na Notion Person ID z `config/notion.yaml` → `users`
- Zakres: ostatnie 7 dni

## PHASE 1: SCAN — Cowork sessions (ostatnie 7 dni)

`list_sessions(since="-7d")` — tylko nowe sesje od ostatniego scanu.

Dla każdej sesji:
- Data, tytuł, skille, domena
- Czy zadanie powtarzało się w poprzednich tygodniach? (sprawdź Notion KB)
- Czy wynik był nieoptymalny? → potencjalna automatyzacja

## PHASE 2-4: Gmail + Slack + Drive (ostatnie 7 dni)

- Gmail: query `(decyzja OR pipeline OR SOP OR automatyzacja) newer_than:7d`
- Slack: wiadomości z ostatnich 7 dni w kanałach OFF
- Drive: pliki zmienione w ostatnich 7 dniach

## PHASE 5: KLASYFIKACJA

Tylko NOWE wzorce (nie ma ich jeszcze w Notion Knowledge Base):

| Sygnał | Type |
|---|---|
| Powtarzalny proces ≥2× | SOP |
| Claude proszony wielokrotnie o to samo | Skill Backlog |
| Trigger + sekwencja między narzędziami | n8n Automation |
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

- Notion: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Scan type: Weekly
- Week: `{ISO_YEAR}-W{ISO_WEEK}`

## PHASE 7: OUTPUT

Po zakończeniu:
1. Wydrukuj podsumowanie (format: emoji 🔄 + stats)
2. Jeśli ≥1 odkrycie High priority → Slack post do #ai-feedback (C0AS00SNGQZ)
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=weekly, discoveries={N}`

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

*Prompt: WEEKLY_COWORK.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
