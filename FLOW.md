# Knowledge Base — Diagram przepływu danych

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
        C{"Czy nadaje się na:\nSOP / Skill / n8n?\n\njeśli NIE → nic nie zapisuje"}:::decision
    end

    subgraph OUTPUT["OUTPUT"]
        D1[SOPs\npowtarzalny proces\ndo ustandaryzowania]:::sop
        D2[Skills Backlog\nzadanie dla Claude'a\ndo automatyzacji]:::skill
        D3[n8n Automations\nworkflow do zbudowania\nw n8n]:::n8n
    end

    subgraph NOTION["NOTION"]
        E["🗃️ Claude Knowledge Base\n📊 Knowledge Base DB\n(Type: SOP | Skill | n8n)"]:::notion
    end

    A1 & A2 & A3 & A4 --> B
    B --> C
    C -->|TAK| D1 & D2 & D3
    D1 & D2 & D3 --> E
    C -->|NIE| F[/nic nie zapisuje/]

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
    S->>G: search threads (last 90d)
    S->>SL: search channels (last 90d)
    S->>D: list files (last 90d)
    S->>S: Klasyfikacja: SOP | Skill | n8n | POMIŃ
    S->>N: create pages → Knowledge Base DB
    S->>SL: post → #ai-feedback
    S->>U: Podsumowanie + setup weekly task?

    Note over U,N: 🔄 WEEKLY (co poniedziałek 10:00)

    loop Co tydzień
        S->>S: Scan last 7 days (all sources)
        S->>S: Tylko NOWE wzorce
        alt ≥1 odkrycie
            S->>N: create pages → Knowledge Base DB
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
        string Title "YYYY-MM-DD · Imię · Opis"
        enum Type "SOP | Skill Backlog | n8n Automation"
        multi_select Source "Claude Code | Chat | Cowork | Gmail | Slack | Drive"
        date Date "data odkrycia"
        string Week "2026-W21"
        text Summary "2-3 zdania: co to + dlaczego wdrożyć"
        enum Priority "High | Medium | Low"
        enum Status "New | Reviewed | Promoted | Rejected"
        person User "osoba OFF"
        text User_name_fallback "dla Krzysztofa, Roksany"
        url Source_URL "link do oryginału"
        enum Scan_type "Bootstrap | Weekly"
        auto_id ID "KB-001..."
    }

    SESSIONS {
        title Title
        text Summary
        checkbox Looks_like_SOP
        select Surface "Claude Code | Chat | Project"
    }

    KNOWLEDGE_BASE ||--o{ SESSIONS : "Session (relation)"
```

---

## Decision tree: klasyfikacja odkrycia

```mermaid
flowchart TD
    START([Wykryty wzorzec/zadanie]) --> Q1

    Q1{Czy ten sam proces\nwystąpił ≥2× w\nróżnych źródłach?}
    Q1 -->|TAK| SOP[Type: SOP\nPriority: Medium-High]
    Q1 -->|NIE| Q2

    Q2{Czy Claude był\nproszony o to samo\nwielorazowo?}
    Q2 -->|TAK| SKILL[Type: Skill Backlog\nPriority: Medium]
    Q2 -->|NIE| Q3

    Q3{Czy jest jasny\ntrigger + sekwencja\nmiędzy narzędziami?}
    Q3 -->|TAK| N8N[Type: n8n Automation\nPriority: zależy od trigger]
    Q3 -->|NIE| SKIP[POMIŃ\nic nie zapisuj]

    SOP --> BOOST
    SKILL --> BOOST
    N8N --> BOOST

    BOOST{Cross-source boost:\nw ≥2 źródłach?}
    BOOST -->|TAK| UP[Priority + 1 poziom\n+ znacznik team-wide]
    BOOST -->|NIE| NOTION[→ Notion KB]
    UP --> NOTION
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

---

*FLOW.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
