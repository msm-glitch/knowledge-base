# Ewidencja godzin — maj 2026

**Repozytorium:** msm-glitch/knowledge-base
**Osoba:** Maciej (msm@off.org.pl)
**Źródło danych:** git log + zmienione pliki (zakres 2026-05-01 – 2026-05-31)
**Wygenerowano:** 2026-06-01

> Projekt: budowa "knowledge-base" — systemu (skill + prompty + integracja
> z Notion/Slack + skrypty), który zbiera wiedzę z kanałów i generuje
> wykonywalne artefakty: SOP-y, Skille i workflowy n8n.

> Uwaga: godziny pochodzą z momentów commitów — praca zwykle zaczyna się
> wcześniej niż pierwszy commit, więc kolumnę "zakres" traktuj jako dolne
> oszacowanie.

## Co robiłem danego dnia

| Data | Zakres (commity) | Opis pracy |
|------|------------------|------------|
| 2026-05-17 | 18:54–20:17 | **Bootstrap projektu od zera.** Założenie szkieletu knowledge-base: skill (SKILL.md), 6 promptów (BOOTSTRAP i WEEKLY w wariantach CC/Chat/Cowork), schemat bazy Notion, config źródeł i katalog skilli. Dodanie quality gates (skip rules, wymagany Source URL, atrybucja użytkownika, prefiksy [NEW]/[FIX]/[BUG]), dual-pass scan, wykrywanie środowiska zdalnego. ~1100 linii nowego kodu/dokumentacji. |
| 2026-05-18 | 16:22 | **Drobna korekta promptów.** Usunięcie bloków compliance pre-flight i przeniesienie skip rules w miejsca, gdzie faktycznie są używane (4 pliki promptów). |
| 2026-05-19 | 19:07–19:13 | **Rewizja v2.1 całej dokumentacji i configu.** Wprowadzenie 4-stopniowego drzewa decyzyjnego, hierarchii SOP/Skill/n8n, progów wystąpień (Skill≥3, n8n≥2), rozszerzonego diagramu ER (Owner/Parent_SOP/Credentials/Test_plan), per-source query specs i sampling rates. Aktualizacja SKILL.md, FLOW.md, README.md, sources.yaml i wszystkich 6 promptów. |
| 2026-05-24 | 14:07–14:26 | **Merge PR #1 + korekta configu** (konto Notion dla Maćka). Lekki dzień. |
| 2026-05-25 | 19:48 | **Krok 4.5 — auto-generowanie artefaktów.** Dodanie adaptacyjnego formatu SOP, słownika kolumn Notion (nowy COLUMNS.md, 134 linie) i logiki auto-gen w SKILL.md (PR #2). |
| 2026-05-29 | 09:38–11:58 | **Hardening v2.2.** Deterministyczny rdzeń, warstwa pamięci/stanu (state/), gate PII i compliance. Pierwsza warstwa skryptów Pythona: kb_lib.py, kb_state.py, kb_setup.py, compliance.py, metrics.py + testy (test_kb.py). Realne ID Notion/Slack w configu, ownership.yaml, owner skilli = Maciej. Duży dzień (~2000 linii, PR #3). |
| 2026-05-31 | 09:35–19:14 | **Warstwa maszynowa / agent-executable.** Wykonywalny schemat SOP (frontmatter + wzorzec + wiring generatora), analogiczne schematy dla Skill i n8n, walidator artefaktów scripts/sop_schema.py + 17 testów (test_sop_schema.py). Przykładowe artefakty (SOP reaktywacji partnera, skill, workflowy n8n), grounding na realnych node'ach n8n i funkcjach MCP, przekierowanie artefaktów krok 4.5 do Notion. PR #4 i #5. Najdłuższy dzień (~2300 linii). |

## Podsumowanie

- **Dni z aktywnością:** 7 (17, 18, 19, 24, 25, 29, 31 maja)
- **Commitów łącznie:** 27
- **Główne kamienie milowe:** bootstrap (17.05) → rewizja v2.1 (19.05) → auto-gen artefaktów (25.05) → hardening v2.2 + skrypty (29.05) → warstwa wykonywalna + walidator (31.05)

---

## Prompt do wklejenia w Cowork / Claude

> Na podstawie poniższego opisu pracy z git log za maj 2026 przygotuj
> ewidencję czasu pracy. Dla każdego dnia oszacuj liczbę przepracowanych
> godzin na podstawie zakresu commitów, liczby zmienionych plików i
> charakteru pracy (pamiętaj, że praca zaczyna się przed pierwszym
> commitem). Zestaw wynik w tabeli: Data | Liczba godzin | Opis pracy,
> i zsumuj godziny w miesiącu.
