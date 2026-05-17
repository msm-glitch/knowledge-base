# Knowledge Base — Bootstrap Cowork (lifetime scan)

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w sesji Claude Cowork jednorazowo — lifetime scan wszystkich sesji Cowork + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_COWORK.md`.

**Dla kogo:** Wszyscy członkowie zespołu OFF używający Cowork (11 osób).

**Czas:** ~30-45 min

---

## PROMPT BOOTSTRAP — skopiuj i wklej w Cowork:

```
# BOOTSTRAP KNOWLEDGE BASE v1.0 — LIFETIME SCAN (Cowork)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan.

## PHASE 0: PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 3 pytania. **Nie przechodzę dalej dopóki nie odpiszesz na wszystkie — nie zakładam żadnych wartości domyślnych.**

Wyświetl poniższy formularz i czekaj:

---

**[1/3] Twoje dane**
Podaj imię i email @off.org.pl.
→ Odpowiedz np.: "Maciek, maciek@off.org.pl"

*Nie zgaduję ani nie zakładam danych — wymagam jawnego wpisu.*

---

**[2/3] Zakres skanu**
Które sesje Cowork skanować?
→ Wybierz i odpisz literę:
(a) Wszystkie sesje (lifetime — od pierwszej do dziś)
(b) Tylko OFF-related (pomijam sesje prywatne/osobiste)
(c) Wybiórczo — dopisz zakres dat np. "od 2026-01-01"

---

**[3/3] Compliance — wymagane potwierdzenie**
Przeczytaj i potwierdź że rozumiesz:
✓ Raport nie cytuje danych osobowych (PESEL, NIP, imiona beneficjentów Mini Granty)
✓ Sesje legal/NDA → auto-skip (nie analizuję treści)
✓ Sesje z klauzulą anty-AI → STOP i informuję Cię
✓ Wątpliwe fragmenty → oznaczam "Needs review", nie zapisuję do Notion
→ Odpowiedz: POTWIERDZAM lub wskaż co chcesz zmienić

---

⛔ **Czekam na Twoje odpowiedzi [1], [2], [3] — dopiero potem zaczynam skan.**

## PHASE 1: SCAN — Cowork sessions

Pobierz pełną listę moich sesji Cowork:
- `list_sessions(all_time=true)` (bootstrap) lub analogicznie

Dla każdej sesji odnotuj:
- Data, tytuł, główne zadanie
- Skille użyte (jeśli widoczne w transcript)
- Domena (Mini Granty / Marketing / PM / Ops / etc.)
- Czy zadanie się powtarzało?
- Czy Claude nie mógł sobie poradzić sam → potencjalna automatyzacja?

⚠️ Auto-skip:
- Sesje legal (akta-kcs, UDIP, KRS) — privacy
- Sesje z PII beneficjentów → REDACT summary

## PHASE 2: SCAN — Gmail

Przez Gmail MCP, szukaj wątków z ostatnich 90 dni:
- Query: `(decyzja OR pipeline OR "powtarzalny" OR automatyzacja OR SOP) -label:SPAM`
- Dla każdego: temat, nadawca, czy sugeruje powtarzalny proces?
- SKIP: wątki z PESEL, NIP, danymi osobowymi → REDACT

## PHASE 3: SCAN — Slack

Przez Slack MCP, kanały OFF z ostatnich 90 dni:
- Kanały: #general, #ai-feedback, #planer-dnia, #brand-team, #mini-granty, #full-team
- Szukaj: pytania powtarzające się, prośby o pomoc, frustrations, decyzje
- SKIP: hasła, tokeny, dane poufne

## PHASE 4: SCAN — Google Drive

Przez Drive MCP, pliki OFF zmienione w ostatnich 90 dniach:
- Folder WSD: `1U10_VXe_qxoYOlrSyIpgQKXOUy-og1D-`
- Odnotuj: tytuły, typy dokumentów, czy sugerują powtarzalny proces

## PHASE 5: KLASYFIKACJA

Dla każdego wykrytego wzorca/odkrycia:

**Czy nadaje się na SOP / Skill / n8n?**

| Sygnał | Klasyfikacja |
|---|---|
| Ten sam proces ≥2× (różne sesje/maile/Slack) | SOP |
| Claude proszony o to samo wielokrotnie | Skill Backlog |
| Jasny trigger + sekwencja między narzędziami | n8n Automation |
| Jednorazowe, brak powtarzalności | POMIŃ |

Priority:
- High: ≥3 wystąpień LUB blokuje pracę LUB oszczędza >30 min
- Medium: 2 wystąpienia LUB przydatne dla ≥3 osób
- Low: 1 wystąpienie, warto zapamiętać

## PHASE 5.5: QUALITY GATES (sprawdź PRZED zapisem)

❌ **NIE ZAPISUJ jeśli:**
- Wpis dotyczy `knowledge-base`, `weekly-discovery`, `team-knowledge-base`, `WSD` (meta)
- "Stan istniejącego skilla" bez konkretnego problemu
- Jednorazowy moment bez powtarzalności

✅ **Title prefix obowiązkowy:**
- `[NEW]` nowy / `[FIX]` poprawka istniejącego / `[BUG]` blokujący błąd

✅ **Source URL WYMAGANE** (Slack permalink / Gmail link / Drive viewUrl / Cowork session ID). Brak → wpisz `—`.

✅ **User = autor wzorca, NIE skanujący.** Mapuj email na Notion Person ID z config/notion.yaml. ≥3 osoby → "(team-wide)" w Title.

✅ **Date = data ORYGINALNEGO zdarzenia**, nie dziś. Wielokrotny → najnowsze wystąpienie.

✅ **1 wpis = 1 dominujący Type.** Drugi aspekt w Summary.

---

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ) stwórz wpis:
- Notion Knowledge Base DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Title: `{YYYY-MM-DD} · {Imię} · {Krótki opis}`
- Type: SOP | Skill Backlog | n8n Automation
- Source: [skąd pochodzi]
- Date: dziś, Week: `{ISO_YEAR}-W{ISO_WEEK}`
- Summary: 2-3 zdania (co to + dlaczego wdrożyć)
- Priority: High/Medium/Low
- Status: New
- Scan type: Bootstrap
- User: Notion Person ID → sprawdź `config/notion.yaml` → `users`
  Fallback: `User name (fallback)` = imię tekstowe (dla Krzysztofa i Roksany)

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
  • SOP:            N  • Skill Backlog: N  • n8n: N  • Pominięto: N

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
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap, discoveries={N}`
```

---

*Prompt: BOOTSTRAP_COWORK.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
