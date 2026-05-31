# Skill — kontrakt zdolności (agent-consumable)

Specyfikacja frontmattera plików `artifacts/skills/{slug}/SKILL.md`. Skill jest **wołany przez
SOP** (`tool: skill:{slug}` — patrz [`../sops/SCHEMA.md`](../sops/SCHEMA.md)), więc agent musi
wiedzieć, co mu przekazać, co dostanie z powrotem, czego skillowi wolno użyć i jak sprawdzić,
że nadal działa.

Wzorzec: [`examples/off-reaktywacja-partnera/SKILL.md`](examples/off-reaktywacja-partnera/SKILL.md).

## Zasada: body zostaje prozą, frontmatter staje się kontraktem

```
┌─ frontmatter YAML ─────────────┐   KONTRAKT ZDOLNOŚCI — agent czyta (io, capabilities, evals)
├─ body Markdown ────────────────┤   INSTRUKCJA DLA LLM — prompt skilla (proza; bez zmian)
└────────────────────────────────┘
```

W odróżnieniu od SOP, body skilla **nie jest** renderem frontmattera — to instrukcja
wykonawcza dla modelu. Zmiana względem starego formatu jest tylko we frontmatterze: z
*metadanych discovery* (`name/description/triggers`) urasta w *kontrakt zdolności*.

## Po co — czym to różni się od starego skilla

| Stary frontmatter | Kontrakt zdolności (ten schemat) |
|---|---|
| `triggers` (matching LLM) | + `io` — typowany kontrakt wejścia/wyjścia (binding z krokiem SOPa) |
| brak | `capabilities` — least-privilege allowlist narzędzi (czego skillowi wolno użyć) |
| brak | `side_effects` — czy skill coś wysyła/zapisuje (kluczowe dla guardrails SOPa) |
| `Examples` (proza) | + `evals` — golden set, maszynowo sprawdzalny (samo-test po edycji) |

## Frontmatter — specyfikacja pól

### Identyfikacja + matching (jak dotąd)

| Pole | Typ | Znaczenie |
|---|---|---|
| `name` | string (kebab-case) | Slug = `tool: skill:{name}` w SOP |
| `version` | int | Inkrementuj przy zmianie kontraktu (`io`/`capabilities`) |
| `status` | enum | `draft` \| `validated` \| `implemented` |
| `description` | string | 1-2 zdania kontekstu biznesowego |
| `parent_sop` | string\|null | Slug SOPa, którego krok realizuje, lub `null` |
| `triggers` | list<string> | ≥5 fraz z source — matching dla LLM (proza, bez zmian) |

### Kontrakt I/O (binding z SOPem)

Nazwy i typy **muszą się zgadzać** z krokiem SOPa, który woła ten skill (`inputs/outputs`).

```yaml
io:
  input:
    - { name: qualified_partners, type: list<partner>, required: true }
  output:
    - { name: draft_emails, type: list<email_draft> }
```

### Capabilities + bezpieczeństwo (warstwa maszynowa)

| Pole | Typ | Znaczenie |
|---|---|---|
| `capabilities.allow` | list<tool> | Least-privilege allowlist (konwencja `tool` jak w SOP: `skill:`/`mcp:`/`script:`) |
| `capabilities.deny` | list<tool> | Jawne zakazy (np. `mcp:gmail/*` — skill drafuje, nie wysyła) |
| `side_effects` | enum | `read-only` \| `writes-internal` \| `external-send` |
| `autonomy` | enum | `autonomous` \| `supervised` \| `human-review-output` |
| `guardrails.pii_handling` | string | Domyślnie: `redact via script:scripts/compliance.py` |
| `guardrails.requires_human_review` | bool | Czy output wymaga akceptacji człowieka przed użyciem |

`side_effects` jest sygnałem dla SOPa: skill `external-send` w kroku SOPa → ten krok trafia do
`guardrails.irreversible_actions`. Skill `read-only` można odpalać swobodnie.

### Evals (golden set — samo-test)

```yaml
evals:
  - { id: 1, input_ref: "examples#1", assert: "output: ton OFF AND zawiera imię partnera AND 0 PII" }
  - { id: 2, input_ref: "examples#2", assert: "output: brak fraz zakazanych z style guide" }
```

Analog `acceptance_criteria` SOPa: pozwala agentowi/CI zweryfikować, że skill nadal działa po
edycji (zwł. `[FIX]` z triggerami) — bez ręcznego klikania.

## Body — struktura (instrukcja dla LLM, bez zmian)

`## Kontekst` · `## Input format` · `## Output format` · `## Examples` · `## Style guide` ·
`## Edge cases` · `## Related skills`. To prompt skilla — proza, nie render frontmattera.

## Kontrakt wołania (jak SOP/agent konsumuje skill)

```
1. SOP krok ma tool: skill:{name}. Runtime ładuje frontmatter.
2. Sprawdź capabilities.allow/deny — skill nie może użyć narzędzia spoza allow.
3. Zwaliduj io.input vs to, co krok SOPa przekazuje (nazwy + typy).
4. Wykonaj (body = prompt). Output zgodny z io.output.
5. Jeśli guardrails.requires_human_review == true → wstrzymaj do akceptacji.
6. (CI/okresowo) odpal evals[] → fail = skill regresował, NIE promuj do implemented.
```

## Migracja ze starego formatu

1. Zostaw `name/description/triggers` i całe body bez zmian.
2. Dodaj `io` — przepisz prozę „Input/Output format" na typowane pola (zgodne z parent SOP).
3. Dodaj `capabilities` (least-privilege) + `side_effects` + `autonomy`.
4. Przekuj `Examples` na `evals[]` z asercjami (proza zostaje w body).

---

*Skill capability schema v1 · knowledge-base · współbieżny z artifacts/sops/SCHEMA.md*
