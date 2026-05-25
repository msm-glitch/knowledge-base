# Knowledge Base — Diagram przepływu danych

## Hierarchia encji: SOP root → Skill/n8n sub-resources

```mermaid
graph TD
    subgraph SOP_ROOT["SOP (root entity)"]
        S["SOP: partner-reaktywacja\nExecutor: Hybrid\nFrequency: quarterly"]:::sop
    end

    subgraph SUB["Sub-resources (kroki SOPa)"]
        SK["Skill: off-reaktywacja-partnera\nParent SOP: partner-reaktywacja"]:::skill
        N1["n8n: crm-stale-partners\nParent SOP: partner-reaktywacja"]:::n8n
        N2["n8n: mass-send-with-tracking\nParent SOP: partner-reaktywacja"]:::n8n
    end

    S --> SK
    S --> N1
    S --> N2

    classDef sop fill:#e8f5e9,stroke:#388e3c,color:#333
    classDef skill fill:#ede7f6,stroke:#7b1fa2,color:#333
    classDef n8n fill:#fff3e0,stroke:#e65100,color:#333
```

SOP bez Parent SOP = **root**. Skill/n8n wskazują Parent SOP slugiem — lub `—` jeśli standalone.

---

## Główny flow (weekly + bootstrap)

```mermaid
flowchart TD
    subgraph ŹRÓDŁA["ŹRÓDŁA"]
        A1[Gmail\nwątki, decyzje, procesy]:::source
        A2[Slack\nDM, kanały, instrukcje]:::source
        A3[Google Drive\npliki, komentarze]:::source
        A4[Claude\nsesje z 7 dni / lifetime]:::source
    end

    subgraph SCAN["SCHEDULED PROMPT"]
        B["⏰ co tydzień, per osoba\nskanuje ostatnie 7 dni\n📅 pon. 10:00\n\n(lub jednorazowy Bootstrap\n— cały lifetime)"]:::scheduled
    end

    subgraph FILTER["FILTR KLASYFIKACJI"]
        C{"Rozłączne drzewo 4-krokowe:\n1) merytoryczne?\n2) ludzki osąd → SOP\n3) kreatywny output → Skill\n4) deterministyczny → n8n"}:::decision
    end

    subgraph OUTPUT["OUTPUT"]
        D1[SOPs\npowtarzalny proces\nz Decision of Done]:::sop
        D2[Skills Backlog\n≥3 wystąpienia\ntrigger phrases z source]:::skill
        D3[n8n Automations\n≥2 wystąpienia\nerror handling wymagany]:::n8n
    end

    subgraph NOTION["NOTION"]
        E["🗃️ Claude Knowledge Base\n📊 Knowledge Base DB\n(Type: SOP | Skill | n8n)\nParent SOP — relacja"]:::notion
    end

    subgraph ARTIFACTS["ARTEFAKTY (auto-gen, Krok 4.5)"]
        F1[artifacts/sops/{slug}.md\ntemplate z prior SOPs]:::sop
        F2[artifacts/n8n/{slug}.json\nworkflow skeleton]:::n8n
        F3[artifacts/skills/{slug}/SKILL.md\nfrontmatter + body]:::skill
    end

    A1 & A2 & A3 & A4 --> B
    B --> C
    C -->|TAK| D1 & D2 & D3
    D1 & D2 & D3 --> E
    E -->|"[NEW] only"| F1 & F2 & F3
    C -->|NIE / poniżej progu| G[/nic nie zapisuje\nlub candidate_flag/]

    classDef source fill:#fff3e0,stroke:#f57c00,color:#333
    classDef scheduled fill:#1a1a2e,stroke:#444,color:#fff
    classDef decision fill:#fff9c4,stroke:#f9a825,color:#333
    classDef sop fill:#e8f5e9,stroke:#388e3c,color:#333
    classDef skill fill:#ede7f6,stroke:#7b1fa2,color:#333
    classDef n8n fill:#fff3e0,stroke:#e65100,color:#333
    classDef notion fill:#e8eaf6,stroke:#3949ab,color:#333
```

---

## Sekwencja Bootstrap vs Weekly

