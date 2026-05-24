# knowledge-base

Skill do zbierania wiedzy operacyjnej zespołu OFF z wielu źródeł (Gmail, Slack, Google Drive, sesje Claude) i klasyfikowania odkryć jako: SOP, Skill Backlog lub n8n Automation — bezpośrednio do Notion.

## Tryby

| Tryb | Kiedy | Co skanuje | Jak często |
|---|---|---|---|
| `bootstrap` | Jednorazowo (pierwsze uruchomienie) | Cały lifetime każdego źródła | 1× |
| `weekly` | Co poniedziałek 10:00 | Ostatnie 7 dni | Co tydzień |

---

## Hierarchia: SOP jako root — Skill/n8n jako sub-resources

SOP jest encją nadrzędną (root) w Knowledge Base. Skill i n8n są **sub-resources** kroków SOPa — nie bytami samodzielnymi.

```
SOP "partner-reaktywacja"
├── Krok 1: pobierz listę z CRM          → n8n  (sub-resource: crm-stale-partners)
├── Krok 2: zweryfikuj fit               → Human
├── Krok 3: napisz mail otwierający      → Skill (sub-resource: off-reaktywacja-partnera)
└── Krok 4: wyślij + zapisz + follow-up  → n8n + Skill
```

**Konsekwencje dla klasyfikacji:**
- Odkrywasz Skill lub n8n → szukaj parent SOP. Jeśli nie istnieje → utwórz `[NEW] SOP — {slug}` jako osobny wpis w tym samym runie.
- Wpis Skill/n8n bez Parent SOP → `Parent SOP: —` (standalone), ale to wyjątek, nie reguła.
- Jedno SOP może mieć wiele powiązanych Skills i n8n flows — każdy z nich ma pole `Parent SOP` wskazujące slug.

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
- Szukaj wątków z keywords i query specs z `config/sources.yaml` → `gmail.query_spec`
- Filtruj: nie SPAM, nie TRASH
- Odnotuj: nadawca/odbiorca, temat, czy sugeruje powtarzalny proces

**Compliance:** nie cytuj PII (PESEL, NIP, dane osobowe z grantów).

### 1E — Slack

Przez Slack MCP (`mcp__8c5de80e`):
- Kanały z `config/sources.yaml` → `slack.channels` (używaj channel_ids, nie nazw)
- Szukaj: decyzje, procesy, prośby o pomoc które się powtarzają
- Pomiń: wiadomości z hasłami, danymi poufnymi

### 1F — Google Drive

Przez Drive MCP (`mcp__7a8eafc1`):
- Foldery z `config/sources.yaml` → `google_drive.folders`
- Nowe/zmienione pliki w zakresie dat z `google_drive.query_spec.lookback`
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
[ ] 11. Jeśli Type=Skill lub n8n: wskaż Parent SOP (slug lub "—" jeśli standalone)
[ ] 12. Czy occurrence count spełnia minimum per typ?
        → SOP: ≥2 | Skill: ≥3 | n8n: ≥2
        → jeśli poniżej progu: flag candidate_{type}, NIE zapisuj do Notion
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
Parent SOP: —  (standalone fix)
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
Parent SOP: mr-mass-outreach
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

### Kryteria klasyfikacji — rozłączne drzewo 4-krokowe

Pytania zadawaj **po kolei** — pierwszy TAK kończy klasyfikację.

```
1. Czy wzorzec jest merytoryczny + powtarzalny + ma jasny input/output?
   NIE → POMIŃ (jednorazowe, meta, preferencja osobista, dane wrażliwe)
   TAK → pytanie 2

2. Czy proces wymaga ludzkiego osądu / decyzji / accountability w środku?
   TAK → SOP  (Executor: Human lub Hybrid)
       → Czy krok w SOPie jest AI-kreatywny? → oznacz w Related skills
       → Czy krok jest deterministyczny? → oznacz w Related n8n
   NIE → pytanie 3

3. Czy output jest kreatywny / wariantowy / wymaga brand voice OFF?
   TAK → Skill Backlog (wymagane: ≥3 wystąpienia — sprawdź config/sources.yaml)
       → Sprawdź skills_catalog.yaml: skill już istnieje? → [FIX], nie [NEW]
   NIE → pytanie 4

4. Czy jest jasny deterministyczny trigger + pipeline bez punktów decyzji?
   TAK → n8n Automation (wymagane: ≥2 wystąpienia lub trigger >1×/tydzień)
   NIE → SOP (Executor: Human, do późniejszej dekompozycji)
```

