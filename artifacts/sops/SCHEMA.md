# SOP — schemat wykonywalny (agent-executable)

Specyfikacja formatu plików `artifacts/sops/{slug}.md`. Cel: SOP ma być **wykonywalny przez
agenta AI**, nie tylko czytelny dla człowieka. To „ostatnia mila" w drodze do fundacji
zarządzanej przez agenty — bez tego artefakt jest notatką, a nie kontraktem wykonania.

Wzorcowy artefakt: [`examples/partner-reaktywacja.md`](examples/partner-reaktywacja.md).

---

## Zasada: dwie warstwy w jednym pliku

```
┌─ frontmatter YAML ─────────────┐   warstwa MASZYNOWA — agent czyta i wykonuje
│  slug, steps[], guardrails ... │   (źródło prawdy dla runtime'u)
├─ body Markdown ────────────────┤   warstwa LUDZKA — owner robi review
│  # Trigger / Steps / DoD ...   │   (render frontmattera, czytelny dla człowieka)
└────────────────────────────────┘
```

Frontmatter jest **źródłem prawdy** dla agenta; body to jego czytelny render dla ownera.
Przy rozbieżności wygrywa frontmatter — body ma być z niego wyprowadzone.

## Po co — czym to się różni od starego SOPa

Stary format (proza: `N. {Imperatyw}. Executor: {Human|AI}. Output: {co}.`) agent może
*zinterpretować*, ale nie *wykonać deterministycznie* — brak mu bindingu do narzędzi,
ewaluowalnych kryteriów decyzji, granic władzy i kryteriów samo-weryfikacji. Ten schemat
dodaje dokładnie te brakujące elementy:

| Stary SOP (proza) | SOP wykonywalny (ten schemat) |
|---|---|
| `Executor: Human` (opisowo) | `automatable: false` + `requires_human: "{powód}"` (twarda bramka) |
| „napisz mail otwierający" | `tool: skill:off-reaktywacja-partnera` (jawny binding) |
| `Decision: fit? → Michał` | `criterion: "fit_score >= 0.6 AND program_aktywny"` (predykat) |
| `Definition of Done: checklist` | `acceptance_criteria: [...]` (maszynowo sprawdzalne) |
| brak | `guardrails` — granice władzy + bramki na akcje nieodwracalne |
| brak | `metrics` — co agent loguje po wykonaniu (pętla sprzężenia) |

---

## Frontmatter — specyfikacja pól

### Identyfikacja

| Pole | Typ | Znaczenie |
|---|---|---|
| `slug` | string (kebab-case) | Unikalny ID; równy `Process slug` w Notion |
| `version` | int | Inkrementuj przy zmianie kontraktu (steps/inputs/outputs/guardrails) |
| `status` | enum | `draft` \| `validated` \| `implemented` — lustro Notion `Status` |
| `owner` | string | Klucz z `config/ownership.yaml` / `config/notion.yaml → users` |
| `source_url` | url | Link do wpisu Notion / oryginału |
| `parent_sop` | string\|null | Slug nadrzędnego SOPa lub `null` (root) |

### Wyzwalanie

| Pole | Typ | Znaczenie |
|---|---|---|
| `trigger.type` | enum | `event` \| `schedule` \| `request` \| `webhook` |
| `trigger.spec` | string | cron / opis okna; dla `schedule`: `daily\|weekly\|monthly\|quarterly\|yearly\|on-demand` |
| `trigger.description` | string | 1 zdanie po ludzku |
| `executor_overall` | enum | `human` \| `ai` \| `auto` \| `hybrid` (dominujący) |
| `frequency` | enum | jw. (częstotliwość uruchomień) |

### Kontrakt I/O (typowany)

`inputs` / `outputs` to listy obiektów. Typowanie pozwala agentowi walidować dane między krokami.

