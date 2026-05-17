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

**Etapy:**
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

## Krok 3: Klasyfikacja odkryć

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
Title:    "{YYYY-MM-DD} · {Imię} · {Krótki opis odkrycia}"
Type:     SOP | Skill Backlog | n8n Automation
Source:   [Claude Code | Claude Chat | Claude Cowork | Gmail | Slack | Google Drive]
Date:     data odkrycia (YYYY-MM-DD)
Week:     ISO week (np. "2026-W21")
Summary:  2-3 zdania: co to jest + dlaczego warto wdrożyć
Priority: High | Medium | Low
Status:   New
User:     Notion Person ID (z config/notion.yaml)
User name (fallback): imię tekstowo jeśli brak Notion ID
Source URL: link do oryginału (jeśli dostępny)
Scan type: Bootstrap | Weekly
```

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
