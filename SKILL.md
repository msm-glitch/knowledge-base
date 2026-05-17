# knowledge-base

Skill do zbierania wiedzy operacyjnej zespołu OFF z wielu źródeł (Gmail, Slack, Google Drive, sesje Claude) i klasyfikowania odkryć jako: SOP, Skill Backlog lub n8n Automation — bezpośrednio do Notion.

## Tryby

| Tryb | Kiedy | Co skanuje | Jak często |
|---|---|---|---|
| `bootstrap` | Jednorazowo (pierwsze uruchomienie) | Cały lifetime każdego źródła | 1× |
| `weekly` | Co poniedziałek 10:00 | Ostatnie 7 dni | Co tydzień |

---

## Krok 0: Pre-flight (zawsze)

**0.1 — Wykryj usera:**
- Claude Code: `git config user.email` LUB `~/.claude/projects/*/memory/user_profile.md`
- Cowork/Chat: spytaj użytkownika o imię i email
- Mapuj na Notion Person ID z `config/notion.yaml` → `users`
- Jeśli email niezidentyfikowany: użyj `User name (fallback)` (pole tekstowe)

**0.2 — Załaduj konfigurację:**
- Odczytaj `config/notion.yaml` — Notion DB IDs, user map, Slack channel
- Odczytaj `config/sources.yaml` — które źródła aktywne, skip patterns

**0.3 — Tryb i zakres:**
```
TRYB: bootstrap / weekly
ZAKRES: ostatnie N dni (7 dla weekly, all-time dla bootstrap)
UŻYTKOWNIK: [imię], [email]
ŹRÓDŁA: [aktywne z config]

Kontynuować? (a) Tak  (b) Zmień zakres  (c) Pomiń źródło
```

---

## Krok 1: Zbieranie danych

### 1A — Claude Code (JSONL)