**Krok 5 (opcjonalny — multi-executor SOP):** Jeśli SOP z pytania 2 lub 4 zawiera >1 typ executora (AI + Auto + Human) — utwórz SOP główny **i osobne wpisy** dla każdego sub-zasobu (Skill/n8n) z `Parent SOP = slug SOPa`.

### 6 precedensów dla przypadków granicznych

| # | Sytuacja | Klasyfikacja | Uzasadnienie |
|---|---|---|---|
| 1 | Proces z 1 krokiem kreatywnym + 3 deterministycznymi | **SOP** główny + **Skill** sub-resource | Decyzja o uruchomieniu wymaga człowieka (pyt. 2 TAK); Skill implementuje 1 krok |
| 2 | n8n flow z pause-point "czekaj na zatwierdzenie Michała" | **SOP** (Executor: Hybrid) | Każdy punkt decyzji człowieka = SOP; n8n to krok SOPa, nie byt samodzielny |
| 3 | Claude proszony o to samo 2× (poniżej min 3) | **POMIŃ** — flag `candidate_skill` | Skill min=3; wróć z wpisem dopiero przy 3. potwierdzonym wystąpieniu |
| 4 | n8n flow uruchamiany <1×/tydzień (np. roczny raport) | **SOP** (Human) lub n8n z `Priority: Low` | Koszt budowy > oszczędność przy niskiej volumetrii; decyzja ROI |
| 5 | Nowy skill pokrywa 80% istniejącego | **[FIX]** istniejącego | Fuzzy match ≥0.75 na skills_catalog → zawsze [FIX], nigdy [NEW] |
| 6 | Zadanie powtarzalne ale "każdy przypadek inny" | Wyciągnij 3-7 **powtarzalnych kroków** → **SOP** | "Robimy elastycznie" = brak dokumentacji, nie brak procesu; wymuś Steps |

### Priorytety:

| Priority | Kiedy |
|---|---|
| High | Powtarza się ≥3× LUB blokuje pracę LUB zajmuje >30 min |
| Medium | Powtarza się 2× LUB byłoby przydatne dla ≥3 osób |
| Low | Spełnia minimum occurrence, ale niska pilność |

Minimum occurrence per typ (z `config/sources.yaml → classification_thresholds`):
- SOP: ≥2 wystąpienia
- Skill: ≥3 wystąpienia
- n8n: ≥2 wystąpienia (lub jasny trigger cykliczny ≥1×/tydzień)

---

## Krok 3.5: Quality gates (KRYTYCZNE — sprawdź PRZED zapisem)

### ❌ NIE ZAPISUJ (skip rules):

1. **Meta-wpisy** — wpis dotyczy samego procesu skanowania/budowy KB:
   - `knowledge-base`, `weekly-discovery`, `team-knowledge-base`, `WSD`, `Weekly Skill Discovery`
   - Wpisy "buduję skill który będzie skanował sesje" → pomiń

2. **"Stan istniejącego skilla"** bez konkretnego problemu:
   - "Skill X działa, użytkownicy go testują" → POMIŃ
   - "Skill X wymaga poprawki Y bo trigger nie działa" → ZAPISZ jako [FIX]

3. **Jednorazowe pytania** — poniżej progu minimalnego (SOP<2, Skill<3, n8n<2)

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

### ❌ Zaktualizowane anty-wzorce (v1.1)

| Anty-wzorzec | Przykład | Co zrobić |
|---|---|---|
| Skill < 3 wystąpień | `[NEW] Skill — nowy-mail` ale tylko 2× w source | POMIŃ; flag `candidate_skill`; wróć przy 3. wystąpieniu |
| Brak `Parent SOP` dla Skill/n8n | Pole puste zamiast slug lub `—` | Wpisz slug parent SOPa lub jawnie `—` (standalone) |
| Wymyślone trigger phrases | "Skill triggeruje na X" bez evidence | Skopiuj dosłownie ≥5 fraz z Slack/Gmail/Chat |
| n8n bez error handling | "Wysyła maile i gotowe" | Dopisz retry + dead letter + Slack alert do kogo |
| Skill nakłada się na istniejący | `nowy-mail-skill` gdy `followup-mail` istnieje | Zmień na `[FIX] followup-mail`, nie twórz nowego |
| User = skanujący zamiast autora wzorca | Maciek skanuje, wzorzec u Michała | User = Michał |
| SOP bez Definition of Done | "Skończone gdy wszystko gotowe" | Wymuś checklist 3-5 pozycji sprawdzalnych |
| Odkrycie bez Source URL | Puste pole lub placeholder | Wpisz jawnie `—`; bez URL nie idzie do Notion |