```yaml
inputs:
  - name: stale_partners
    type: list<partner>             # prymityw lub list<...> / map<...>
    source: "mcp:monday/get_board_items_page"   # SKĄD agent to bierze (binding)
    required: true
outputs:
  - name: reactivation_emails_sent
    type: list<email_ref>
    destination: "mcp:gmail/create_draft"        # DOKĄD trafia
```

### Kroki — rdzeń wykonywalny

Każdy element `steps[]`:

| Pole | Typ | Znaczenie |
|---|---|---|
| `id` | int | Numer kroku (kolejność wykonania) |
| `action` | string | Imperatyw — co robi krok |
| `automatable` | bool | **Twarda bramka**: czy runtime może wykonać bez człowieka |
| `executor` | enum | `human` \| `ai` \| `auto` (konceptualny wykonawca) |
| `tool` | string\|null | Binding zdolności (patrz konwencja niżej); `null` = krok ludzki |
| `implements` | string | (opc.) slug sub-resource'u (skill/n8n), który realizuje ten krok |
| `requires_human` | string | (jeśli `automatable: false`) powód, dla którego potrzebny człowiek |
| `inputs` / `outputs` | list<string> | Nazwy wartości z kontraktu I/O przepływające przez krok |
| `preconditions` | list<predykat> | Warunki, które MUSZĄ być spełnione przed wykonaniem |
| `postconditions` | list<predykat> | Warunki sprawdzane po wykonaniu (samo-weryfikacja) |
| `decision` | obiekt | (jeśli krok to punkt decyzji) patrz niżej |
| `on_error` | obiekt | `{retry, backoff, escalate_to, rollback}` |

Obiekt `decision` (punkt decyzyjny):
```yaml
decision:
  criterion: "partner.fit_score >= 0.6 AND program_aktywny"   # predykat ewaluowalny
  options: [reactivate, skip, defer]
  decider: author          # kto rozstrzyga gdy automatable: false
  fallback: skip           # domyślna gałąź gdy brak rozstrzygnięcia
```

### Guardrails — granice władzy agenta

Bez tego autonomiczny agent nie ma jak wiedzieć, czego mu NIE wolno zrobić sam.

| Pole | Typ | Znaczenie |
|---|---|---|
| `autonomy_level` | enum | `autonomous` (sam) \| `supervised` (sam, ale loguje + da się cofnąć) \| `human-gated` (czeka na approval) |
| `irreversible_actions` | list<int> | `id` kroków nieodwracalnych (wysyłka, płatność, publikacja) → wymagają approval |
| `pii_handling` | string | Reguła; domyślnie: `redact via script:scripts/compliance.py przed każdym outputem` |
| `escalation` | string | Kto przy compliance/tech (klucz z ownership.yaml) |
| `anti_ai_clause` | string | Warunek STOP (np. partner pod NDA z klauzulą anty-AI) |

### Kryteria akceptacji + metryki

```yaml
acceptance_criteria:                          # maszynowo sprawdzalne — agent weryfikuje się sam
  - "reactivation_emails_sent.length == qualified_partners.length"
  - "0 maili do partnerów z decision=skip"
metrics:                                      # pętla sprzężenia — co agent loguje po runie
  log_to: "state/runs.jsonl"
  fields: [run_id, started_at, processed, human_interventions, errors, duration_s]
```

---

## Konwencja `tool` (binding zdolności)

Wartość pola `tool` (i `source`/`destination` w I/O) wskazuje zdolność, którą wywołuje krok:

| Prefiks | Znaczenie | Przykład |
|---|---|---|
| `mcp:<konektor>/<fn>` | wywołanie konektora MCP | `mcp:monday/get_board_items_page` |
| `skill:<slug>` | wywołanie skilla Claude | `skill:off-reaktywacja-partnera` |
| `n8n:<flow>` | uruchomienie workflow n8n | `n8n:crm-stale-partners` |
| `script:<ścieżka>` | deterministyczny rdzeń | `script:scripts/compliance.py` |
| `null` | krok ludzki (brak automatyzacji) | — |

