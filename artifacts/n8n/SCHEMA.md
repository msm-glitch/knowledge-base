# n8n — kontrakt zdolności (capability contract)

Specyfikacja bloku `meta` w plikach `artifacts/n8n/{slug}.json`. n8n ma **własny runtime**, więc
nie auto-generujemy w pełni działającego workflow — okablowanie węzłów i credentials to robota
człowieka po stronie n8n cloud. Warstwą maszynową jest tu **kontrakt w `meta`**, dzięki któremu
SOP może flow *zawołać* (`tool: n8n:{slug}` — patrz [`../sops/SCHEMA.md`](../sops/SCHEMA.md)) i
*zweryfikować*, nawet gdy węzły zostają `type: TBD`.

Wzorzec: [`examples/mass-send-with-tracking.json`](examples/mass-send-with-tracking.json).

## Zasada: rozdziel kontrakt od implementacji węzłów

```
┌─ nodes[] ──────────────────────┐   IMPLEMENTACJA — po stronie n8n; type:TBD = human todo
├─ meta {} ──────────────────────┤   KONTRAKT ZDOLNOŚCI — agent czyta (io, trigger, guardrails)
└────────────────────────────────┘
```

Agent **nie buduje** flow — *invokuje i ufa* mu jako zdolności. Budowa węzłów (`type: TBD` →
konkretny node + credentials) zostaje przy człowieku i jest świadomie poza zakresem auto-gen.

## Po co — czym to różni się od starego skeletonu

| Stary `meta` | Kontrakt zdolności (ten schemat) |
|---|---|
| `notion_entry`, `source_url`, `parent_sop` | + `slug` / `capability_ref` — jak SOP go woła |
| `credentials_required`, `test_plan` (proza) | + `io` typowane (binding z krokiem SOPa) |
| brak | `trigger` strukturalny + `status` (draft/deployed/active) |
| brak | `side_effects` + `guardrails` (czy nieodwracalny → bramka w SOP) |
| `test_plan` | + `verification.healthcheck` (jak agent potwierdza, że flow wstał) |

## `meta` — specyfikacja pól

| Pole | Typ | Znaczenie |
|---|---|---|
| `slug` | string (kebab-case) | == nazwa pliku; `capability_ref` = `n8n:{slug}` |
| `version` | int | Inkrementuj przy zmianie kontraktu |
| `status` | enum | `draft` (skeleton) \| `deployed` (w n8n, nieaktywny) \| `active` (działa) |
| `capability_ref` | string | `n8n:{slug}` — jak SOP go adresuje |
| `io.input` / `io.output` | list | Typowane (nazwy/typy zgodne z krokiem SOPa, który go woła) |
| `trigger` | obiekt | `{ type: cron\|webhook\|form\|db-change, spec }` |
| `side_effects` | enum | `read-only` \| `writes-internal` \| `external-send` |
| `credentials_required` | list<string> | Klucze/tokeny do dopięcia ręcznie |
| `guardrails` | obiekt | `{ autonomy, irreversible }` — `irreversible:true` → SOP doda krok do `irreversible_actions` |
| `verification.test_plan` | string | Scenariusze testowe (jak dotąd) |
| `verification.healthcheck` | string | Maszynowy sygnał, że flow żyje (np. endpoint/last_run) |
| `parent_sop` | string\|null | Slug SOPa |
| `notion_entry` / `source_url` | string | Powiązanie ze źródłem (jak dotąd) |

## `nodes[]` — skeleton (bez zmian, ale flagowany)

Węzły zostają minimalnym skeletonem (`Trigger → Source → Transform → Destination → Error
handler`). `type: TBD` to **jawny human-todo** — Maciek dopina konkretny node + credentials.
Auto-gen nie zgaduje typów węzłów ani sekretów.

## Kontrakt wołania (jak SOP/agent konsumuje flow)

```
1. SOP krok ma tool: n8n:{slug}. Runtime czyta meta z artefaktu/rejestru.
2. Sprawdź meta.status == active (inaczej: flow nie wdrożony → eskaluj do owner).
3. Zwaliduj meta.io.input vs to, co krok SOPa przekazuje.
4. Jeśli meta.guardrails.irreversible == true → wymagaj approval (spójne z SOP irreversible_actions).
5. Wywołaj flow (trigger). Po zakończeniu sprawdź meta.verification.healthcheck.
```

## Migracja ze starego skeletonu

1. Zostaw `nodes[]` bez zmian (`type: TBD` jako human-todo).
2. Rozszerz `meta`: dodaj `slug`, `version`, `status`, `capability_ref`, `io`, `trigger`,
   `side_effects`, `guardrails`.
3. Rozbij `test_plan` na `verification.{test_plan, healthcheck}`.
4. Flow `external-send` lub `irreversible: true` → upewnij się, że parent SOP ma go w
   `guardrails.irreversible_actions`.

---

*n8n capability schema v1 · knowledge-base · współbieżny z artifacts/sops/SCHEMA.md*