---

## Krok 3.6: Cross-cutting concerns (adapted multi-channel)

### Model selection per pass

| Pass | Claude Code | Claude Chat | Claude Cowork |
|---|---|---|---|
| Pass 1: Discovery scan | standard Sonnet (opcjonalnie Opus dla głębokiego bootstrapu) | standard Sonnet | standard Sonnet |
| Pass 2: Enrichment | standard Sonnet | standard Sonnet | standard Sonnet |
| Pass 3: Quality gates | standard Sonnet | standard Sonnet | standard Sonnet |
| Pass 4: Anti-duplicate | standard Sonnet (Notion query) | standard Sonnet | standard Sonnet |

### Budget cap per run

| Kanał | Cap tokenów | Uwagi |
|---|---|---|
| Claude Code (local) | ~200K | pełny skan JSONL + 4 źródła |
| Claude Chat | ~80K | brak lokalnych JSONL |
| Claude Cowork | ~80K | brak lokalnych JSONL |

Jeśli cap osiągnięty przed końcem skanu: zakończ bieżące źródło, przejdź do zapisu zebranych draftów, zaraportuj `"Budget cap reached — N sources skipped"` w podsumowaniu.

### Rate limity MCP

- Max **10 wywołań MCP/min** na jedno źródło
- Przy `429 Too Many Requests`: exponential backoff 2 s → 4 s → 8 s (max 3 próby)
- Po 3 niepowodzeniach: oznacz źródło `source_error`, kontynuuj kolejne źródło

### Error handling

| Błąd | Akcja |
|---|---|
| MCP timeout / 5xx | Retry 2× z backoff; jeśli fail → draft dostaje `needs_enrichment = true` |
| Notion write fail | Retry 1×; jeśli fail → log w podsumowaniu, NIE porzucaj draftu |
| Anti-AI clause w source | STOP natychmiast, poinformuj usera, nie zapisuj źródła |
| PII wykryte w drafcie | REDACT przed zapisem; dodaj `Status = New` + notatka "Needs review" |

### Brak lokalnego storage

**BEZ SQLite.** Dedup wyłącznie przez Notion query (Pass 3 → `notion-query-database-view`).

**BEZ `/runs/` na dysk.** Drafty trzymaj in-memory do zapisu w Notion. Wpisy odrzucone zapisz w Notion ze `Status = Rejected`. Wpisy do wzbogacenia zapisz ze `Status = Draft` (do triage przez Wojciecha).

---

## Krok 4: Zapis do Notion Knowledge Base

### Pola wspólne (wszystkie typy):

```
Title:               "[NEW/FIX/BUG] {YYYY-MM-DD} · {Imię} · {Type slug} — {opis}"
Type:                SOP | Skill Backlog | n8n Automation
Source:              [Claude Code | Claude Chat | Claude Cowork | Gmail | Slack | Google Drive]
Date:                data ostatniego wystąpienia (YYYY-MM-DD)
Week:                ISO week (np. "2026-W21")
Summary:             Format STRICT:
                       Zdanie 1: Co — wzorzec + liczba × + zakres dat
                       Zdanie 2: Dowód — gdzie/kto (Source URLs)
                       Zdanie 3: Triggers obs. (TYLKO Skill Backlog)
                       Zdanie 4: Next: {1 actionable krok dla ownera}
Priority:            High | Medium | Low (po Pass 4 normalizacji)
Status:              New | Triaged | In Progress | Implemented | Validated | Rejected | Draft
User:                Notion Person ID (z config/notion.yaml)
User name (fallback): imię tekstowo jeśli brak Notion ID
Source URL:          PERMALINK do oryginału (Slack: slack_get_permalink, nie app_redirect)
Source examples:     2-3 dodatkowe linki do prawdziwych instancji
Scan type:           Bootstrap | Weekly | WSD-relay
Occurrences:         liczba wystąpień wzorca (int, default 1)
Sources count:       liczba unikalnych źródeł (int, default 1)
Time saved (min/week): szacunek oszczędności po wdrożeniu (int)
Implementation size: S (<2h) | M (2-8h) | L (>8h)
Owner:               kto odpowiada za wdrożenie (mapuj wg tabeli poniżej)
Parent SOP:          slug parent SOPa (dla Skill/n8n) lub "—" (dla SOP root lub standalone)
ROI score:           occurrences × sources × time_saved_min / impl_size_factor  (auto)
```