**Lokalizacja sesji:**
- Windows: `C:\Users\<user>\.claude\projects\`
- macOS/Linux: `~/.claude/projects/`

**Format:** pliki `*.jsonl`, schema:
```json
{"type":"user","message":{"content":"..."},"cwd":"...","timestamp":"..."}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"...","input":{}}]}}
{"type":"ai-title","aiTitle":"...","sessionId":"..."}
```

**Wykrycie środowiska (zawsze przed skanem):**
```bash
JSONL_COUNT=$(find ~/.claude/projects -name "*.jsonl" 2>/dev/null | wc -l)
```
- `JSONL_COUNT > 1` → środowisko **lokalne** → kontynuuj pełny skan
- `JSONL_COUNT ≤ 1` → środowisko **zdalne (cloud/web container)** → wyświetl ostrzeżenie:

> ⚠️ Wykryto środowisko zdalne. Pełna historia sesji CC jest na maszynie lokalnej.
> Opcje: (a) Pomiń CC JSONL, kontynuuj Gmail/Slack/Drive  (b) Zatrzymaj i uruchom lokalnie w CLI  (c) Skanuj tylko bieżącą sesję (próbka)
> ⛔ Czekaj na wybór przed kontynuowaniem.

**Etapy (tylko jeśli lokalne lub opcja c):**
1. Glob `**/*.jsonl` → lista plików
2. Klasyfikuj `cwd` per `config/sources.yaml` → `skip_patterns` (AUTO-SKIP) lub INCLUDE
3. Pokaż listę do override przed startem
4. Wyciągnij z każdej sesji: tytuł, datę, narzędzia, powtarzające się komendy

**Token strategy:**
```
(A) Light  — tylko metadane + tytuły (~150K)
(B) Medium — + sampling 30 linii na sesję (~600K) [domyślne]
(C) Deep   — full scan (~2M+)
```

### 1B — Claude Chat (claude.ai)

Wymagane: **"Search and reference chats"** włączone (Settings → Privacy).

Przeszukaj historię rozmów. Dla każdej:
- Temat / cel
- Narzędzia/skille użyte
- Czy zadanie się powtarzało?
- Czy efekt był nieoptymalny (mógłby być zautomatyzowany)?

### 1C — Claude Cowork

```
list_sessions(all_time=true)   # bootstrap
list_sessions(since="-7d")     # weekly
```

Dla każdej sesji: tytuł, data, skille, domena, wynik.

### 1D — Gmail

Przez Gmail MCP (`mcp__ab46da28`):
- Szukaj wątków z keywords: `decyzja`, `pipeline`, `SOP`, `powtarzalny`, `automatyzacja`
- Filtruj: nie SPAM, nie TRASH
- Odnotuj: nadawca/odbiorca, temat, czy sugeruje powtarzalny proces

**Compliance:** nie cytuj PII (PESEL, NIP, dane osobowe z grantów).

### 1E — Slack

Przez Slack MCP (`mcp__8c5de80e`):
- Kanały z `config/sources.yaml` → `slack.channels`
- Szukaj: decyzje, procesy, prośby o pomoc które się powtarzają
- Pomiń: wiadomości z hasłami, danymi poufnymi

### 1F — Google Drive

Przez Drive MCP (`mcp__7a8eafc1`):
- Foldery z `config/sources.yaml` → `google_drive.folders`
- Nowe/zmienione pliki w zakresie dat
- Odnotuj: tytuł, typ dokumentu, czy to procedura/instrukcja/szablon

---

## Krok 2: Filtr compliance

Przed każdym wpisem do Notion — LLM pass:

```
Sprawdź czy wpis zawiera:
- Dane osobowe (PESEL, NIP, imiona beneficjentów Mini Granty) → REDACT
- Sekrety (hasła, tokeny, API keys) → REDACT + flag Needs review
- Treści NDA (partner pod NDA) → FLAG, nie zapisuj summary
- Anti-AI clause → STOP + poinformuj usera
```

Wątpliwe wpisy → `Needs review = true` (to pole jest w Sessions DB, w Knowledge Base DB użyj `Status = New` z notatką).

---

## Krok 3: Klasyfikacja odkryć — DUAL-PASS

### Pass 1 — DRAFT (bez zapisu)

Zbierz wszystkie kandydatów na wpisy w pamięci (lista draftów). NIE zapisuj jeszcze do Notion.

Dla każdego draftu wypełnij wszystkie pola według Krok 3.5 (Quality gates).

### Pass 2 — WERYFIKACJA (przed zapisem)

Dla każdego draftu sprawdź:

```
[ ] 1. Czy wpis przeszedł SKIP RULES? (meta, "stan istniejącego skilla", jednorazowe)
       → sprawdź też skip_meta_patterns w skills_catalog.yaml (regex/contains)
[ ] 2. Czy proponowana nazwa skilla/SOPa istnieje już w config/skills_catalog.yaml?
       → fuzzy match na: base_off + extended_uao + extended_extra
       → JEŚLI MATCH: wymuś [FIX] zamiast [NEW]
       → JEŚLI w skip_meta: POMIŃ wpis całkowicie
[ ] 3. Czy Source URL jest wypełniony (lub jawnie "—")?
       → Slack: MUSI być permalink (slack_get_permalink), NIE app_redirect
[ ] 4. Czy User to oryginalny autor wzorca (nie skanujący)?
[ ] 5. Czy Date to data zdarzenia (nie dziś)?
[ ] 6. Czy Title ma prefix [NEW]/[FIX]/[BUG]?
[ ] 7. Czy Summary daje konkret z liczbą wystąpień + dowodem + co naprawić?
[ ] 8. Czy Summary kończy się zdaniem "Next: ___"? (1 actionable krok)
[ ] 9. WSD-relay check: source=Slack #ai-feedback (C0AS00SNGQZ) i tekst ma "WSD"?
       → ustaw Scan_type=WSD-relay, obniż Priority o 1 poziom
[ ] 10. Trigger phrases (tylko dla Skill Backlog [FIX]/[NEW]):
       → wyciągnij konkretne frazy z source które miss/trigger
       → dopisz na końcu Summary: "Triggers obs.: 'fraza1', 'fraza2'..."
```

Jeśli ≥1 check fail → popraw draft LUB odrzuć do `rejected_drafts.log`.
Dopiero po wszystkich ✅ → przejdź do Pass 3.

### Pass 3 — ANTI-DUPLICATE QUERY (przed zapisem do Notion)

Dla każdego draftu, **przed `notion-create-pages`**, query Notion KB DB:

```
query: filter by (Type == draft.Type) AND (Status != "Rejected")
       AND (Date in [draft.Date - 14d, draft.Date + 14d])
```

Dla każdego wyniku oblicz **similarity score** względem draftu:
- Title token overlap (Jaccard) — waga 0.4
- Skill name match (extract z Title po prefix [NEW]/[FIX]/[BUG]) — waga 0.4
- User match — waga 0.2

```
similarity = 0.4 * jaccard(titles) + 0.4 * skill_name_match + 0.2 * user_match
```

| similarity | Akcja |
|---|---|
| ≥ 0.75 | **MERGE** — NIE twórz nowego. Update istniejącego: `occurrences += 1`, append do Summary "Także: {Source URL nowego}", refresh Date jeśli nowsze |
| 0.55-0.74 | **FLAG** — pokaż userowi diff "Czy to duplikat #X?" i czekaj na decyzję |
| < 0.55 | **CREATE** — nowy wpis OK |

Przykład merge (z bootstrapu Macieja):
- Draft: `[FIX] 2026-05-17 · Maciej · off-brand-voice — dodaj 'podopieczni'`
- Istnieje: `[FIX] 2026-05-11 · Maciej · volunteer-message — dodaj podopieczni...`
- similarity = 0.4·0.6 (titles) + 0.4·0.8 (oba dotyczą "podopieczni" w skillu od brand voice) + 0.2·1.0 (Maciej) = **0.76** → MERGE

### Pass 4 — PRIORITY NORMALIZATION (anty-inflacja)

Po wszystkich Pass 3 zapisach, oblicz rozkład priorytetów dla tego skanu:

```
target_distribution: High=20%, Medium=50%, Low=30%
```

Jeśli faktyczny High% > 35%:
1. Posortuj High'e malejąco po `score = (occurrences × sources × time_saved_min)`
2. Top 20% zostają High, reszta → Medium (update via `notion-update-page`)

Rationale: jeśli wszystko jest "High", priorytet traci znaczenie. Zespół musi wiedzieć co BIERZE NAJPIERW.

### Few-shot examples — UCZ SIĘ Z PRAWDZIWYCH PRZYPADKÓW

#### ✅ DOBRE wpisy (zachowaj ten format):

**Przykład 1 — [FIX] z konkretnymi dowodami:**
```
Title: [FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' do triggerów
Type: Skill Backlog
Priority: High (5× miss w jednym źródle = intra-source intensity High)
Source: [Claude Chat]
Source URL: https://claude.ai/chat/abc-2026-05-11
Date: 2026-05-11  ← data NAJNOWSZEGO miss-a
User: Michał (Notion Person ID)
Summary: Skill off-brand-voice v3.3 nie odpala dla 'podopieczni'/'stypendyści'/
  'laureaci' — 5× ręczne przepisanie w Chat (5-11.05). Trigger w SKILL.md zawiera
  tylko 'wolontariusze'. Fix: dodać 3 słowa do triggerKeywords + description.
```

**Przykład 2 — [NEW] n8n z cross-source:**
```
Title: [NEW] 2026-05-15 · Maciek · Masowy outreach do MR — ten sam szablon ×10+
Type: n8n Automation
Priority: High (10+ wystąpień + cross-source 2)
Source: [Gmail, Claude Chat]
Source URL: https://mail.google.com/mail/u/0/#sent/thread-id-xyz
Date: 2026-05-15
User: Maciek
Summary: 10+ maili do MR (Młodzieżowe Rady Miast) z identycznym szablonem promocji
  PM OFF, tylko nazwa rady różna. Maciek pisał ręcznie + Claude pomagał stylem
  (cross-source: Gmail wysyłka + Chat draft). Oszczędność ~2h/kampanię.
  n8n workflow: lista MR → personalizacja nazwy → auto-send.
```

#### ❌ ZŁE wpisy (poprawiaj/odrzucaj):

**Anti-przykład 1 — meta:**
```
Title: Weekly Knowledge Scan — pełna automatyzacja
  ↑ META! To jest TEN skill który właśnie się uruchomił. POMIŃ.
```

**Anti-przykład 2 — brak konkretu:**
```
Title: 2026-05-17 · Maciek · Ewidencja godzinowa — wymaga doprecyzowania
Summary: "Skill działa ale wymaga doprecyzowania"
  ↑ Za ogólne. Brak liczby wystąpień, brak konkretu co naprawić.
  ↑ Cross-check: skill 'ewidencja-godzinowa-miesieczna' istnieje
    → powinno być [FIX], nie [NEW]
```

**Anti-przykład 3 — błędna atrybucja:**
```
Title: 2026-05-17 · Maciek · CRM-Rejs sync — KRYTYCZNY (WSD)
User: Maciek
  ↑ Wzorzec dotyczy Michała (Michał zgłosił na Slacku, Maciek tylko widział)
  ↑ User powinien być Michał
```

**Anti-przykład 4 — data dziś zamiast oryginału:**
```
Date: 2026-05-17 (dzień skanowania)
  ↑ Powinno być data ostatniego wystąpienia wzorca (np. 2026-05-11)
```

---

### Kryteria (z diagramu przepływu):

Dla każdego wzorca/odkrycia odpowiedz na pytanie:

**Czy nadaje się na SOP / Skill / n8n?**

| Sygnał | Klasyfikacja |
|---|---|
| Ten sam proces wykonywany ≥2× przez różnych ludzi lub w różnych sesjach | **SOP** |
| Claude jest proszony o to samo zadanie wielokrotnie (np. "napisz email w stylu OFF") | **Skill Backlog** |
| Jest jasny trigger + sekwencja akcji między narzędziami (Gmail → Slack → Drive) | **n8n Automation** |
| Jednorazowe zadanie, brak powtarzalności, brak wartości uogólnienia | **POMIŃ** — nic nie zapisuj |

### Priorytety:

| Priority | Kiedy |
|---|---|
| High | Powtarza się ≥3× LUB blokuje pracę LUB zajmuje >30 min |
| Medium | Powtarza się 2× LUB byłoby przydatne dla ≥3 osób |
| Low | Jednorazowe ale warto zapamiętać |

---

## Krok 3.5: Quality gates (KRYTYCZNE — sprawdź PRZED zapisem)

### ❌ NIE ZAPISUJ (skip rules):

1. **Meta-wpisy** — wpis dotyczy samego procesu skanowania/budowy KB:
   - `knowledge-base`, `weekly-discovery`, `team-knowledge-base`, `WSD`, `Weekly Skill Discovery`
   - Wpisy "buduję skill który będzie skanował sesje" → pomiń

2. **"Stan istniejącego skilla"** bez konkretnego problemu:
   - "Skill X działa, użytkownicy go testują" → POMIŃ
   - "Skill X wymaga poprawki Y bo trigger nie działa" → ZAPISZ jako [FIX]

3. **Jednorazowe pytania** — mniej niż 2× w jakimkolwiek źródle i brak wartości uogólnienia

### ✅ Title prefix — rozróżnij typ działania:

| Prefix | Kiedy | Przykład |
|---|---|---|
| `[NEW]` | Nowy SOP / nowy skill / nowa automatyzacja | `[NEW] Onboarding AI OFF — SOP` |
| `[FIX]` | Poprawka istniejącego skilla (trigger conflict, missing keywords) | `[FIX] off-brand-voice — dodaj 'podopieczni' do triggerów` |
| `[BUG]` | Bug w istniejącym narzędziu który blokuje pracę | `[BUG] CRM-Rejs sync — wpisuje do złej bazy` |

### ✅ Source URL (WYMAGANE):

Każdy wpis MUSI mieć link do oryginalnego źródła. Bez tego nie da się zweryfikować.

| Źródło | Co wpisać |
|---|---|
| Slack | Permalink wiadomości (`slack_get_permalink` lub URL `https://*.slack.com/archives/...`) |
| Gmail | Link do wątku (`https://mail.google.com/mail/u/0/#inbox/...`) |
| Drive | `viewUrl` pliku |
| Claude Chat | URL konwersacji jeśli dostępny |
| Claude Code | Ścieżka JSONL + session ID (`~/.claude/projects/[cwd]/[session].jsonl`) |
| Brak | Wpisz jawnie `—` (NIE zostawiaj pustego pola) |

Wpis wielokrotny → URL najsilniejszego/najnowszego wystąpienia (resztę wymień w Summary).

### ✅ User attribution (atrybucja):

User w Notion = **osoba u której wzorzec się pojawia**, NIE skanujący.

| Sytuacja | Co zrobić |
|---|---|
| Wzorzec własny (skanujący wysłał maila, miał sesję) | User = skanujący |
| Widziany w Slack post Michała o problemie | User = Michał |
| Wzorzec u ≥3 różnych osób | Multi-select User + `(team-wide)` w Title |
| Z WSD bez konkretnej osoby | User name (fallback) = "WSD report" |

**Mapowanie email → Notion Person ID:**
- Załaduj `config/notion.yaml` → `users`
- Email `wfs@off.org.pl` → Notion ID `206d872b-594c-81d6-8a6f-0002a2592991`
- Jeśli brak mapowania → tylko `User name (fallback) = "Imię"`

### ✅ Date — ORYGINALNE zdarzenie:

NIE wpisuj dziś. Wpisz datę ostatniego wystąpienia wzorca:
- Slack: data wiadomości
- Gmail: data wątku
- Drive: `lastModified`
- Claude session: `timestamp` ostatniej tury
- Wzorzec wielokrotny → data NAJNOWSZEGO wystąpienia

### ✅ Multi-type (1 wpis = 1 Type):

Jeśli odkrycie pasuje do 2 typów (np. SOP + n8n):
- Wybierz **dominujący** Type (główne działanie wymagane)
- W Summary wymień drugi aspekt: "Type: n8n Automation, ale wymaga też SOP-a opisującego kiedy uruchamiać"

---

## Krok 4: Zapis do Notion Knowledge Base

### Pola wpisu:

```
Title:    "{YYYY-MM-DD} · {Imię} · [PREFIX] {Krótki opis odkrycia}"
Type:     SOP | Skill Backlog | n8n Automation
Source:   [Claude Code | Claude Chat | Claude Cowork | Gmail | Slack | Google Drive]
Date:     data ostatniego wystąpienia (YYYY-MM-DD)
Week:     ISO week (np. "2026-W21")
Summary:  Format STRICT:
  Zdanie 1: Co — wzorzec + liczba × + zakres dat
  Zdanie 2: Dowód — gdzie/kto (Source URLs)
  Zdanie 3: Triggers obs.: 'fraza1', 'fraza2' (TYLKO dla Skill Backlog)
  Zdanie 4: Next: {1 actionable krok dla ownera}
Priority: High | Medium | Low (po Pass 4 normalizacji)
Status:   New | Triaged | In Progress | Implemented | Validated | Rejected
User:     Notion Person ID (z config/notion.yaml)
User name (fallback): imię tekstowo jeśli brak Notion ID
Source URL: PERMALINK do oryginału (Slack: slack_get_permalink, nie app_redirect)
Scan type: Bootstrap | Weekly | WSD-relay
Occurrences: liczba wystąpień wzorca (int, default 1)
Sources count: liczba unikalnych źródeł (int, default 1)
Time saved (min/week): szacunek oszczędności po wdrożeniu (int)
Implementation size: S (<2h) | M (2-8h) | L (>8h)
Related skill: nazwa skilla z skills_catalog (dla [FIX]/[BUG]) lub "—"
Owner suggestion: kto powinien obsłużyć (autor / skill-creator / n8n-admin / Wojciech)
ROI score: occurrences × sources × time_saved_min / impl_size_factor  (auto)
```

**Implementation size factor:** S=1, M=4, L=12 (do obliczenia ROI).
**ROI score** jest kluczem do sortowania backlogu — pokazuje co dawać do realizacji NAJPIERW.

**Jak szacować time_saved:**
- Z wpisów: jeśli source mówi "2h/kampanię, 4× w miesiącu" → 2h×4/4 tyg = 120 min/tydzień
- Jeśli brak danych: konserwatywnie 15 min/tydzień (Low), 60 (Medium), 180 (High)

**Jak ustawić Owner suggestion:**
| Typ wpisu | Owner |
|---|---|
| [FIX] istniejącego skilla | skill-creator (Wojciech) |
| [BUG] blokujący | autor wzorca + Wojciech |
| [NEW] Skill Backlog | skill-creator (Wojciech) |
| [NEW] n8n Automation | n8n-admin (Maciek) |
| [NEW] SOP | autor wzorca |
| Team-wide (≥3 osoby) | Wojciech + Maciek |

### Wywołanie MCP:

Użyj `notion-create-pages` z data source ID:
```
collection://[knowledge_base_id z config/notion.yaml]
```

Sprawdź `config/notion.yaml` → `databases.knowledge_base` — jeśli puste, uruchom najpierw `kb:setup`.

---

## Krok 5: Cross-source boost + Intra-source intensity

Po zebraniu wszystkich odkryć — deduplikacja i ranking. **Dwa równoległe sygnały** podnoszą priorytet:

### A) Cross-source (różne źródła)

Ten sam wzorzec w ≥2 niezależnych źródłach → realny problem zespołowy (nie anegdota).

```
Wzorzec w ≥2 źródłach        → Priority +1 poziom
Wzorzec w ≥3 źródłach        → Priority = High (override)
Wzorzec u ≥2 różnych userów  → dodaj "(team-wide)" w Title
```

### B) Intra-source intensity (powtarzalność w jednym źródle)

Pojedyncze źródło, ale silnie powtarzalne → też silny sygnał (#8 Macieka: 5× w Chat).

```
≥5 wystąpień w jednym źródle  → Priority = High (nawet bez cross-source)
≥3 wystąpienia w jednym źródle → Priority = Medium minimum
```

### Łącznie — final Priority:

```
final_priority = max(
  base_priority_from_kriteria,
  cross_source_boost,
  intra_source_intensity
)
```

Jeśli kolizja (np. cross-source mówi Medium, intra-source mówi High) → bierz wyższy.

Consolidated output (dla bootstrapu):
```
📊 Knowledge Base Bootstrap — {Imię} — {Data}

Przeskanowano:
  • Claude Code:  X sesji / Y odkryć
  • Claude Chat:  X konwersacji / Y odkryć
  • Gmail:        X wątków / Y odkryć
  • Slack:        X wiadomości / Y odkryć
  • Drive:        X plików / Y odkryć

🎯 Łącznie: Z odkryć → Notion
  • SOP:            N wpisów
  • Skill Backlog:  N wpisów
  • n8n Automation: N wpisów
  • Pominięto:      N (brak powtarzalności)
```

---

## Krok 6: Slack #ai-feedback

Post do `#ai-feedback` (C0AS00SNGQZ) — tylko jeśli tryb `bootstrap` lub ≥1 odkrycie High priority:

```
🧠 {Bootstrap/Weekly} Knowledge Base — {Imię} — {Data}

📊 {X} odkryć → Notion:
  • SOP: N  |  Skill: N  |  n8n: N
  ↑ Cross-source boost: N wzorców w ≥2 źródłach

🎯 Top 3 priorytety:
1. [High] {opis odkrycia 1} ({type})
2. [High] {opis odkrycia 2} ({type})
3. [Medium] {opis odkrycia 3} ({type})

📁 Notion: {link do Knowledge Base}
```

---

## Krok 7 (Bootstrap only): Setup scheduled task

Po bootstrapie zaproponuj weekly auto-run:

```
Bootstrap zakończony. Czy ustawić cotygodniowy scan?
(a) Poniedziałek 10:00 [rekomendowane]
(b) Piątek 15:00
(c) Inny termin
(d) Nie — będę uruchamiał manualnie
```

Dla Cowork: skill `schedule` → `knowledge-base --mode weekly`
Dla Claude Code: zaplanuj task `wsd-kb-weekly-scan`
Dla Chat: przypomnij o kalendarzu Google

---

## Krok 8: Memory update

Po zakończeniu (bootstrap lub weekly) zaktualizuj memory:
```
knowledge-base: last_run={DATE}, mode={MODE}, discoveries={N}
```

---

## Compliance: stop conditions

NIE uruchamiaj jeśli:
- Anti-AI clause w umowie projektowej → STOP + skonsultuj z Wojciechem (wfs@off.org.pl)
- Tajemnica zawodowa / legal → STOP
- NDA z explicit AI processing prohibition → STOP

---

## Quick reference

```
# Bootstrap (jednorazowo):
Uruchom skill knowledge-base w trybie bootstrap.
Imię: [Twoje imię], Email: [Twój @off.org.pl]
Zakres: all-time, wszystkie źródła

# Weekly (cotygodniowo):
Uruchom skill knowledge-base w trybie weekly.
Imię: [Twoje imię], Email: [Twój @off.org.pl]
```

---

*knowledge-base v1.0 · OFF AI v3.0 · msm-glitch/knowledge-base*
