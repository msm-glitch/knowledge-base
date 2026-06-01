# Ewidencja godzin — maj 2026

**Repozytorium:** msm-glitch/knowledge-base
**Osoba:** Maciej (msm@off.org.pl)
**Źródło danych:** git log (zakres 2026-05-01 – 2026-05-31)
**Wygenerowano:** 2026-06-01

> Uwaga: znaczniki czasu pochodzą z momentów commitów. Faktyczna praca nad
> danym dniem zwykle zaczyna się wcześniej niż pierwszy commit — kolumny
> "pierwszy/ostatni commit" traktuj jako dolne oszacowanie okna pracy.

## Podsumowanie dzienne

| Dzień | Pierwszy commit | Ostatni commit | Liczba commitów |
|-------|-----------------|----------------|-----------------|
| 2026-05-17 | 18:54 | 20:17 | 6 |
| 2026-05-18 | 16:22 | 16:22 | 1 |
| 2026-05-19 | 19:07 | 19:13 | 5 |
| 2026-05-24 | 14:07 | 14:26 | 2 |
| 2026-05-25 | 19:48 | 19:48 | 1 |
| 2026-05-29 | 09:38 | 11:58 | 4 |
| 2026-05-31 | 09:35 | 19:14 | 8 |

**Dni z aktywnością:** 7 (17, 18, 19, 24, 25, 29, 31 maja)
**Commitów łącznie:** 27

## Pełna lista commitów

| Data | Godzina | Hash | Opis |
|------|---------|------|------|
| 2026-05-31 | 19:14 | `4d67662` | Merge pull request #5 from msm-glitch/claude/magical-pasteur-u9L94 |
| 2026-05-31 | 16:57 | `eccb161` | grounding: realne node'y n8n + funkcje MCP zamiast TBD/zgadywania |
| 2026-05-31 | 16:31 | `0c6f604` | krok 4.5: artefakty trafiają do Notion zamiast git |
| 2026-05-31 | 09:59 | `9b2b422` | Merge: walidator artefaktów wykonywalnych (sop_schema) na main |
| 2026-05-31 | 09:52 | `a3669e1` | Walidator artefaktów wykonywalnych: scripts/sop_schema.py + 17 testów |
| 2026-05-31 | 11:43 | `e8b4026` | Merge pull request #4 from msm-glitch/claude/magical-pasteur-u9L94 |
| 2026-05-31 | 09:41 | `1bce766` | Warstwa maszynowa dla artefaktów Skill i n8n (analogicznie do SOP) |
| 2026-05-31 | 09:35 | `9d887dd` | Agent-executable SOP schema: frontmatter wykonywalny + wzorzec + wiring generatora |
| 2026-05-29 | 11:58 | `8ec034c` | Hardening v2.2: deterministyczny rdzeń, pamięć, compliance + config + README (#3) |
| 2026-05-29 | 09:55 | `a0b03ed` | Krzysztof+Roksana → pełne Notion ID; README wg template'u OFF |
| 2026-05-29 | 09:45 | `2f9e29a` | Config: realne ID (Notion+Slack), owner skilli = Maciej |
| 2026-05-29 | 09:38 | `8e0728e` | Hardening v2.2: deterministyczny rdzeń, pamięć, gate PII, spójność configu |
| 2026-05-25 | 19:48 | `6ecee4c` | Krok 4.5 (artifact auto-gen) + adaptive SOP format + Notion columns glossary (#2) |
| 2026-05-24 | 14:26 | `7a29dd5` | Update Notion account for maciek |
| 2026-05-24 | 14:07 | `4924a6f` | Merge pull request #1 from msm-glitch/claude/load-context-discovery-0lNZE |
| 2026-05-19 | 19:13 | `33f46bd` | Update prompts/ per v2.1: 4-step decision tree, progi Skill≥3/n8n≥2, Parent SOP check, Owner+nowe pola w PHASE 6, PHASE 0.5 cross-cutting concerns per kanał |
| 2026-05-19 | 19:08 | `3a0c43d` | Update README.md per v2.1: 4-step decision tree, occurrence thresholds, Parent SOP note, v1.1 |
| 2026-05-19 | 19:08 | `19efa84` | Update FLOW.md per v2.1: hierarchia SOP root diagram, 4-step decision tree, rozszerzony ER z Owner/Parent_SOP/Credentials/Test_plan |
| 2026-05-19 | 19:07 | `6655951` | Update config/sources.yaml per v2.1: per-source query specs, skill_min 1→3, n8n_min_occurrences=2, channel_ids, sampling_rates |
| 2026-05-19 | 19:07 | `e8f84f1` | Update SKILL.md per v2.1: hierarchia SOP/Skill/n8n, 4-step decision tree, 6 precedensów, nowe schematy 4A/4B/4C, anti-patterns, cross-cutting concerns |
| 2026-05-18 | 16:22 | `039649d` | Remove compliance pre-flight blocks — move skip rules to where they're used |
| 2026-05-17 | 20:17 | `506c70d` | Quality v2: semantic dedup, WSD-relay, ROI fields, anti-inflation |
| 2026-05-17 | 20:08 | `5dd75e2` | Add remote environment detection to BOOTSTRAP_CC and SKILL.md |
| 2026-05-17 | 19:42 | `3c4be01` | quality: dual-pass scan + cross-check z katalogiem skilli + few-shot examples |
| 2026-05-17 | 19:34 | `6c3b669` | quality gates: skip rules, Source URL required, User attribution, [NEW]/[FIX]/[BUG] prefix |
| 2026-05-17 | 19:13 | `2647847` | fix pre-flight: explicit stop + interactive form w wszystkich 6 promptach |
| 2026-05-17 | 18:54 | `593282d` | bootstrap knowledge-base: skill, prompts, Notion DB, config |

---

## Prompt do wklejenia w Cowork / Claude

> Na podstawie poniższej ewidencji z git log za maj 2026 przygotuj ewidencję
> czasu pracy. Dla każdego dnia z aktywnością oszacuj liczbę przepracowanych
> godzin na podstawie zakresu commitów i ich liczby/charakteru (pamiętaj, że
> praca zaczyna się przed pierwszym commitem). Zsumuj godziny w miesiącu i
> zestaw wynik w tabeli: Data | Zakres godzin | Liczba godzin | Opis pracy.
