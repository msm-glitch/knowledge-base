# Knowledge Base — Bootstrap Chat (lifetime scan)

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w Claude Chat (claude.ai) jednorazowo — lifetime scan historii rozmów + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_CHAT.md`.

**Wymagania:**
- Konto claude.ai (Pro/Team)
- ⚠️ **"Search and reference chats" OBOWIĄZKOWO włączone** (Settings → Privacy)
- Dostęp do Gmail, Slack #ai-feedback, Google Drive OFF

**Czas:** ~20-30 min

---

## PROMPT BOOTSTRAP — skopiuj i wklej w Claude Chat:

```
# BOOTSTRAP KNOWLEDGE BASE v1.0 — LIFETIME SCAN (Chat)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan mojej historii rozmów z Claude.

## PRE-FLIGHT — STOP, CZEKAM NA TWOJE ODPOWIEDZI

Przed skanem zadaję Ci 4 pytania. **Nie przechodzę dalej dopóki nie odpiszesz na wszystkie — nie zakładam żadnych wartości domyślnych.**

Wyświetl poniższy formularz i czekaj:

---

**[1/4] Search & reference chats**
Czy masz włączone "Search and reference chats" w Settings → Privacy?
→ Odpowiedz: TAK / NIE

*Jeśli NIE: przerwij i napisz "Włącz 'Search and reference chats' w claude.ai → Settings → Privacy, potem wróć z tym promptem."*

---

**[2/4] Twoje dane**
Podaj imię i email @off.org.pl.
→ Odpowiedz np.: "Maciek, maciek@off.org.pl"

*Nie zgaduję ani nie zakładam danych — wymagam jawnego wpisu.*

---

**[3/4] Zakres skanu**
Które rozmowy skanować?
→ Wybierz i odpisz literę:
(a) Wszystkie rozmowy (lifetime — od pierwszej do dziś)
(b) Tylko OFF-related (pomijam rozmowy prywatne/osobiste)
(c) Wybiórczo — dopisz zakres dat lub tematy np. "od 2026-01-01" / "tylko marketing"

---

**[4/4] Compliance — wymagane potwierdzenie**
Przeczytaj i potwierdź że rozumiesz:
✓ Raport nie cytuje danych osobowych (PESEL, NIP, imiona beneficjentów Mini Granty)
✓ Rozmowy legal/NDA → auto-skip (nie analizuję treści)
✓ Rozmowy z klauzulą anty-AI → STOP i informuję Cię
✓ Wątpliwe fragmenty → oznaczam "Needs review", nie zapisuję do Notion
→ Odpowiedz: POTWIERDZAM lub wskaż co chcesz zmienić

---

⛔ **Czekam na Twoje odpowiedzi [1], [2], [3], [4] — dopiero potem zaczynam skan.**

## PHASE 1: SCAN — Claude Chat history

Użyj "Search and reference chats" żeby przeskanować pełną historię moich rozmów.

Dla każdej rozmowy odnotuj:
- Data, temat/tytuł
- Cel zadania i wynik
- Domena: PM / Mini Granty / Marketing / Ops / Legal / Inne
- Czy zawierała PII? (Mini Granty, dane osobowe) → REDACT summary
- Czy zadanie się powtarzało w innych rozmowach?
- Skille/triggery użyte (jeśli widoczne)
- Czy Claude nie poradził sobie → potencjalna automatyzacja?

⚠️ Auto-skip:
- Rozmowy z tagiem legal/private (akta-kcs, UDIP, KRS)
- Rozmowy z NDA (PwC, Allegro, Forbes itp.) → FLAG w raporcie, nie cytuj
- Rozmowy osobiste (poza OFF) → skip lub user confirm

## PHASE 2: SCAN — Gmail

Przez Gmail MCP, szukaj wątków z ostatnich 90 dni:
- Query: `(decyzja OR pipeline OR "powtarzalny" OR automatyzacja) -label:SPAM`
- Dla każdego: temat, nadawca, czy sugeruje powtarzalny proces?
- SKIP: wątki z PESEL, NIP, danymi beneficjentów → REDACT

## PHASE 3: SCAN — Slack

Przez Slack MCP, kanały OFF z ostatnich 90 dni:
- #general, #ai-feedback, #planer-dnia, #brand-team, #mini-granty
- Szukaj: pytania które się powtarzają, frustrations, decyzje
- SKIP: hasła, tokeny

## PHASE 4: SCAN — Google Drive

Przez Drive MCP, pliki OFF zmienione w ostatnich 90 dniach:
- Odnotuj instrukcje, szablony, procedury → SOP candidates

## PHASE 5: KLASYFIKACJA

**Czy nadaje się na SOP / Skill / n8n?**

| Sygnał | Klasyfikacja |
|---|---|
| Ten sam proces ≥2× (różne rozmowy/maile/Slack) | SOP |
| Claude proszony o to samo zadanie wielokrotnie | Skill Backlog |
| Jasny trigger + sekwencja między narzędziami (Gmail→Slack→Drive) | n8n Automation |
| Jednorazowe, brak powtarzalności | POMIŃ |

Priority:
- High: ≥3 wystąpień LUB blokuje pracę
- Medium: 2 wystąpienia LUB przydatne dla ≥3 osób
- Low: 1 wystąpienie, warto zapamiętać

