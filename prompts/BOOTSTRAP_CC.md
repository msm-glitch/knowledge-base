# Knowledge Base — Bootstrap Claude Code (lifetime scan)

**Wersja:** 2.2 | **Data:** 2026-05-19 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w sesji Claude Code (CLI) jednorazowo — lifetime scan wszystkich sesji terminalowych + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_CC.md`.

**Dla kogo:** Osoby używające Claude Code CLI (`claude` w terminalu) — Michał, Wojciech, Krzysztof, Maciek.

**Czas:** ~60-90 min (token strategy Medium)

---

## PROMPT BOOTSTRAP — skopiuj i wklej w sesji `claude`:

```
# BOOTSTRAP KNOWLEDGE BASE v2.2 — LIFETIME SCAN (Claude Code)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan.

Uruchom skill `knowledge-base` z repozytorium `msm-glitch/knowledge-base` w trybie `bootstrap`.

## PHASE 0: PRE-FLIGHT

**0.1 — Wykryj usera i pokaż formularz PRE-FLIGHT:**

Sprawdź `git config user.email` i `~/.claude/projects/*/memory/user_profile.md`.
Następnie wyświetl poniższy formularz i **czekaj na odpowiedzi — nie zakładaj wartości domyślnych:**

---

**[1/4] Twoje dane**
Wykryto: `[email z git config lub "nieznany"]`, imię: `[z memory lub "nieznane"]`
→ Potwierdź lub popraw: "Tak, to ja" / "Poprawiam: [imię, email]"

*Jeśli dane nieznane lub niepewne — wymagam jawnego wpisu przed kontynuowaniem.*

---

**[2/4] Zakres skanu sesji**
Które projekty (cwd) skanować?
→ Wybierz i odpisz literę:
(a) Wszystkie (auto-skip dla legal/private wg config/sources.yaml)
(b) Tylko OFF-related — pomijam projekty prywatne
(c) Wybiórczo — poczekaj na listę CWD i wskaż numery

*Listę CWD z klasyfikacją pokażę po Twojej odpowiedzi.*

---

**[3/4] Token strategy**
Jak głęboko skanować?
(A) Light — tylko metadane + grep (~150K, ~5 min)
(B) Medium — + sampling 30 linii/sesja (~600K, ~15 min) ← rekomendowane
(C) Deep — full content (~2M+, ~60 min)
→ Odpisz literę: A / B / C

---

⛔ **Czekam na Twoje odpowiedzi [1], [2], [3] — dopiero potem zaczynam skan.**

