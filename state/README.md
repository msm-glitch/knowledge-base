# state/ — trwała pamięć knowledge-base (item #4)

Wcześniej skill działał **bez pamięci** ("BEZ SQLite / BEZ /runs/"). To powodowało dwa błędy:

1. **Subprogowe wzorce ginęły.** Skill wymaga ≥3 wystąpień. Wzorzec widziany 1× na tydzień
   przez 3 tygodnie nigdy nie zliczał się do 3 — flaga `candidate_skill` żyła tylko w pamięci
   pojedynczego runu.
2. **Każdy weekly czytał wszystko od zera** — koszt i ryzyko duplikatów.

Te dwa pliki (małe, czytelne, **commitowane** — audytowalne w git) to naprawiają.

## `candidates.json` — ledger kandydatów

Subprogowe wzorce z doliczaniem `occurrences` **między** skanami. Klucz = `"{Type}::{slug}"`
(deterministyczny). Idempotentny po `source_url` — ten sam link nie liczy się dwa razy.

```jsonc
{
  "version": 1,
  "candidates": {
    "Skill Backlog::off-x": {
      "type": "Skill Backlog", "slug": "off-x", "occurrences": 2,
      "sources": ["Claude Chat", "Slack"], "users": ["Michał"],
      "source_urls": ["url1", "url2"],
      "first_seen": "2026-05-10", "last_seen": "2026-05-17", "promoted": false
    }
  }
}
```

Gdy `occurrences` osiągnie próg (`config/sources.yaml → classification_thresholds`) →
kandydat trafia na listę `ready` → promocja do Notion → `promoted: true`.

## `watermarks.json` — od kiedy skanować per źródło

```jsonc
{ "version": 1, "sources": { "gmail": "2026-05-20T10:00:00Z", "slack": "..." } }
```

Weekly skanuje treści **nowsze niż** watermark danego źródła, potem aktualizuje znacznik.

## Użycie (skill woła przez Bash)

```bash
# dolicz wystąpienie
python3 scripts/kb_state.py record --type "Skill Backlog" --slug off-x \
    --date 2026-05-20 --source Slack --user Michał --url https://...

# kto osiągnął próg i czeka na promocję do Notion
python3 scripts/kb_state.py ready --thresholds config/sources.yaml

# oznacz jako wypromowany (po zapisie do Notion)
python3 scripts/kb_state.py promote --key "Skill Backlog::off-x"

# watermarki
python3 scripts/kb_state.py get-watermark --source gmail
python3 scripts/kb_state.py set-watermark --source gmail --ts 2026-05-20T10:00:00Z
```
