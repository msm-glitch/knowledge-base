# artifacts/ — auto-generowane drafty (Krok 4.5) + ich cykl życia (item #7)

Skill generuje tu **drafty** z wpisów `[NEW]` w Notion (SOP/n8n/Skill). Wcześniej brakowało
zdefiniowanego cyklu życia → ryzyko: mnożenie branchy `kb-scan/*` z draftami, których nikt
nie merge'uje, i gnijące pliki. Poniżej kanon.

## Struktura

```
artifacts/
├── sops/{process_slug}.md          # SOP draft (template adaptacyjny — Krok 4.5)
├── n8n/{flow_name}.json            # n8n workflow skeleton (import do n8n cloud)
└── skills/{skill_name}/SKILL.md    # Skill draft (frontmatter + body)
```

Generujemy **tylko dla `[NEW]`** (nie `[FIX]`/`[BUG]` — te to punktowa edycja istniejącego pliku).

## Cykl życia draftu

| Stan | Co się dzieje | Kto |
|---|---|---|
| **Generated** | Skill tworzy plik na branchu `kb-scan/{YYYY-MM-DD}-{user}`, commit + push | skill |
| **In review** | Owner (per `config/ownership.yaml`) robi code review draftu | owner |
| **Merged** | Draft zaakceptowany → merge do `main`, wpis Notion `Status=Implemented` | owner |
| **Rejected** | Draft odrzucony → zamknij branch bez merge, wpis Notion `Status=Rejected` | owner |

## Polityka branchy i SLA (KANON — wcześniej brakowało)

- **Jeden branch na skan:** `kb-scan/{YYYY-MM-DD}-{user}`. NIE pushujemy draftów na `main`.
- **Review SLA: 7 dni.** Owner przegląda branch w tygodniu od utworzenia (na cotygodniowym
  triage Wojciecha, `Status=New, sort by ROI desc`).
- **Sprzątanie:** branch `kb-scan/*` bez aktywności > 30 dni → zamknij (draft trafia do
  `Status=Rejected` w Notion, branch usuń). Zapobiega gniciu.
- **Konflikt nazwy pliku:** append `-v2` do slug, NIE nadpisuj istniejącego draftu.
- **Naming:** plik = `{slug}` z wpisu Notion (`Process slug` / `Flow name` / `Skill name`).
  Brak sluga → skill pomija generację i flaguje `needs_slug` (patrz SKILL.md Krok 4.5 error handling).

## Powiązanie z Notion

Każdy draft ma w nagłówku/`meta` link do źródłowego wpisu Notion (`Source URL`) i `Parent SOP`.
Owner przy merge ustawia `Status` wpisu i (dla SOP) `Status ∈ {Validated, Implemented}`, co
zasila adaptacyjny template (Krok 4.5: ≥60% prior SOPs definiuje pola).
