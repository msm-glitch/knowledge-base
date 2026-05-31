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

## Orkiestracja: kto skanuje co (item #8)

Problem: 11 osób × weekly, każdy skanuje wspólny #general, Drive i całą skrzynkę → ten sam
wzorzec wykrywany N razy (koszt × N + N× ryzyko duplikatów, łagodzone tylko przez Pass 3).

Model z `config/sources.yaml → scan_ownership`:

| Źródło | Kto skanuje | Częstotliwość |
|---|---|---|
| **Slack, Google Drive** (współdzielone) | JEDEN team-runner (`shared_runner`, domyślnie Maciek) | 1× / tydzień dla całego zespołu |
| **Claude Code/Chat/Cowork, Gmail** (osobiste) | każdy swoje | 1× / tydzień per osoba |

- **Atrybucja działa nadal:** team-runner ustawia `User` = autor wiadomości (nie runner).
- Dzięki temu wspólne źródła są skanowane raz, a nie 11×; osobiste sesje skanuje tylko właściciel.
- Jeśli team-runner niedostępny — fallback: pierwszy weekly w tygodniu przejmuje shared sources
  (oznacz w podsumowaniu "shared scan by {kto}").

---

## Krok 0: Pre-flight (zawsze)

**0.0 — Gate konfiguracji (STOP jeśli niepełna):**
```bash
python3 scripts/kb_setup.py validate
```
- exit `0` → config OK, kontynuuj.
- exit `≠0` → są błędy krytyczne (puste Notion DB ID lub Slack channel_id dla aktywnych kanałów).
  Pokaż output, uruchom `python3 scripts/kb_setup.py resolve` (mówi co i skąd uzupełnić) i
  **NIE zaczynaj skanu** — inaczej dostaniesz złą atrybucję i martwe kanały (item #1).

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
- **Self-ingestion guard (item #6):** ten skill POSTUJE do `#ai-feedback` i go SKANUJE.
  Pomiń wiadomości pasujące do `slack.self_ingestion_guard` (prefiksy podsumowań KB + posty
  bota), inaczej własny raport wpadnie jako "odkrycie" (pętla). WSD-relay obsługuje osobno
  `wsd_relay_signals`.

### 1G — Watermark (weekly, item #4)

Dla trybu `weekly` skanuj treści **nowsze niż** watermark danego źródła:
```bash
python3 scripts/kb_state.py get-watermark --source slack   # → ostatni znacznik lub null
```
Po skanie zaktualizuj: `python3 scripts/kb_state.py set-watermark --source slack --ts <ISO>`.
Dzięki temu weekly nie czyta wszystkiego od nowa (koszt + duplikaty). Bootstrap ignoruje watermark.

### 1F — Google Drive

Przez Drive MCP (`mcp__7a8eafc1`):
- Foldery z `config/sources.yaml` → `google_drive.folders`
- Nowe/zmienione pliki w zakresie dat z `google_drive.query_spec.lookback`
- Odnotuj: tytuł, typ dokumentu, czy to procedura/instrukcja/szablon

---

## Krok 2: Filtr compliance

**Dwa etapy: najpierw twardy gate deterministyczny, potem osąd LLM.**

### 2A — Deterministyczny gate PII (must-pass, item #5)

Skanowanie po `skip_patterns` w ścieżce to za mało — PESEL wklejony do "zwykłej" sesji
przejdzie. Dlatego KAŻDE pole tekstowe wpisu (zwł. `Summary`, `Source examples`) przepuść
przez regexowy redaktor **zanim** cokolwiek trafi do Notion/Git:

```bash
echo "$pole_tekstowe" | python3 scripts/compliance.py redact      # zwraca tekst z [REDACTED:TYP]
echo "$pole_tekstowe" | python3 scripts/compliance.py scan         # {findings, must_block}
```

- Wykrywa: **PESEL/NIP** (z sumą kontrolną — mało false-positive), **IBAN PL**, email, telefon PL.
- Jeśli `must_block=true` (PESEL/NIP/IBAN) → użyj zredagowanej wersji; bez redakcji wpis NIE idzie dalej.
- To jest powtarzalne i nie zależy od osądu modelu.

### 2B — Osąd LLM (rzeczy nieregexowe)

Po gate sprawdź to, czego regex nie złapie:
- Imiona beneficjentów Mini Granty w kontekście → REDACT
- Sekrety (hasła, tokeny, API keys) → REDACT + flag Needs review
- Treści NDA (partner pod NDA) → FLAG, nie zapisuj summary
- Anti-AI clause → STOP + poinformuj usera

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
       → uruchom: python3 scripts/kb_lib.py catalog --name "{slug}" --catalog config/skills_catalog.yaml
       → deterministyczny fuzzy match (substring lub Levenshtein ≤3) na base_off+extended_uao+extended_extra
       → JEŚLI "matched" ≠ null (prefix_hint=[FIX]): wymuś [FIX] zamiast [NEW]
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
        → SOP: ≥2 | Skill: ≥3 | n8n: ≥2 (próg z config/sources.yaml → classification_thresholds)
        → poniżej progu: NIE zapisuj do Notion, ale ZAPISZ do ledgera (akumulacja między skanami):
          python3 scripts/kb_state.py record --type "{Type}" --slug "{slug}" --date {Date} \
              --source "{Source}" --user "{User}" --url "{Source URL}"
        → na starcie skanu sprawdź kto już dobił do progu:
          python3 scripts/kb_state.py ready --thresholds config/sources.yaml
          (te wzorce promujesz do Notion mimo że w bieżącym skanie były <próg; po zapisie:
           python3 scripts/kb_state.py promote --key "{Type}::{slug}")
```

Jeśli ≥1 check fail → popraw draft LUB odrzuć do `rejected_drafts.log`.
Dopiero po wszystkich ✅ → przejdź do Pass 3.

### Pass 3 — ANTI-DUPLICATE QUERY (przed zapisem do Notion)

Dla każdego draftu, **przed `notion-create-pages`**, query Notion KB DB:

```
query: filter by (Type == draft.Type) AND (Status != "Rejected")
       AND (Date in [draft.Date - W, draft.Date + W])
```

**Okno W zależy od trybu** (`config/sources.yaml → dedup.window_days`, item #4):
`bootstrap = 365 dni` (lifetime scan gubił duplikaty starsze niż 2 tyg.), `weekly = 14 dni`.

Similarity liczy **skrypt** (deterministycznie, nie "na oko" — item #3). Zrzuć draft i wyniki
Notion do JSON i wywołaj:
```bash
python3 scripts/kb_lib.py dedup --draft draft.json --existing notion_hits.json
# → {"similarity": 0.84, "action": "MERGE", "match": {...}}
```
Wzór (w kb_lib): `similarity = 0.4·jaccard(titles) + 0.4·skill_name_match + 0.2·user_match`.
Progi (`merge_at`/`flag_at`) są w configu i w kb_lib — spójne.

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

Nie licz tego ręcznie — zrzuć wpisy do JSON (`[{"id","priority","score"}]`, gdzie
`score = occurrences × sources × time_saved_min`) i wywołaj skrypt (item #3):
```bash
python3 scripts/kb_lib.py normalize --entries entries.json
# → {"entries":[...], "changes":[...], "high_pct_before":0.6, "high_pct_after":0.2}
```
Dla każdej pozycji w `changes` zrób `notion-update-page` (Priority High→Medium).

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

### ❌ Zaktualizowane anty-wzorce

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

Źródło: `config/sources.yaml → models` (item #9 — środowisko OFF działa na rodzinie 4.x;
wcześniej było wszędzie nieaktualne "standard Sonnet").

| Pass / tryb | Model | Uwaga |
|---|---|---|
| Pass 1: Discovery scan | **Sonnet** | szeroki skan — tani, szybki |
| Pass 1: token strategy Light | **Haiku** | tylko metadane/tytuły — najtańszy |
| Pass 1: bootstrap (C) Deep | **Opus** | głębsza analiza JSONL — tylko na żądanie usera |
| Pass 2: Enrichment | **Sonnet** | |
| Pass 3: Quality gates / Anti-duplicate | **Sonnet** | liczby i tak liczy skrypt (kb_lib), nie model |

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

### Storage stanu (item #4 — zaktualizowane)

**BEZ SQLite, BEZ zrzutów `/runs/` na dysk.** Drafty bieżącego skanu trzymaj in-memory.
Dedup żywych wpisów dalej przez Notion query (Pass 3 → `notion-query-database-view`).

**ALE: lekki, commitowany stan w `state/`** (małe JSON, audytowalne w git):
- `state/candidates.json` — ledger subprogowych wzorców (akumulacja occurrences między skanami,
  inaczej Skill `≥3×` widziany 1×/tydzień nigdy nie dobije do progu).
- `state/watermarks.json` — od kiedy skanować per źródło (weekly nie czyta wszystkiego od nowa).

Obsługa: `scripts/kb_state.py` (patrz `state/README.md`). Wpisy odrzucone → Notion `Status = Rejected`.
Do wzbogacenia → `Status = Draft` (triage przez Wojciecha).

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

**Mapowanie Owner per typ wpisu** (lustro `config/ownership.yaml` → `owner_by_kind` — KANON tam):

| Typ wpisu | Owner |
|---|---|
| [FIX] istniejącego skilla | owner skilli (Maciek) |
| [BUG] blokujący | autor wzorca + Wojciech |
| [NEW] Skill Backlog | owner skilli (Maciek) |
| [NEW] n8n Automation | n8n-admin (Maciek) |
| [NEW] SOP | autor wzorca |
| Team-wide (≥3 osoby) | Wojciech + Maciek |

> Wartości pochodzą z `config/ownership.yaml`. Jeśli się rozjadą — **config wygrywa**, popraw tabelę.
> (Wcześniej README mówił Skill→Michał, n8n→Wojciech/Michał — sprzeczność z tą tabelą, item #2.)

**Implementation size factor:** S=1, M=4, L=12 (do obliczenia ROI score — patrz `scripts/kb_lib.py roi`).

**Jak szacować time_saved:**
- Z wpisów: jeśli source mówi "2h/kampanię, 4× w miesiącu" → 2h×4/4 tyg = 120 min/tydzień
- Jeśli brak danych: konserwatywnie 15 min/tydzień (Low), 60 (Medium), 180 (High)

---

### Schema 4A — Type: SOP (pola adaptacyjne — patrz Krok 4.5)

**Zasada:** NIE definiujemy formatu z góry. Lista pól poniżej to **starting template** (minimum viable + obserwowane z dotychczasowej praktyki OFF). Krok 4.5 derywuje faktyczny zestaw pól per draft z prior SOPs w Notion — jeśli ≥60% prior SOPs ma pole X, dodajemy je do template'u. Format ewoluuje wraz z dojrzewaniem zespołu.

#### Minimum (zawsze wypełniaj — bez tego SOP jest niewykonywalny):
```
Process slug:           kebab-case unikalny (np. partner-reaktywacja)
Trigger:                Kiedy proces się odpala — 1 zdanie (event / data / request)
Steps:                  3-7 kroków: "N. {Imperatyw}. Executor: {Human|AI|Auto|Hybrid}. Output: {co}."
Outputs:                Lista: artefakt, decyzja, stan po zakończeniu
Definition of Done:     Checklist 3-5 pozycji sprawdzalnych (nie ogólniki)
Executor target overall: Human | AI | Hybrid | Auto (dominujący)
Frequency:              daily | weekly | monthly | quarterly | yearly | on-demand
```

#### Obserwowane (dodaj jeśli ≥60% prior SOPs to ma):
```
Inputs:                 Lista: dane, dostęp, decyzje wymagane na wejściu
Decisions:              Punkty decyzyjne: "Decyzja: {co?} → Kryterium: {jak?} → Decydent: {kto?}"
Edge cases:             Lista "if X → do Y" lub "STOP + ping {kto}"
Related skills:         lista slugów Skill z tego SOPa (z skills_catalog.yaml)
Related n8n:            lista flow n8n (lub kandydatów do budowy)
```

#### Pierwsze uruchomienie (puste Notion SOPs DB):
Użyj pełnego template'u (minimum + obserwowane). Po pierwszym tygodniu Wojciech reviewuje, które pola faktycznie były wypełniane przez team — te zostają w template, reszta wypada. Krok 4.5 robi to automatycznie od 2. tygodnia.

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

## Krok 4.5: Auto-generacja artefaktów

Po zapisie do Notion każdy wpis ma już wszystkie pola potrzebne do wygenerowania pliku artefaktu. Ten krok zamyka pętlę: z `[NEW]` wpisu Notion → konkretny draft pliku w repo, gotowy do code review przez ownera.

### Co generujemy (tylko dla `[NEW]`, nie `[FIX]`/`[BUG]`):

| Type wpisu | Wygenerowany artefakt | Owner do review |
|---|---|---|
| SOP | `artifacts/sops/{Process_slug}.md` | autor wzorca |
| n8n Automation | `artifacts/n8n/{Flow_name}.json` | Maciek |
| Skill Backlog | `artifacts/skills/{Skill_name}/SKILL.md` | Maciek |

`[FIX]` wpisy NIE generują nowego artefaktu — owner robi punktową edycję istniejącego pliku (slug w Title wskazuje który).

### Zasada: format SOP wynika z realnego użycia (nie z góry)

Przed generacją SOP draftu:

1. **Query Notion SOPs DB** (`config/notion.yaml → databases.sops`) — pobierz 3-5 ostatnich aktywnych SOPów (`Status ∈ {Validated, Implemented}`).
2. **Wyznacz observed field set** — które pola są wypełnione w ≥60% próbki.
3. **Zbuduj template** = minimum viable (z Schema 4A) ∪ observed field set.
4. **Jeśli SOPs DB jest puste** (pierwszy run): użyj pełnego starting template ze Schema 4A. Od 2. tygodnia template adaptuje się automatycznie.

Konsekwencja: format draftów odzwierciedla co naprawdę działa w OFF, nie co teoretycznie powinno być. Pola które nikt nie wypełnia same wypadną z template'u.

### SOP — generacja `artifacts/sops/{slug}.md` (format WYKONYWALNY — patrz [`artifacts/sops/SCHEMA.md`](artifacts/sops/SCHEMA.md))

SOP generowany jest **dwuwarstwowo**: frontmatter YAML (warstwa maszynowa, którą czyta i
wykonuje agent) + body Markdown (warstwa ludzka do review). Cel: artefakt jest kontraktem
wykonania, nie tylko notatką. Pełna specyfikacja pól i kontrakt wykonania:
[`artifacts/sops/SCHEMA.md`](artifacts/sops/SCHEMA.md). Wzorzec: `artifacts/sops/examples/partner-reaktywacja.md`.

Wyciągnij z Notion entry: `Process slug`, `Title`, `Trigger`, `Steps`, `Outputs`,
`Definition of Done`, `Decisions`, `Inputs`, `Owner`, `Parent SOP` + observed fields. Zmapuj
na frontmatter wg SCHEMA.md.

Struktura pliku:
```markdown
---
slug: {Process slug}
version: 1
status: draft
owner: {Owner}
source_url: "{Source URL}"
parent_sop: {Parent SOP slug lub null}
trigger: { type: {event|schedule|request|webhook}, spec: "...", description: "{Trigger}" }
executor_overall: {human|ai|auto|hybrid}
frequency: {Frequency}
inputs:  [ { name, type, source, required } ]       # typowane — patrz SCHEMA.md
outputs: [ { name, type, destination } ]
steps:                                               # KAŻDY krok: patrz reguły mapowania niżej
  - { id, action, automatable, executor, tool, inputs, outputs, preconditions, postconditions, on_error }
guardrails: { autonomy_level, irreversible_actions: [], pii_handling, escalation, anti_ai_clause }
acceptance_criteria: [ ... ]                         # maszynowo sprawdzalne predykaty (z Definition of Done)
metrics: { log_to: "state/runs.jsonl", fields: [...] }
---

# {Title bez prefix}

> Auto-gen {Date} · Owner: {Owner} · Status: Draft

## Trigger
{Trigger}

## Steps
{render steps[]: "N. {action} — executor / tool / automatable"}

## Decisions
{render decision[]: Decyzja → Kryterium (predykat) → Decydent → Fallback}

## Definition of Done
{acceptance_criteria[] jako checklist}

{Dla każdego observed field obecnego w entry: ## {Field name} → wartość}

---
<!-- Auto-generated by knowledge-base scan {Date}. Schema: artifacts/sops/SCHEMA.md. Template derived from {N} prior SOPs ({field_coverage}% coverage). -->
```

**Reguły mapowania (krytyczne dla agent-readiness):**
- Krok `Executor: Human` → `automatable: false`, `tool: null`, dopisz `requires_human: "{powód}"`.
- Krok wskazujący sub-resource (Related skill/n8n) → `tool: skill:{slug}` / `n8n:{slug}` + `implements: {slug}`.
- Krok z akcją zewnętrzną/nieodwracalną (wysyłka, płatność, publikacja) → dodaj `id` do
  `guardrails.irreversible_actions` (runtime wymusi approval przed wykonaniem).
- Krok bez znanego bindingu → `automatable: false` (NIE zgaduj `tool`).
- Puste pole z template'u → placeholder `[TBD: opisz {field}]` + komentarz `<!-- wymagane od owner -->`.

### n8n — generacja `artifacts/n8n/{flow_name}.json` (kontrakt zdolności w `meta` — patrz [`artifacts/n8n/SCHEMA.md`](artifacts/n8n/SCHEMA.md))

`nodes[]` zostają skeletonem (`type: TBD` = human-todo), ale **`meta` to kontrakt zdolności** —
żeby SOP mógł flow zawołać (`tool: n8n:{slug}`) i zweryfikować. Pełna specyfikacja:
`artifacts/n8n/SCHEMA.md`. Wzorzec: `artifacts/n8n/examples/mass-send-with-tracking.json`.

```json
{
  "name": "{Flow name}",
  "nodes": [
    { "name": "Trigger", "type": "n8n-nodes-base.{trigger_type}", "notes": "{Trigger z Notion}", "parameters": {} },
    { "name": "Source: {Data sources[0]}", "type": "TBD", "notes": "{credential needed}", "parameters": {} },
    { "name": "Transform", "type": "n8n-nodes-base.code", "notes": "{Transformations z Notion}", "parameters": {} },
    { "name": "Destination: {Destinations[0]}", "type": "TBD", "notes": "{action z Notion}", "parameters": {} },
    { "name": "Error handler", "type": "n8n-nodes-base.slack", "notes": "{Error handling z Notion}", "parameters": {} }
  ],
  "connections": {},
  "meta": {
    "slug": "{Flow name}",
    "version": 1,
    "status": "draft",
    "capability_ref": "n8n:{Flow name}",
    "io": { "input": [ {"name","type","required"} ], "output": [ {"name","type"} ] },
    "trigger": { "type": "{cron|webhook|form|db-change}", "spec": "{Trigger z Notion}" },
    "side_effects": "{read-only|writes-internal|external-send}",
    "credentials_required": ["{Credentials z Notion}"],
    "guardrails": { "autonomy": "{autonomous|supervised|human-gated}", "irreversible": false },
    "verification": { "test_plan": "{Test plan z Notion}", "healthcheck": "{sygnał że flow żyje}" },
    "manual_steps_remaining": "{Manual steps remaining}",
    "parent_sop": "{Parent SOP}",
    "notion_entry": "{Title}",
    "source_url": "{Source URL}"
  }
}
```

**Reguły mapowania:** `io` zgodne z krokiem SOPa, który woła flow. Flow `external-send` lub
`irreversible: true` → parent SOP MUSI mieć ten krok w `guardrails.irreversible_actions`. Maciek
importuje JSON do n8n cloud, dopina credentials, testuje wg `verification.test_plan`, a po
wdrożeniu ustawia `meta.status: active`.

### Skill — generacja `artifacts/skills/{skill_name}/SKILL.md` (kontrakt zdolności — patrz [`artifacts/skills/SCHEMA.md`](artifacts/skills/SCHEMA.md))

Body zostaje prozą (instrukcja dla LLM), ale **frontmatter to kontrakt zdolności** — żeby SOP
mógł skill zawołać (`tool: skill:{slug}`) i mu zaufać. Pełna specyfikacja: `artifacts/skills/SCHEMA.md`.
Wzorzec: `artifacts/skills/examples/off-reaktywacja-partnera/SKILL.md`. Z Notion entry:

```markdown
---
name: {Skill name}
version: 1
status: draft
description: {Description z Notion}
parent_sop: {Parent SOP slug lub null}
triggers:
{lista Trigger phrases z Notion — minimum 5}
io:                                  # typowane; nazwy/typy ZGODNE z krokiem SOPa, który woła skill
  input:  [ { name, type, required } ]
  output: [ { name, type } ]
capabilities:                        # least-privilege (konwencja tool jak w SOP)
  allow: [ ... ]
  deny:  [ ... ]                     # np. mcp:gmail/* jeśli skill drafuje a nie wysyła
side_effects: {read-only|writes-internal|external-send}
autonomy: {autonomous|supervised|human-review-output}
guardrails: { pii_handling: "redact via script:scripts/compliance.py", requires_human_review: {bool} }
evals:                               # golden set z Examples — maszynowo sprawdzalny samo-test
  - { id: 1, input_ref: "examples#1", assert: "{predykat}" }
---

# {Skill name}

## Kontekst        {Description rozwinięty}
## Input format    {Input format z Notion}
## Output format   {Output format z Notion}
## Examples        {Examples z Notion — 2-3 pary input/output}
## Style guide     {Persona/style guide z Notion}
## Edge cases      {Edge cases z Notion}
## Related skills  {Related skills z Notion}

---
<!-- Auto-generated by knowledge-base scan {Date}. Schema: artifacts/skills/SCHEMA.md. Source: {Source URL}. -->
```

**Reguły mapowania:** `io` musi zgadzać się z `inputs/outputs` kroku SOPa (Parent SOP), który
woła skill. Skill, który nic nie wysyła → `side_effects: read-only` + `deny` na narzędzia
wysyłkowe. `Examples` z Notion → `evals[]` z asercjami (proza zostaje w body). Brak danych do
pola → `[TBD: ...]`.

### Commit i push (po wszystkich generacjach w jednym run)

```bash
git add artifacts/
git commit -m "kb-scan {Date}: {N_sop} SOP + {N_n8n} n8n + {N_skill} skill drafts"
git push origin {current-branch}
```

Branch: jeśli skan uruchamiany lokalnie → osobny branch `kb-scan/{YYYY-MM-DD}-{user}`. Jeśli z GitHub Action → push na konfigurowany branch.

**Cykl życia draftu — KANON w [`artifacts/README.md`](artifacts/README.md) (item #7):**
NIE pushuj draftów na `main`. Review SLA: owner (per `config/ownership.yaml`) przegląda branch
w 7 dni (cotygodniowy triage). Branch bez aktywności >30 dni → zamknij, wpis Notion `Status=Rejected`.
Merge draftu → `Status=Implemented`. Bez tego branche `kb-scan/*` mnożą się i gniją.

### Powiadomienie ownerów

Slack post w Kroku 6 dostaje dodatkową sekcję:
```
📂 Drafty wygenerowane:
  • SOPs: artifacts/sops/{slug}.md ×N
  • n8n: artifacts/n8n/{slug}.json ×N
  • Skille: artifacts/skills/{slug}/ ×N
  → Review na branchu kb-scan/{date}
```

### Error handling

| Sytuacja | Akcja |
|---|---|
| Brak `Process slug` / `Flow name` / `Skill name` w Notion entry | Pomiń generację, flag draft `needs_slug`, log w podsumowaniu |
| Konflikt nazwy pliku (artefakt już istnieje) | Append `-v2` do slug, NIE nadpisuj |
| Git push fail | Retry 2× backoff; jeśli fail → artefakty zostają lokalnie, log "manual push required" |
| Notion SOPs DB query fail (template detection) | Fallback na pełny starting template, log "template detection skipped" |

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

## Krok 8.5: Metryki systemu (item #9 — feedback loop)

Raz na jakiś czas (np. miesięcznie) zmierz czy KB faktycznie działa — bez tego nie da się
stroić progów. Odpytaj Notion KB DB (`notion-query-database-view`), zrzuć wynik do JSON i:
```bash
python3 scripts/metrics.py --file notion_export.json
```
Patrz na: **High% vs cel 20%** (alert >35% = inflacja priorytetów), **implemented_rate**
(ile backlogu faktycznie wdrożono), **rejected_rate** (proxy false-positive klasyfikacji),
**backlog_open + ROI**. Jeśli rejected_rate wysoki → drzewo klasyfikacji za luźne; jeśli
implemented_rate niski → za dużo szumu albo brak ownerów.

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

*knowledge-base v2.2 · OFF AI v3.0 · msm-glitch/knowledge-base*