## PHASE 0.5: CROSS-CUTTING CONCERNS (Claude Code)
**Gate konfiguracji (item #1) — STOP jeśli niepełna:**
Jeśli masz terminal/repo: `python3 scripts/kb_setup.py validate` (exit≠0 → pokaż błędy, `resolve`, STOP).
W Chat/Cowork sprawdź ręcznie, że `config/notion.yaml → users` i `config/sources.yaml → slack.channel_ids`
nie są puste — jeśli są, STOP i uzupełnij (inaczej zła atrybucja / martwe kanały).


Przed skanem skonfiguruj limity:

**Budget cap:** ~200K tokenów dla full scan (JSONL + Gmail + Slack + Drive).
Jeśli cap osiągnięty przed końcem: zakończ bieżące źródło, zapisz zebrane drafty, zaraportuj "Budget cap reached — N sources skipped".

**Model:** modele per pass wg `config/sources.yaml → models` (Sonnet: skan · Haiku: token strategy Light · Opus: bootstrap Deep na żądanie). Dla bootstrapu z opcją (C) Deep możesz wybrać Opus dla Pass 1 (głębsza analiza JSONL) — tylko na żądanie usera.

**Rate limity MCP:** max 10 wywołań/min na źródło. Przy 429: backoff 2s→4s→8s (max 3 próby). Po 3 fail: oznacz źródło `source_error`, kontynuuj.

**Error handling:**
- MCP timeout → retry 2× → draft dostaje `needs_enrichment = true`
- Notion write fail → retry 1× → log w podsumowaniu
- Anti-AI clause → STOP natychmiast, poinformuj

**BEZ lokalnego SQLite / BEZ /runs/ na dysk.** (item #4: lekki stan w `state/` — ledger kandydatów + watermarki, scripts/kb_state.py) Drafty in-memory → Notion. Odrzucone → `Status = Rejected`. Do wzbogacenia → `Status = Draft`.

---

**0.2 — Po odpowiedziach — załaduj config i pokaż listę CWD:**
- Odczytaj `config/notion.yaml` i `config/sources.yaml`
- Glob `~/.claude/projects/**/*.jsonl` → zdekoduj cwd → pokaż listę do override (jeśli user wybrał [2c] lub [2b])

**0.3 — Wykryj środowisko i klasyfikuj cwd:**

Najpierw sprawdź środowisko:
```bash
JSONL_COUNT=$(find ~/.claude/projects -name "*.jsonl" 2>/dev/null | wc -l)
CURRENT_SESSION_CWD=$(pwd)
```

**Jeśli `JSONL_COUNT == 0` lub `JSONL_COUNT == 1` (tylko bieżąca sesja):**

⚠️ **WYKRYTO ŚRODOWISKO ZDALNE (Claude Code on the web / cloud container)**

Twoja pełna historia sesji Claude Code jest na **maszynie lokalnej** — ten kontener ma dostęp tylko do bieżącej sesji i nie może przeskanować Twojej lokalnej historii.

**Wybierz jak kontynuować:**
```
(a) Pomiń skan CC JSONL — kontynuuj z Gmail + Slack + Drive
    [REKOMENDOWANE jeśli jesteś w cloud/web]

(b) Zatrzymaj — uruchom ten prompt ponownie lokalnie w terminalu:
    cd ~/knowledge-base && claude
    Wklej ten sam prompt w sesji CLI (nie web).

(c) Skanuj tylko bieżącą sesję jako próbkę (ograniczona wartość)
```
⛔ **Czekam na wybór (a/b/c) przed kontynuowaniem.**

---

**Jeśli `JSONL_COUNT > 1` (środowisko lokalne — pełna historia dostępna):**

Glob `~/.claude/projects/**/*.jsonl` → zdekoduj cwd → pokaż listę:

```
PRE-FLIGHT — kandydaci do skip:

🚫 AUTO-SKIP (legal/private):
 [1] /path/to/akta-spraw — X sesji

⚠️ FLAG (NDA/confidential):
 [...]

✅ INCLUDE (OFF-related):
 [...]

CHCESZ:
 (a) Domyślnie
 (b) Override — podaj numery
```

## PHASE 1: SCAN — Claude Code (JSONL)

Załaduj skip list z `config/sources.yaml` → `claude_code.skip_patterns`. Użyj `sampling_rates` per wybraną token strategy.

Dla każdej sesji wyciągnij:
- Data (`timestamp`), tytuł (`ai-title`), cwd (zdekodowany)
- Narzędzia użyte (`tool_use.name`)
- Skille wywołane (pattern: `"name":"Skill","input":{"skill":"..."}`)
- Powtarzające się komendy Bash (pierwsze 60 znaków)
- Czy sesja zawierała błędy/retry (sygnał frustration → SOP candidate)

## PHASE 2: SCAN — Gmail

Przez Gmail MCP (`mcp__ab46da28`), użyj `config/sources.yaml → gmail.query_spec.bootstrap`:
- Query: `(decyzja OR pipeline OR SOP OR powtarzalny OR automatyzacja OR procedura OR szablon) -label:SPAM -label:TRASH`
- Lookback: 90 dni
- SKIP: wątki z PESEL, NIP, danymi osobowymi → REDACT summary

## PHASE 3: SCAN — Slack

Przez Slack MCP (`mcp__8c5de80e`), użyj `config/sources.yaml → slack`:
- Kanały według `channel_ids` (nie nazw), lookback 90 dni
- Kanały: #general, #ai-feedback (C0AS00SNGQZ), #planer-dnia, #brand-team, #mini-granty, #full-team
- Szukaj: pytania które się powtarzają, prośby o pomoc, decyzje, frustracje
- SKIP: wiadomości z hasłami, tokenami, danymi poufnymi

## PHASE 4: SCAN — Google Drive

Przez Drive MCP (`mcp__7a8eafc1`), folder `1U10_VXe_qxoYOlrSyIpgQKXOUy-og1D-`, lookback 90 dni:
- Odnotuj: tytuły, typy (instrukcja/szablon/raport), czy sugerują powtarzalny proces

## PHASE 5: KLASYFIKACJA — rozłączne drzewo 4-krokowe

Dla każdego wykrytego wzorca/odkrycia pytaj **po kolei**:

```
1. Merytoryczny + powtarzalny + jasny input/output?
   NIE → POMIŃ (jednorazowe, meta, preferencja osobista, dane wrażliwe)
   TAK → pytanie 2

2. Wymaga ludzkiego osądu / decyzji / accountability w środku?
   TAK → SOP (Executor: Human lub Hybrid)
       → Czy krok jest AI-kreatywny? → oznacz Related skills
       → Czy krok jest deterministyczny? → oznacz Related n8n
   NIE → pytanie 3

3. Output kreatywny / wariantowy / brand voice OFF?
   TAK → Skill Backlog (WYMAGANE: ≥3 wystąpienia)
       → skills_catalog.yaml: istnieje? → [FIX], nie [NEW]
   NIE → pytanie 4

4. Jasny deterministyczny trigger + pipeline bez decyzji?
   TAK → n8n Automation (WYMAGANE: ≥2 wystąpienia)
   NIE → SOP (Executor: Human, do późniejszej dekompozycji)
```

**Progi minimalne (z config/sources.yaml → classification_thresholds):**
- SOP: ≥2 wystąpienia | Skill: ≥3 wystąpienia | n8n: ≥2 wystąpienia
- Poniżej progu → flag `candidate_{type}`, NIE zapisuj do Notion

## PHASE 5.5: DUAL-PASS + QUALITY GATES

**Pass 1 (draft):** Zbierz kandydatów w pamięci. NIE zapisuj.

**Pass 2 (weryfikacja) — checklist każdego draftu:**
```
[ ] Skip rules: nie meta (knowledge-base/WSD/etc), nie "stan skilla", nie poniżej progu
[ ] Cross-check z config/skills_catalog.yaml:
    - fuzzy match z base_off + extended_uao + extended_extra → [FIX]
    - jeśli na skip_meta → POMIŃ
[ ] Source URL = ścieżka JSONL + session ID (lub "—")
[ ] User = autor wzorca (mapuj git config email→Notion Person ID z config/notion.yaml)
[ ] Date = timestamp z JSONL (nie dziś)
[ ] Title [NEW]/[FIX]/[BUG]
[ ] Summary: liczba × + link + konkret + "Next: ___"
[ ] Jeśli Type=Skill lub n8n: Parent SOP wskazany (slug lub "—" jeśli standalone)
[ ] Occurrence count ≥ progu per typ
```

### Few-shot:

**✅ DOBRY:**
```
[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni'
Source URL: ~/.claude/projects/cwd-x/session-2026-05-11.jsonl
Summary: 5× miss w sessions 5-11.05, fix: triggerKeywords + description. Next: Wojciech dodaje do SKILL.md.
Parent SOP: —
```

**❌ ZŁE:**
- `Weekly Knowledge Scan` (meta — to ten skill)
- `[NEW] Ewidencja godzinowa` (skill istnieje → [FIX])
- `User: skanujący` dla wzorca obserwowanego u innego usera
- `Date: dziś` (powinno być timestamp z JSONL)
- Skill z 2 wystąpieniami (min=3 → POMIŃ lub flag candidate_skill)
- n8n bez error handling (obowiązkowe: retry + dead letter + alert)

---

## PHASE 5.5b: QUALITY GATES

❌ **NIE ZAPISUJ jeśli:**
- Wpis dotyczy `knowledge-base`, `weekly-discovery`, `team-knowledge-base`, `WSD`
- "Stan istniejącego skilla" bez konkretnego problemu
- Poniżej progu: Skill<3, SOP<2, n8n<2

✅ **Title prefix:** `[NEW]` nowy / `[FIX]` poprawka / `[BUG]` bug
✅ **Source URL WYMAGANE** (ścieżka JSONL + session ID, lub `—`)
✅ **User = autor wzorca, NIE skanujący** (mapuj email na Notion Person ID)
✅ **Date = data ORYGINALNEGO zdarzenia** (timestamp z JSONL), nie dziś
✅ **Parent SOP** = slug dla Skill/n8n, lub `—`
✅ **n8n MUSI mieć** Error handling (retry + dead letter + Slack alert)

---

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ) stwórz wpis w Notion Knowledge Base DB:
- Collection: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`

**Pola wspólne:**
- Title, Type, Source, Date, Week, Summary, Priority, Status: New, Scan type: Bootstrap
- User: Notion Person ID z `config/notion.yaml` (lub User name fallback)
- Source URL, Source examples (2-3 linki)
- Occurrences, Sources count, Time saved (min/week), Implementation size
- **Owner** (mapuj wg typu: SOP→autor, Skill→Wojciech, n8n→Maciek)
- **Parent SOP** (slug lub `—`)
- ROI score (auto)

**Pola dodatkowe per Type:**
- SOP: Process slug, Trigger, Inputs, Outputs, Steps, Decisions, Definition of Done, Edge cases, Executor overall, Frequency, Related skills, Related n8n
- Skill: Skill name, Description, Trigger phrases (≥5 z source), Input/Output format, Examples, Persona/style guide
- n8n: Flow name, Trigger, Data sources, Transformations, Destinations, **Error handling** (retry+dead letter+alert), Volume estimate, Manual steps remaining, **Credentials**, **Dependencies**, **Test plan**

## PHASE 6.5: GENERACJA ARTEFAKTÓW (Krok 4.5)

Dla każdego wpisu `[NEW]` zapisanego w PHASE 6 wygeneruj stronę artefaktu w odpowiedniej bazie Notion.
**Pomijaj `[FIX]` i `[BUG]`** — owner aktualizuje istniejącą stronę na podstawie sluga.

**Krok 1 — przygotuj JSON wpisu:**
Dla każdego [NEW] stwórz obiekt z polami:
```json
{
  "title":        "<pełny tytuł z prefixem [NEW]>",
  "type":         "<SOP | Skill Backlog | n8n Automation>",
  "summary":      "<summary z KB>",
  "owner":        "<owner imię>",
  "kb_entry_url": "<URL strony Notion KB>",
  "date":         "<YYYY-MM-DD>",
  "trigger":      "<trigger>",
  "priority":     "<High | Medium | Low>",
  "parent_sop":   "<slug lub null>",
  "steps":        ["<krok 1>", "..."],          // tylko SOP
  "frequency":    "<quarterly | weekly | ...>", // tylko SOP
  "description":  "<opis>",                     // tylko Skill
  "trigger_phrases": ["<fraza>", "..."],         // tylko Skill — min 5
  "data_sources": ["<system>", "..."],           // tylko n8n
  "destinations": ["<system>", "..."],           // tylko n8n
  "transformations": "<opis transformacji>",    // tylko n8n
  "error_handling":  "<opis obsługi błędów>"    // tylko n8n
}
```

**Krok 2 — wywołaj skrypt:**
```bash
cat > /tmp/kb_entry.json << 'ENTRY'
{...wypełniony obiekt z Kroku 1...}
ENTRY
python3 scripts/artifact_generator.py generate \
    --entry /tmp/kb_entry.json \
    --connectors config/connectors.yaml \
    --n8n-nodes  config/n8n_nodes.yaml \
    --date $(date +%Y-%m-%d)
```

**Krok 3 — obsłuż wynik (JSON na stdout):**
- `errors` zawiera `needs_slug` → **pomiń**, dodaj do Notes KB entry: `needs_slug: true — uzupełnij slug ręcznie`
- `warnings` → zaloguj w podsumowaniu (nieblokujące)
- `errors` puste → Krok 4

**Krok 4 — wywołaj `notion-create-pages`:**

| artifact_type | Docelowa baza Notion | Pole `Type` / select |
|---|---|---|
| `sop` | `config/notion.yaml → databases.sops` | Select: `"Wersja robocza"` |
| `skill` | `config/notion.yaml → databases.skills_backlog` | Type: `"Skill"` |
| `n8n` | `config/notion.yaml → databases.skills_backlog` | Type: `"Automation"` |

Użyj:
- `notion_fields` jako properties strony
- `body_content` jako treść strony w bloku code (język: wartość `body_language`)

**Error handling:**
- Duplikat slug → dopisz ` v2` do tytułu, dodaj note `"duplikat — sprawdź"`
- `notion-create-pages` fail → retry 1×; jeśli nadal fail → zapisz `body_content` jako komentarz do KB entry

---

## PHASE 7: CROSS-SOURCE BOOST

Zdeduplikuj odkrycia:
- Wzorzec w ≥2 źródłach → priorytet +1
- Wzorzec u ≥2 userów → dodaj "(team-wide)" do tytułu

## PHASE 8: OUTPUT

Po zapisie wydrukuj podsumowanie:

```
📊 Knowledge Base Bootstrap — [Imię] — [Data]

Przeskanowano:
  • Claude Code:   X sesji / Y odkryć
  • Gmail:         X wątków / Y odkryć
  • Slack:         X wiadomości / Y odkryć
  • Drive:         X plików / Y odkryć

🎯 Łącznie: Z odkryć → Notion
  • SOP:             N wpisów
  • Skill Backlog:   N wpisów
  • n8n Automation:  N wpisów
  • Pominięto:       N (poniżej progu / brak powtarzalności)
  • Cross-source boost: N wzorców

🏆 Top 3 priorytety:
1. [High] {tytuł} ({type}) — {1 zdanie}
2. [High] {tytuł} ({type}) — {1 zdanie}
3. [Medium] {tytuł} ({type}) — {1 zdanie}

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

## PHASE 9: POST-BOOTSTRAP

1. Wyślij Slack post do #ai-feedback (C0AS00SNGQZ) — format z SKILL.md Krok 6
2. Zaproponuj setup weekly scheduled task:
   - (a) Poniedziałek 10:00 [rekomendowane]
   - (b) Piątek 15:00
   - (c) Inny
   - (d) Nie
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap, discoveries={N}, by_type={SOP:N, Skill:N, n8n:N}, rejected={N}`
```

---

*Prompt: BOOTSTRAP_CC.md v2.2 · knowledge-base · msm-glitch/knowledge-base*