```mermaid
sequenceDiagram
    participant U as Użytkownik OFF
    participant S as Skill knowledge-base
    participant G as Gmail MCP
    participant SL as Slack MCP
    participant D as Drive MCP
    participant N as Notion MCP

    Note over U,N: 🚀 BOOTSTRAP (jednorazowo)

    U->>S: bootstrap [imię] [email]
    S->>U: Pre-flight: klasyfikacja CWD, scope confirm
    U->>S: (a) domyślnie OK
    S->>S: Scan Claude sessions (all-time JSONL)
    S->>G: search threads (last 90d, query_spec bootstrap)
    S->>SL: search channels (last 90d, channel_ids)
    S->>D: list files (last 90d)
    S->>S: Klasyfikacja 4-krokowa: SOP | Skill | n8n | POMIŃ
    S->>S: Pass 2-4: quality gates + anti-duplicate (Notion query)
    S->>N: create pages → Knowledge Base DB
    S->>N: query SOPs DB → derive adaptive template
    S->>S: Generate artifacts (sops/.md, n8n/.json, skills/SKILL.md)
    S->>S: git commit + push (branch kb-scan/{date})
    S->>SL: post → #ai-feedback (z linkami do artefaktów)
    S->>U: Podsumowanie + setup weekly task?

    Note over U,N: 🔄 WEEKLY (co poniedziałek 10:00)

    loop Co tydzień
        S->>S: Scan last 7 days (all sources, query_spec weekly)
        S->>S: Tylko NOWE wzorce (pass anti-duplicate)
        alt ≥1 odkrycie
            S->>N: create/update pages → Knowledge Base DB
            S->>N: query SOPs DB → derive adaptive template
            S->>S: Generate artifacts dla [NEW] wpisów
            S->>S: git commit + push
            S->>SL: post → #ai-feedback (jeśli High priority)
        else 0 odkryć
            S->>U: Cicha notyfikacja "Brak nowych"
        end
    end
```

---

## Anatomia wpisu Knowledge Base

```mermaid
erDiagram
    KNOWLEDGE_BASE {
        string Title "[NEW/FIX/BUG] YYYY-MM-DD · Imię · slug"
        enum Type "SOP | Skill Backlog | n8n Automation"
        multi_select Source "Claude Code | Chat | Cowork | Gmail | Slack | Drive"
        date Date "data ostatniego wystąpienia"
        string Week "2026-W21"
        text Summary "4 zdania: co + dowód + triggers + next"
        enum Priority "High | Medium | Low"
        enum Status "New | Triaged | In Progress | Implemented | Validated | Rejected | Draft"
        person User "osoba OFF"
        text User_name_fallback "dla Krzysztofa, Roksany"
        url Source_URL "permalink do oryginału"
        url Source_examples "2-3 dodatkowe linki"
        enum Scan_type "Bootstrap | Weekly | WSD-relay"
        int Occurrences "liczba wystąpień"
        int Sources_count "liczba unikalnych źródeł"
        int Time_saved_min_week "estymata oszczędności"
        enum Implementation_size "S | M | L"
        string Owner "kto wdraża"
        string Parent_SOP "slug parent SOPa lub —"
        float ROI_score "occurrences × sources × time_saved / impl_factor"
    }

    SOP_EXTRA {
        string Process_slug "kebab-case unikalny"
        text Trigger "kiedy odpala się proces"
        text Inputs "lista wymaganych danych"
        text Outputs "lista artefaktów"
        text Steps "N. Imperatyw. Executor. Output."
        text Decisions "Decyzja → Kryterium → Decydent"
        text Definition_of_Done "checklist 3-5 pozycji"
        text Edge_cases "if X → do Y / STOP + ping"
        enum Executor_overall "Human | AI | Hybrid | Auto"
        enum Frequency "daily | weekly | monthly | quarterly | yearly | on-demand"
    }

    SKILL_EXTRA {
        string Skill_name "kebab-case"
        text Description "kontekst biznesowy 1-2 zdania"
        text Trigger_phrases "≥5 fraz z source"
        text Input_format "co user wkleja"
        text Output_format "struktura, długość, format"
        text Examples "pary input + output"
        text Persona_style_guide "brand voice OFF"
    }

    N8N_EXTRA {
        string Flow_name "kebab-case"
        text Trigger "cron / webhook / form / DB change"
        text Data_sources "API endpointy"
        text Transformations "filter / enrich / dedupe"
        text Destinations "system + akcja"
        text Error_handling "retry + dead letter + alert"
        text Volume_estimate "rekordy/tydzień"
        text Manual_steps_remaining "co zostaje przy człowieku"
        text Credentials "klucze API / tokeny"
        text Dependencies "zewnętrzne systemy"
        text Test_plan "scenariusze testowe"
    }

    SESSIONS {
        title Title
        text Summary
        checkbox Looks_like_SOP
        select Surface "Claude Code | Chat | Project"
    }

    KNOWLEDGE_BASE ||--o| SOP_EXTRA : "if Type=SOP"
    KNOWLEDGE_BASE ||--o| SKILL_EXTRA : "if Type=Skill"
    KNOWLEDGE_BASE ||--o| N8N_EXTRA : "if Type=n8n"
    KNOWLEDGE_BASE ||--o{ KNOWLEDGE_BASE : "Parent SOP (self-ref)"
    KNOWLEDGE_BASE ||--o{ SESSIONS : "Session (relation)"
```