> **Rozwiązywanie bindingów to zadanie runtime'u / rejestru zdolności agentów** (warstwa,
> której KB jeszcze nie ma — patrz „Czego brakuje" niżej). Konektory MCP mają w tym
> środowisku ID hashowe (np. `mcp__8c5de80e` = Slack w `config/sources.yaml`); schemat używa
> nazw logicznych, a mapowanie logiczne→konkretne ID trzyma rejestr, nie artefakt (stabilność).

## `automatable` vs `executor` — dlaczego oba

- `executor` mówi *kto konceptualnie* wykonuje (human/ai/auto) — to klasyfikacja z drzewa SOP.
- `automatable` to *twarda bramka runtime'u*: czy agent MOŻE wykonać krok teraz.

Krok może mieć `executor: ai`, ale `automatable: false`, jeśli nie istnieje jeszcze binding
(`tool`) albo skill nie jest gotowy. To czyni schemat **mapą drogową automatyzacji**: liczba
kroków `automatable: true` rośnie w czasie i jest mierzalna per SOP.

---

## Body — struktura (render dla człowieka)

```markdown
# {Title bez prefixu}

> Auto-gen {Date} · Owner: {owner} · Status: {status}

## Trigger
{trigger.description}

## Steps
{render steps[]: "N. {action} — executor: {executor} · tool: {tool} · automatable: {bool}"}

## Decisions
{render decision[]: "Decyzja → Kryterium (predykat) → Decydent → Fallback"}

## Definition of Done
{render acceptance_criteria[] jako checklist}
```

---

## Kontrakt wykonania (jak agent konsumuje SOP)

```
1. Wczytaj frontmatter. Sprawdź guardrails.anti_ai_clause → jeśli zachodzi: STOP + eskalacja.
2. Zwaliduj inputs[] (typy + dostępność source). Brak required → STOP, eskaluj do owner.
3. Dla każdego step w kolejności id:
   a. Sprawdź preconditions[]. Niespełnione → on_error (retry/escalate).
   b. Jeśli step.id ∈ guardrails.irreversible_actions LUB autonomy_level=human-gated:
        → poproś o approval ownera PRZED wykonaniem.
   c. Jeśli automatable == false:
        → przekaż człowiekowi (requires_human / decision.decider), czekaj na wynik.
      W przeciwnym razie:
        → wykonaj przez step.tool z inputs[], zbierz outputs[].
   d. Sprawdź postconditions[]. Niespełnione → on_error (retry → rollback → escalate).
4. Sprawdź acceptance_criteria[] (samo-weryfikacja). Fail → NIE oznaczaj jako done, eskaluj.
5. Zaloguj metrics.fields do metrics.log_to.
```

## Migracja ze starego formatu (proza → wykonywalny)

1. Przenieś nagłówek (`Owner`, `Frequency`, `Executor`, `Source`) do frontmattera.
2. Każdy krok prozą → element `steps[]`. **Domyślnie `automatable: false`** dopóki nie znasz
   `tool` — nie zgaduj bindingu.
3. Krok `Executor: Human` → `automatable: false` + `requires_human`.
4. Krok wskazujący skill/n8n (Related skills / Related n8n) → `tool: skill:{slug}` / `n8n:{slug}`.
5. Akcja zewnętrzna/nieodwracalna (wysyłka, płatność, publikacja) → dodaj `id` do
   `guardrails.irreversible_actions`.
6. `Definition of Done` → `acceptance_criteria[]` jako predykaty (nie ogólniki).

## Walidacja (planowane)

Lekki walidator `scripts/` (wzorem `kb_setup.py`) sprawdzi: unikalność `slug`, spójność
referencji `inputs/outputs` między krokami, że każde `id ∈ irreversible_actions` istnieje w
`steps[]`, i że krok `automatable: true` ma niepusty `tool`. Do czasu jego dodania — review
ownera wg kontraktu wyżej.

---

*SOP execution schema v1 · knowledge-base · msm-glitch/knowledge-base*
