# scripts/ — deterministyczny rdzeń knowledge-base

Logika, która **musi być powtarzalna**, wyniesiona z promptu (gdzie LLM "liczył w głowie")
do testowalnego kodu. Te same dane wejściowe → ten sam wynik, za każdym razem.

Bez zależności zewnętrznych poza **PyYAML** (tylko walidator/CLI configu). Python 3.9+.

| Plik | Rola | Item |
|---|---|---|
| `kb_lib.py` | similarity/dedup (Pass 3), ROI score, normalizacja priorytetów (Pass 4), fuzzy match katalogu, progi | #3 |
| `compliance.py` | deterministyczny gate PII (PESEL/NIP z sumą kontrolną, IBAN, email, telefon) | #5 |
| `kb_state.py` | ledger kandydatów (akumulacja occurrences) + watermarki per źródło | #4 |
| `kb_setup.py` | walidacja kompletności configu (gate PRE-FLIGHT) + `resolve` (co/skąd uzupełnić) | #1 |
| `metrics.py` | rollup skuteczności systemu (implemented/rejected rate, High%-inflacja) | #9 |
| `tests/test_kb.py` | testy jednostkowe całego rdzenia | — |

## Jak skill ich używa (mapa na Kroki SKILL.md)

```bash
# Krok 0 (PRE-FLIGHT): gate konfiguracji — STOP jeśli exit≠0
python3 scripts/kb_setup.py validate

# Krok 1 (skan): od kiedy skanować (weekly)
python3 scripts/kb_state.py get-watermark --source gmail

# Krok 2 (compliance): twarda redakcja PRZED zapisem
echo "$summary" | python3 scripts/compliance.py redact

# Krok 3 Pass 2 ([FIX] vs [NEW]): czy nazwa istnieje w katalogu
python3 scripts/kb_lib.py catalog --name "$slug" --catalog config/skills_catalog.yaml

# Krok 3 Pass 3 (anti-duplicate): similarity draftu vs wynik Notion query
python3 scripts/kb_lib.py dedup --draft draft.json --existing notion_hits.json

# Krok 3 Pass 4 (anty-inflacja): normalizacja priorytetów
python3 scripts/kb_lib.py normalize --entries entries.json

# Krok 4 (ROI): wartość pola ROI score
python3 scripts/kb_lib.py roi --occurrences 10 --sources 2 --time-saved 120 --impl M

# akumulacja subprogowych wzorców między skanami
python3 scripts/kb_state.py record --type "Skill Backlog" --slug off-x --date 2026-05-20 \
    --source Slack --user Michał --url https://...
python3 scripts/kb_state.py ready --thresholds config/sources.yaml

# Krok 8+ (feedback loop): metryki z eksportu Notion
python3 scripts/metrics.py --file notion_export.json
```

## Testy

```bash
python3 -m unittest discover -s scripts/tests -v
```

Każdy plik ma też `--help`. Wyniki idą na stdout jako JSON (łatwe do sparsowania przez skill).