---

## Decision tree: klasyfikacja odkrycia (rozłączny, 4-krokowy)

```mermaid
flowchart TD
    START([Wykryty wzorzec/zadanie]) --> Q0

    Q0{"1. Merytoryczny + powtarzalny\n+ jasny input/output?"}
    Q0 -->|NIE| SKIP[POMIŃ\njedno­razowe / meta /\ndane wrażliwe]
    Q0 -->|TAK| Q1

    Q1{"2. Wymaga ludzkiego\nosądu / decyzji /\naccountability?"}
    Q1 -->|TAK| SOP["Type: SOP\n(Executor: Human lub Hybrid)\n→ Related skills / n8n\n→ Definition of Done wymagany"]:::sop
    Q1 -->|NIE| Q2

    Q2{"3. Output kreatywny /\nwariantowy /\nwymaga brand voice OFF?"}
    Q2 -->|TAK| SKILL["Type: Skill Backlog\nwymagane: ≥3 wystąpienia\n→ ≥5 trigger phrases z source\n→ sprawdź skills_catalog [FIX?]"]:::skill
    Q2 -->|NIE| Q3

    Q3{"4. Jasny deterministyczny\ntrigger + pipeline\nbez punktów decyzji?"}
    Q3 -->|TAK| N8N["Type: n8n Automation\nwymagane: ≥2 wystąpienia\n→ error handling obowiązkowy\n→ Test plan wymagany"]:::n8n
    Q3 -->|NIE| SOP2["Type: SOP\n(Executor: Human)\ndo późniejszej dekompozycji"]:::sop

    SOP --> BOOST
    SKILL --> BOOST
    N8N --> BOOST
    SOP2 --> BOOST

    BOOST{"Cross-source boost:\n≥2 źródła?"}
    BOOST -->|TAK| UP["Priority +1 poziom\n+ (team-wide) w Title\njeśli ≥2 różnych userów"]
    BOOST -->|NIE| NOTION[→ Pass 3 Anti-duplicate\n→ Notion KB]
    UP --> NOTION

    classDef sop fill:#e8f5e9,stroke:#388e3c,color:#333
    classDef skill fill:#ede7f6,stroke:#7b1fa2,color:#333
    classDef n8n fill:#fff3e0,stroke:#e65100,color:#333
```

---

## Gdzie szukać odpowiedzi na pytania biznesowe

| Pytanie | Gdzie patrzeć |
|---|---|
| Jakie procesy zespołu można ustandaryzować? | Knowledge Base DB → filter Type=SOP, Status=New |
| Co warto zbudować jako skill Claude? | Knowledge Base DB → filter Type=Skill Backlog, Priority=High |
| Jakie automatyzacje n8n warto wdrożyć? | Knowledge Base DB → filter Type=n8n Automation |
| Kto ma najwięcej odkryć? | Knowledge Base DB → group by User |
| Co było High priority w tym tygodniu? | Knowledge Base DB → filter Week=bieżący, Priority=High |
| Które wzorce powtarzają się u wielu osób? | Knowledge Base DB → filter Title contains "team-wide" |
| Jaka jest historia odkryć? | Knowledge Base DB → sort by Date ASC |
| Które Skille i n8n należą do jednego procesu? | Knowledge Base DB → filter Parent SOP = {slug} |

---

*FLOW.md v1.1 · knowledge-base · msm-glitch/knowledge-base*