## PHASE 5.5: DUAL-PASS + QUALITY GATES

**Pass 1 (draft):** Zbierz wszystkie kandydatów w pamięci. NIE zapisuj jeszcze do Notion.

**Pass 2 (weryfikacja):** Dla każdego draftu przejdź checklist:
```
[ ] Skip rules: nie meta, nie "stan skilla bez konkretu", nie jednorazowe
[ ] Cross-check z config/skills_catalog.yaml:
    - fuzzy match nazwy → jeśli skill już istnieje → wymuś [FIX]
    - jeśli na skip_meta → POMIŃ wpis
[ ] Source URL wypełniony (lub jawnie "—")
[ ] User = autor wzorca, nie skanujący (mapuj email→Notion Person ID)
[ ] Date = data oryginalnego zdarzenia, nie dziś
[ ] Title z prefiksem [NEW]/[FIX]/[BUG]
[ ] Summary: liczba wystąpień + dowód (link) + konkret co naprawić
```

Jeśli ≥1 fail → popraw lub odrzuć. Tylko ✅ → zapis.

### Few-shot — naucz się z prawdziwych przypadków:

**✅ DOBRY [FIX]:**
```
[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' do triggerów
Priority: High (5× miss = intra-source intensity)
Source: [Claude Chat] | URL: https://claude.ai/chat/abc
Date: 2026-05-11 (nie dziś!)
Summary: Skill off-brand-voice v3.3 nie odpala dla 'podopieczni'/'stypendyści'.
  5× ręczne przepisanie 5-11.05. Fix: dodać do triggerKeywords + description.
```

**✅ DOBRY [NEW] n8n:**
```
[NEW] 2026-05-15 · Maciek · Masowy outreach do MR — szablon ×10+
Priority: High (10+ wystąpień + cross-source 2)
Source: [Gmail, Claude Chat] | URL: https://mail.google.com/.../thread-xyz
Date: 2026-05-15
Summary: 10+ maili do Młodzieżowych Rad z identycznym szablonem, tylko nazwa rady różna.
  Cross-source: Gmail wysyłka + Chat draft. n8n: lista → personalizacja → auto-send.
  Oszczędność ~2h/kampanię.
```

**❌ ZŁE — odrzucaj/poprawiaj:**
- `Weekly Knowledge Scan — automatyzacja` → META, POMIŃ
- `Ewidencja godzinowa — wymaga doprecyzowania` → za ogólne + skill już istnieje → [FIX]
- `User: Maciek` dla Slack-post Michała → wrong attribution, User = Michał
- `Date: 2026-05-17` (dzień skanu) → powinno być data oryginalnego zdarzenia

---

## PHASE 5.5b: QUALITY GATES (legacy — zachowane dla pełności)

❌ **NIE ZAPISUJ jeśli:**
- Wpis dotyczy `knowledge-base`, `weekly-discovery`, `team-knowledge-base`, `WSD` (meta — to ten sam skill)
- "Stan istniejącego skilla" bez konkretnego problemu/poprawki
- Jednorazowy moment bez powtarzalności

✅ **Title prefix obowiązkowy:**
- `[NEW]` — nowy SOP / nowy skill / nowa automatyzacja
- `[FIX]` — poprawka istniejącego skilla (trigger conflict, missing keywords)
- `[BUG]` — bug w istniejącym narzędziu

Przykład: `[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' do triggerów`

✅ **Source URL — WYMAGANE** (jeśli faktycznie brak → wpisz `—`, nie zostawiaj pustego):
- Slack: permalink wiadomości
- Gmail: link do wątku
- Drive: viewUrl
- Chat: URL konwersacji jeśli dostępny

✅ **User attribution** — kto JEST autorem wzorca, nie skanujący:
- Wzorzec własny → User = ja
- Slack post Michała o problemie → User = Michał (mapuj email na Notion Person ID z config/notion.yaml)
- ≥3 osoby → "(team-wide)" w Title

✅ **Date — data ORYGINALNEGO zdarzenia** (NIE dziś):
- Slack: data wiadomości / Gmail: data wątku / Chat: data rozmowy
- Wzorzec wielokrotny → najnowsze wystąpienie

✅ **Multi-type** — 1 wpis = 1 dominujący Type. Drugi aspekt opisz w Summary.

---

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ) stwórz wpis:
- Notion Knowledge Base DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Title: `{YYYY-MM-DD} · {Imię} · {Krótki opis}`
- Type: SOP | Skill Backlog | n8n Automation
- Source: [lista źródeł]
- Date: dziś, Week: `{ISO_YEAR}-W{ISO_WEEK}`
- Summary: 2-3 zdania
- Priority: High/Medium/Low, Status: New, Scan type: Bootstrap
- User: Notion Person ID z `config/notion.yaml`

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
  • SOP: N  • Skill: N  • n8n: N  • Pominięto: N

🏆 Top 3: 1. [High]... 2. [High]... 3. [Medium]...

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

## PHASE 8: POST-BOOTSTRAP

1. Wyślij post do Slack #ai-feedback (C0AS00SNGQZ)
2. Przypomnij: ustaw przypomnienie Google Calendar co poniedziałek 10:00 z `WEEKLY_CHAT.md`
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap`
```

---

*Prompt: BOOTSTRAP_CHAT.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