**Mapowanie Owner per typ wpisu:**

| Typ wpisu | Owner |
|---|---|
| [FIX] istniejącego skilla | skill-creator (Wojciech) |
| [BUG] blokujący | autor wzorca + Wojciech |
| [NEW] Skill Backlog | skill-creator (Wojciech) |
| [NEW] n8n Automation | n8n-admin (Maciek) |
| [NEW] SOP | autor wzorca |
| Team-wide (≥3 osoby) | Wojciech + Maciek |

**Implementation size factor:** S=1, M=4, L=12 (do obliczenia ROI).

**Jak szacować time_saved:**
- Z wpisów: jeśli source mówi "2h/kampanię, 4× w miesiącu" → 2h×4/4 tyg = 120 min/tydzień
- Jeśli brak danych: konserwatywnie 15 min/tydzień (Low), 60 (Medium), 180 (High)

---

### Schema 4A — Type: SOP (dodatkowe pola obowiązkowe)

```
Process slug:           kebab-case unikalny (np. partner-reaktywacja)
Trigger:                Kiedy proces się odpala — 1 zdanie (event / data / request)
Inputs:                 Lista: dane, dostęp, decyzje wymagane na wejściu
Outputs:                Lista: artefakt, decyzja, stan po zakończeniu
Steps:                  3-7 kroków: "N. {Imperatyw}. Executor: {Human|AI|Auto|Hybrid}. Output: {co}."
Decisions:              Punkty decyzyjne: "Decyzja: {co?} → Kryterium: {jak?} → Decydent: {kto?}"
Definition of Done:     Checklist 3-5 pozycji sprawdzalnych (nie ogólniki)
Edge cases:             Lista "if X → do Y" lub "STOP + ping {kto}"
Executor target overall: Human | AI | Hybrid | Auto (dominujący)
Frequency:              daily | weekly | monthly | quarterly | yearly | on-demand
Related skills:         lista slugów Skill z tego SOPa (z skills_catalog.yaml)
Related n8n:            lista flow n8n (lub kandydatów do budowy)
```

---

### Schema 4B — Type: Skill Backlog (dodatkowe pola obowiązkowe)

```
Skill name:          kebab-case (sprawdź skills_catalog.yaml — nie duplikuj)
Description:         Do czego skill służy — 1-2 zdania kontekstu biznesowego
Trigger phrases:     ≥5 fraz DOSŁOWNIE skopiowanych z source (Slack/Gmail/Chat)
Input format:        Co user wkleja/pisze (notatki, lista, link, brief)
Output format:       Co skill produkuje (struktura, długość, format)
Examples:            2-3 pary: raw input + ideal output (z prawdziwych instancji)
Persona/style guide: Brand voice OFF + odniesienie do off-brand-voice jeśli stosuje
Edge cases:          Co skill MUSI rozróżnić (VIP vs casual, program A vs B)
Related skills:      inne skille OFF w łańcuchu (sekwencja wywołań)
```

---

### Schema 4C — Type: n8n Automation (dodatkowe pola obowiązkowe)

```
Flow name:              kebab-case
Trigger:                Konkretny event (cron / webhook / form submit / DB change)
Data sources:           Systemy na wejściu z konkretnymi API/endpointami
Transformations:        Co flow robi z danymi (filter / enrich / dedupe / map / aggregate)
Destinations:           Gdzie ląduje output (system + akcja)
Error handling:         Retry strategy + dead letter + Slack alert do kogo (OBOWIĄZKOWE)
Volume estimate:        Ile rekordów/triggerów dziennie/tygodniowo
Manual steps remaining: Które kroki ZOSTAJĄ przy człowieku i dlaczego (zawsze coś zostaje)
Credentials:            Lista wymaganych kluczy API / tokenów / service accounts
Dependencies:           Zewnętrzne systemy i ich wersje (monday.com, Google Forms, etc.)
Test plan:              Jak zweryfikować że flow działa — 1-3 scenariusze testowe
Related SOP:            Slug SOPa, którego krokiem jest ten flow
Related skill:          Czy w pipeline jest call do Claude skilla
```

---

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
  • Pominięto:      N (poniżej progu / brak powtarzalności)
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
knowledge-base: last_run={DATE}, mode={MODE}, discoveries={N},
  by_type={SOP:N, Skill:N, n8n:N}, rejected={N}
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

*knowledge-base v1.1 · OFF AI v3.0 · msm-glitch/knowledge-base*
