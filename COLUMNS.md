# Knowledge Base — Glossary kolumn Notion

Wyjaśnienie każdej kolumny w Knowledge Base DB (`3709c230152c40a2a46adbaf2b9f40b1`).

Każda kolumna odpowiada na pytanie: **po co tu jest i jak ją czytać** (nie tylko jak ją wypełnić).

---

## Pola wspólne (wszystkie typy wpisów)

| Pole | Typ Notion | Co oznacza | Dlaczego istnieje |
|---|---|---|---|
| **Title** | text | Nagłówek z prefixem `[NEW/FIX/BUG] YYYY-MM-DD · Imię · slug — opis` | Jeden ciąg = wszystko co potrzebne do szybkiego scrollu listy: czy nowy, kogo dotyczy, czego |
| **Type** | select | `SOP` / `Skill Backlog` / `n8n Automation` | Rozłączna klasyfikacja drzewa 4-krokowego — definiuje kto jest ownerem i jakie pola są obowiązkowe |
| **Source** | multi-select | `Claude Code / Chat / Cowork / Gmail / Slack / Drive` (≥1) | Daje sygnał cross-source: ≥2 = boost priority, ≥3 = override do High |
| **Date** | date | Data **ostatniego wystąpienia wzorca w source** — NIE data skanowania | Pozwala odróżnić świeży wzorzec od historycznego; data skanowania nic nie mówi |
| **Week** | formula/text | ISO week (`2026-W21`) wyprowadzona z Date | Filtr "co znaleziono w tym tygodniu" |
| **Summary** | text | 4 zdania: 1) co + liczba × + zakres dat, 2) dowód + Source URLs, 3) Triggers obs. (tylko Skill), 4) `Next: {1 actionable krok}` | Zero ogólników — każde zdanie ma konkretne zadanie. Bez tego owner musi zgadywać co zrobić |
| **Priority** | select | `High / Medium / Low` po Pass 4 normalizacji (target: 20/50/30%) | Jeśli wszystko jest High → priorytet traci znaczenie. Normalizacja wymusza wybór |
| **Status** | select | Workflow: `New → Triaged → In Progress → Implemented → Validated`. Bocznie: `Rejected`, `Draft` | Wojciech filtruje `Status = New` w cotygodniowym przeglądzie |
| **User** | person (Notion) | Notion Person ID **autora wzorca**, NIE skanującego | Jeśli skanujący widzi problem Michała w Slacku → User = Michał (nie skanujący). Bez tego atrybucja jest błędna |
| **User name (fallback)** | text | Imię tekstem dla osób bez konta Notion | Mechanizm awaryjny. Cały team OFF ma już konta Notion (od 2026-05-29) — pole zostaje dla przypadków bez relacji (np. "WSD report") |
| **Source URL** | url | **Permalink** do oryginału. Slack: `slack_get_permalink` (NIE app_redirect). Brak → wpisz jawnie `—` | Bez URL nie da się zweryfikować wpisu — staje się "wierz mi". Każdy wpis musi mieć ślad |
| **Source examples** | text | 2-3 dodatkowe linki do innych instancji tego samego wzorca | Pokazuje "to nie pojedynczy incydent" — backup dla głównego URL |
| **Scan type** | select | `Bootstrap` (lifetime, raz) / `Weekly` (7d) / `WSD-relay` (cytat z #ai-feedback) | WSD-relay obniża Priority o 1 — bo to relay, nie nowe odkrycie |
| **Occurrences** | number | Liczba wystąpień wzorca w skanowanym okresie | Próg per typ: SOP≥2, Skill≥3, n8n≥2. Poniżej progu → flag `candidate_*`, nie zapisuj |
| **Sources count** | number | Liczba unikalnych źródeł (deduplikacja `Source` multi-select) | ≥2 → automatyczny boost Priority o 1 poziom |
| **Time saved (min/week)** | number | Estymata oszczędności po wdrożeniu (tygodniowo) | Wchodzi do ROI score. Konserwatywnie: Low=15, Medium=60, High=180 |
| **Implementation size** | select | Effort: `S`=<2h, `M`=2-8h, `L`=>8h | Faktor do ROI: S=1, M=4, L=12 |
| **Owner** | person/text | Kto wdraża (per typ — patrz tabela poniżej) | Jeśli nikt nie jest przypisany, wpis ląduje w "nie wiadomo czyje" |
| **Parent SOP** | text | Slug parent SOPa dla Skill/n8n. SOP root lub standalone: `—` | Bez tego Skille/n8n są bytami samodzielnymi — tracimy widok że to kroki większego procesu |
| **ROI score** | formula/number | `occurrences × sources × time_saved / impl_factor` | Auto-sortowanie kolejki: co bierzemy najpierw |

### Mapowanie Owner per typ wpisu

> Kanon: [`config/ownership.yaml`](config/ownership.yaml) → `owner_by_kind`. Tabela poniżej to lustro.

| Typ wpisu | Owner |
|---|---|
| `[FIX]` istniejącego skilla | owner skilli (Maciek) |
| `[BUG]` blokujący | autor wzorca + Wojciech |
| `[NEW] Skill Backlog` | owner skilli (Maciek) |
| `[NEW] n8n Automation` | n8n-admin (Maciek) |
| `[NEW] SOP` | autor wzorca |
| Team-wide (≥3 osoby) | Wojciech + Maciek |

---

## Pola SOP-specyficzne (Type = SOP)

> **Uwaga:** Lista poniżej to **starting template**. Faktyczny zestaw pól jest adaptacyjny — patrz Krok 4.5 w SKILL.md.

| Pole | Typ Notion | Co oznacza | Kiedy wypełnić |
|---|---|---|---|
| **Process slug** | text | Unikalny kebab-case (`partner-reaktywacja`) | Zawsze — używany jako filename SOP draftu |
| **Trigger** | text | Jednozdaniowy opis kiedy proces się odpala | Zawsze — bez tego SOP "jest", ale nigdy się nie uruchamia |
| **Inputs** | text | Lista czego potrzeba na wejściu: dane, dostępy, decyzje | Jeśli wymagane ≠ trywialnie z Trigger |
| **Outputs** | text | Lista artefaktów / decyzji / stanów po zakończeniu | Zawsze — Definition of Done buduje się na Outputs |
| **Steps** | text | 3-7 kroków: `N. {Imperatyw}. Executor: {Human/AI/Auto/Hybrid}. Output: {co}.` | Zawsze — bez kroków SOP to "intencja", nie procedura |
| **Decisions** | text | Punkty decyzyjne: `Decyzja: {co} → Kryterium: {jak} → Decydent: {kto}` | Jeśli executor zawiera `Human` lub `Hybrid` |
| **Definition of Done** | text | Checklist 3-5 sprawdzalnych pozycji (NIE ogólników) | Zawsze — wymusza weryfikowalność |
| **Edge cases** | text | `if X → do Y` lub `STOP + ping {kto}` | Jeśli ≥1 znana ścieżka błędu |
| **Executor target overall** | select | Dominujący wykonawca: `Human / AI / Hybrid / Auto` | Zawsze |
| **Frequency** | select | `daily / weekly / monthly / quarterly / yearly / on-demand` | Zawsze — wpływa na priorytet automatyzacji |
| **Related skills** | multi-select | Slugi Skills będących sub-resources kroków SOPa | Jeśli ≥1 krok jest kreatywny |
| **Related n8n** | multi-select | Flow n8n będące sub-resources kroków SOPa | Jeśli ≥1 krok jest deterministyczny |

---

## Pola Skill-specyficzne (Type = Skill Backlog)

| Pole | Typ Notion | Co oznacza | Notatka |
|---|---|---|---|
| **Skill name** | text | Kebab-case. Cross-check z `config/skills_catalog.yaml` | Match → wymuś `[FIX]`, nie `[NEW]` |
| **Description** | text | 1-2 zdania kontekstu biznesowego — do czego skill służy | Nie techniczny opis, tylko biznesowy |
| **Trigger phrases** | text | ≥5 fraz DOSŁOWNIE skopiowanych z source (Slack/Gmail/Chat) | Wymyślone frazy = anti-wzorzec; muszą być z dowodów |
| **Input format** | text | Co user wkleja/pisze (notatki, lista, link, brief) | |
| **Output format** | text | Co skill produkuje (struktura, długość, format) | |
| **Examples** | text | 2-3 pary `raw input → ideal output` z prawdziwych instancji | Z source, nie wymyślone |
| **Persona/style guide** | text | Brand voice OFF + odniesienie do `off-brand-voice` jeśli stosuje | |
| **Edge cases** | text | Co skill MUSI rozróżnić (VIP vs casual, program A vs B) | |
| **Related skills** | multi-select | Inne skille OFF w łańcuchu (sekwencja wywołań) | |

---

## Pola n8n-specyficzne (Type = n8n Automation)

| Pole | Typ Notion | Co oznacza | Notatka |
|---|---|---|---|
| **Flow name** | text | Kebab-case — filename JSON-a | |
| **Trigger** | text | Konkretny event: cron / webhook / form submit / DB change | Bez tego flow nie wie kiedy startować |
| **Data sources** | text | Systemy + API endpointy na wejściu | |
| **Transformations** | text | Co flow robi z danymi: filter / enrich / dedupe / map / aggregate | |
| **Destinations** | text | Gdzie ląduje output: system + akcja | |
| **Error handling** | text | **WYMAGANE**: retry strategy + dead letter + Slack alert do kogo | Bez tego flow działa, ale ciche awarie są niewidoczne |
| **Volume estimate** | text | Ile rekordów/triggerów dziennie/tygodniowo | |
| **Manual steps remaining** | text | Które kroki ZOSTAJĄ przy człowieku i dlaczego | Zawsze coś zostaje — uczciwy n8n to nie 100% automat |
| **Credentials** | text | Lista wymaganych kluczy API / tokenów / service accounts (bez wartości) | Tylko nazwy — wartości nigdy w Notion |
| **Dependencies** | text | Zewnętrzne systemy i wersje (monday.com, Google Forms, etc.) | |
| **Test plan** | text | 1-3 scenariusze testowe weryfikujące że flow działa | |
| **Related SOP** | text | Slug SOPa którego krokiem jest ten flow | Zwykle wypełnione — standalone n8n to wyjątek |
| **Related skill** | multi-select | Czy w pipeline jest call do Claude skilla | |

---

## Filtry najczęściej używane

| Cel biznesowy | Filter |
|---|---|
| Co wymaga standaryzacji teraz? | `Type = SOP, Status = New` |
| Co warto zbudować jako skill? | `Type = Skill Backlog, Priority = High` |
| Co warto zautomatyzować? | `Type = n8n Automation, Status = New` |
| Co dotyczy wielu osób? | `Title contains "team-wide"` |
| Co w tym tygodniu? | `Week = bieżący ISO week` |
| Sub-resources SOPa X? | `Parent SOP = {slug}` |
| Co Wojciech ma dziś triagować? | `Status = New, sort by ROI score DESC` |
| Co wymaga decyzji granicznej? | `Status = Draft` (z notatką "Needs review") |

---

## Anti-wzorce (czego NIE robić w kolumnach)

| Anty-wzorzec | Co zamiast |
|---|---|
| `Date = dzisiaj` (data skanowania) | Data ostatniego wystąpienia wzorca w source |
| `User = skanujący` | User = autor wzorca |
| `Source URL = pusty` | `—` jawnie, jeśli brak URL |
| `Summary = "wymaga poprawki"` | 4 zdania STRICT: co + dowód + (triggers) + Next |
| `Owner = pusty` | Mapuj per typ wpisu (tabela powyżej) |
| `Parent SOP = pusty` dla Skill/n8n | `—` jawnie (standalone) lub slug parenta |
| Skill z 2× w source | POMIŃ — flag `candidate_skill`, wróć przy 3. |
| Multi-Type w jednym wpisie | Wybierz dominujący Type; drugi aspekt w Summary |

---

*COLUMNS.md · knowledge-base v2.2 · msm-glitch/knowledge-base*
