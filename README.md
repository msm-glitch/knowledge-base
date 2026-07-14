<div align="center">

![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3500&pause=900&color=6E56CF&center=true&vCenter=true&width=640&lines=Operacyjna+wiedza+zespolu+OFF;Gmail+%C2%B7+Slack+%C2%B7+Drive+%C2%B7+Claude+-%3E+Notion;SOP+%C2%B7+Skill+%C2%B7+n8n+--+klasyfikacja+automatyczna)

# 🧠 knowledge-base

**Zbiera wiedzę operacyjną zespołu z wielu źródeł — myśli z Claude AI, klasyfikuje do Notion.**

![Claude](https://img.shields.io/badge/Claude-Sonnet%20%2F%20Opus-6E56CF?logo=anthropic&logoColor=white)
![Notion](https://img.shields.io/badge/Notion-KB%20DB-000000?logo=notion&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-skan%20%2B%20%23ai--feedback-4A154B?logo=slack&logoColor=white)
![Gmail](https://img.shields.io/badge/Gmail-skan-EA4335?logo=gmail&logoColor=white)
![Drive](https://img.shields.io/badge/Google%20Drive-skan-4285F4?logo=googledrive&logoColor=white)

</div>

---

> *Jest poniedziałek, 10:00. Skan rusza sam.*
> *Przegląda ostatnie 7 dni: maile, Slacka, Drive, sesje z Claude.*
> *Claude pyta przy każdym wzorcu: to procedura (SOP), skill, czy automatyzacja n8n?*
> *Liczy ROI, odsiewa duplikaty, redaguje PESEL-e i zapisuje do Notion.*
> *O 10:05 na #ai-feedback ląduje top 3 priorytetów.*
>
> Nic, co zespół robi powtarzalnie, nie ginie.

knowledge-base powstał z prostego problemu: wiedza operacyjna zespołu **rozłazi się po
narzędziach** — coś ustalono na Slacku, coś w mailu, coś w sesji z Claude — i nikt tego nie
spina. To narzędzie skanuje te źródła, rozpoznaje **powtarzalne** wzorce i zamienia je w
konkretne artefakty: procedury (SOP), kandydatów na skille Claude i automatyzacje n8n —
prosto do Notion. Działa wewnątrz Claude (Chat / Cowork / Code), bez własnego serwera.

---

## Jak to wygląda w praktyce

```
📊 Knowledge Base Weekly — Maciej — 2026-05-25 (W21)

Przeskanowano (7 dni):  Slack 142 · Gmail 38 · Drive 9 · Claude 17 sesji
Nowe odkrycia: 4 → Notion
  • SOP: 1   • Skill Backlog: 2   • n8n: 1   • Pominięto: 11 (poniżej progu)
  ↑ Cross-source boost: 2 wzorce w ≥2 źródłach

🏆 Top priorytety:
  1. [High] off-brand-voice — brak triggera 'podopieczni' (Skill, 5× miss)
  2. [High] Masowy outreach do MR — ten sam szablon ×10+ (n8n)
  3. [Medium] partner-reaktywacja — kwartalny proces bez SOP-a (SOP)
```

A tak wygląda pojedynczy wpis, który ląduje w Notion:

```
[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni' do triggerów
Type: Skill Backlog   Priority: High   Owner: Maciek   Parent SOP: —
Summary: Skill off-brand-voice nie odpala dla 'podopieczni'/'stypendyści' —
  5× ręczne przepisanie (5-11.05). Triggers obs.: 'napisz do podopiecznych'.
  Next: dodać 3 słowa do triggerKeywords.
ROI score: 90   Source URL: https://claude.ai/chat/abc-2026-05-11
```

---

## Funkcje

<details>
<summary><b>🌳 Klasyfikacja 4-krokowa (rozłączna)</b></summary>

Każdy wykryty wzorzec przechodzi drzewo decyzyjne — pierwszy TAK kończy:

1. Merytoryczny + powtarzalny + jasny input/output? **NIE → POMIŃ**
2. Wymaga ludzkiego osądu / decyzji? **TAK → SOP** (Human/Hybrid)
3. Output kreatywny / brand voice OFF? **TAK → Skill Backlog** (≥3 wystąpienia)
4. Deterministyczny trigger + pipeline? **TAK → n8n Automation** (≥2) / **NIE → SOP**

SOP jest encją root; Skill i n8n to sub-resources kroków SOPa (pole `Parent SOP`).

</details>

<details>
<summary><b>🔌 Skan wieloźródłowy</b></summary>

Jedno przejście obejmuje cztery źródła przez konektory MCP:
- **Gmail** — wątki, decyzje, powtarzalne procesy
- **Slack** — kanały zespołu (skan + post wyników na #ai-feedback)
- **Google Drive** — instrukcje, szablony, procedury
- **Claude** — sesje Code (JSONL) / Chat / Cowork

Tryb `bootstrap` skanuje cały lifetime jednorazowo; `weekly` tylko ostatnie 7 dni.

</details>

<details>
<summary><b>⚙️ Deterministyczny rdzeń (scripts/)</b></summary>

Logika, która musi być powtarzalna, jest w testowanym kodzie (nie „liczona w głowie"):
- **similarity / dedup** (Jaccard + nazwa skilla + user) → MERGE / FLAG / CREATE
- **ROI score** = `occurrences × sources × time_saved / impl_factor`
- **normalizacja priorytetów** (anty-inflacja: High ≤ 20%)
- **fuzzy match** do katalogu skilli → wymusza `[FIX]` zamiast `[NEW]`

`python3 -m unittest discover -s scripts/tests` — 60 testów.

</details>

<details>
<summary><b>🧠 Pamięć między skanami (state/)</b></summary>

- **Ledger kandydatów** (`state/candidates.json`) — dolicza wystąpienia subprogowych
  wzorców między skanami, więc Skill „≥3×" widziany 1×/tydzień w końcu dobije do progu.
- **Watermarki** (`state/watermarks.json`) — od kiedy skanować per źródło, żeby weekly
  nie czytał wszystkiego od nowa.

</details>

<details>
<summary><b>🔒 Compliance gate (PII)</b></summary>

Zanim cokolwiek trafi do Notion/Git, każde pole tekstowe przechodzi deterministyczną
redakcję: **PESEL** i **NIP** (z sumą kontrolną — mało false-positive), **IBAN**, email,
telefon. Wpis z danymi wysokiej pewności nie idzie dalej bez redakcji.

</details>

<details>
<summary><b>📂 Auto-generacja artefaktów + metryki</b></summary>

Z każdego `[NEW]` wpisu KB skill generuje artefakt **prosto do Notion**: SOP → `🪩 Baza SOPs`,
n8n/Skill → `🛠️ Skills Backlog` (status `Wersja robocza`/`Idea`, owner robi review i awansuje).
Typy węzłów n8n i bindingi `mcp:` są rozwiązywane z grounded katalogów (`config/n8n_nodes.yaml`,
`config/connectors.yaml`) — generator wstawia realny node/funkcję zamiast `TBD`/zgadywania.
`scripts/metrics.py` liczy skuteczność systemu (implemented vs rejected rate, inflacja High%).

</details>

---

## Architektura

```
┌──────────────────────────────────────────────────────────────┐
│  ŹRÓDŁA   Gmail · Slack · Google Drive · Claude (Code/Chat/Cowork)
└─────────────────────────┬────────────────────────────────────┘
                          │  prompt: bootstrap (lifetime) / weekly (7 dni)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  SKILL.md — proces 8-krokowy                                   │
│   0 gate configu → 1 skan(+watermark) → 2 compliance(PII)      │
│   → 3 drzewo 4-krokowe + Pass 1-4 (dedup/ROI/normalizacja)     │
│   → 4 zapis → 4.5 artefakty → 5 boost → 6 Slack → 8.5 metryki  │
└──────┬───────────────────┬───────────────────┬────────────────┘
       ▼                   ▼                   ▼
  scripts/             state/              config/
  kb_lib · compliance  candidates.json     notion · sources · ownership
  kb_state · metrics   watermarks.json     skills_catalog · n8n_nodes · connectors
  sop_schema
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  WYJŚCIE  Notion KB DB → Baza SOPs / Skills Backlog · Slack #ai-feedback │
└──────────────────────────────────────────────────────────────┘
```

**Brak własnego backendu i deployu.** knowledge-base działa wewnątrz Claude i korzysta z
konektorów MCP. Stan trzymany jest w lekkich, commitowanych plikach `state/` (bez bazy danych).

---

## Tryby uruchomienia

Skill odpala się przez wklejenie gotowego promptu z `prompts/` w odpowiednim kanale Claude:

| Tryb | Kiedy | Zakres | Prompt |
|---|---|---|---|
| `bootstrap` | jednorazowo (pierwsze użycie) | cały lifetime | `prompts/BOOTSTRAP_{CHAT,COWORK,CC}.md` |
| `weekly` | co poniedziałek 10:00 | ostatnie 7 dni | `prompts/WEEKLY_{CHAT,COWORK,CC}.md` |

| Kanał Claude | Bootstrap | Weekly |
|---|---|---|
| **Chat** (claude.ai) | `BOOTSTRAP_CHAT.md` | `WEEKLY_CHAT.md` (przypomnienie w kalendarzu) |
| **Cowork** | `BOOTSTRAP_COWORK.md` | `WEEKLY_COWORK.md` (scheduled task) |
| **Code** (CLI) | `BOOTSTRAP_CC.md` | `WEEKLY_CC.md` (scheduled task / manual) |

---

## Uruchomienie lokalne

### Wymagania

- **Python 3.9+** (rdzeń deterministyczny + walidator)
- **PyYAML** (`pip install pyyaml`)
- Dostęp do **Claude**: Chat (claude.ai) / Cowork / Code (CLI)
- Konektory **MCP**: Notion, Slack, Gmail, Google Drive (włączone w środowisku Claude)

### Kroki

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/msm-glitch/knowledge-base.git
cd knowledge-base

# 2. Zwaliduj konfigurację (gate — blokuje skan jeśli niepełna)
python3 scripts/kb_setup.py validate
python3 scripts/kb_setup.py resolve     # mówi CO i SKĄD uzupełnić

# 3. Uruchom testy rdzenia
python3 -m unittest discover -s scripts/tests -v

# 4. (opcjonalnie) sprawdź, czy skill wgra się do Claude
python3 scripts/skill_manifest.py validate

# 5. Odpal skan — wklej prompt z prompts/ w Claude
#    (najpierw bootstrap, potem co tydzień weekly)
```

### Instalacja jako skill Claude

`SKILL.md` ma frontmatter (`name` + `description`) zgodny ze specyfikacją Claude Agent Skills,
więc repo działa też jako **instalowalny skill**. Skopiuj katalog repo do skilli Claude:

```bash
# Claude Code (CLI) — skille projektowe:
mkdir -p .claude/skills/knowledge-base
cp -r SKILL.md scripts config state artifacts .claude/skills/knowledge-base/

python3 scripts/skill_manifest.py validate    # gate: frontmatter poprawny → skill się wgra
```

Gate `skill_manifest.py` waliduje manifest deterministycznie (jak `kb_setup.py` waliduje config):
`name` kebab-case ≤64 znaki, `description` ≤1024 znaki, dozwolone klucze frontmattera.

---

## Konfiguracja (`config/`)

knowledge-base **nie używa `.env`** — cała konfiguracja jest w wersjonowanych plikach YAML:

| Plik | Co konfiguruje |
|---|---|
| `config/notion.yaml` | Notion DB IDs + Person IDs zespołu (mapowanie atrybucji) |
| `config/sources.yaml` | źródła, progi, okno dedup, state, modele per pass, scan ownership, self-ingestion guard |
| `config/ownership.yaml` | **kanon** owner mappingu (kto wdraża) + eskalacja |
| `config/skills_catalog.yaml` | katalog skilli OFF — cross-check `[FIX]` vs `[NEW]` |
| `config/n8n_nodes.yaml` | grounded katalog realnych node'ów n8n per system OFF (generator wstawia typ zamiast `TBD`) |
| `config/connectors.yaml` | grounded katalog konektorów MCP + funkcji (binding `mcp:<conn>/<fn>` zamiast zgadywania) |

Walidator jest **gatem** — skan się nie zaczyna, jeśli brakuje krytycznych pól (Notion DB IDs,
Slack channel IDs dla aktywnych kanałów):

```bash
python3 scripts/kb_setup.py validate    # exit≠0 → STOP, pokaż braki
```

---

## Połączenia (MCP) i bazy Notion

Zamiast własnych integracji/OAuth, knowledge-base korzysta z konektorów MCP środowiska Claude.
Brak konektora = źródło pomijane (graceful degradation).

| Konektor | Po co |
|---|---|
| **Notion** | zapis odkryć + query anti-duplicate |
| **Slack** | skan kanałów zespołu + post wyników na `#ai-feedback` |
| **Gmail** | skan wątków (decyzje, powtarzalne procesy) |
| **Google Drive** | skan plików (instrukcje, szablony) |

**Parent:** 🧠 Claude Knowledge Base (`356fab98-766f-81eb-8194-f33ebeed7f51`)

| Baza | ID | Przeznaczenie |
|---|---|---|
| **Knowledge Base** | `3709c230152c40a2a46adbaf2b9f40b1` | Odkrycia: SOP / Skill / n8n |
| SOPs | `deaf78c2362146cea5987eceb3220227` | Zatwierdzone procedury |
| Skills Backlog | `da811c4f224b4697919d9ed82d33bf76` | Kandydaci na skille |
| Sessions | `62f940a08fb342d79fcfb809e7c7c96c` | Wpisy per sesja Claude |

Najczęstsze filtry: `Type=SOP, Status=New` · `Type=Skill Backlog, Priority=High` ·
`Type=n8n Automation` · `Title contains "team-wide"`. Pełny glossary kolumn → [`COLUMNS.md`](COLUMNS.md).

---

## Owner i progi

Kanon: [`config/ownership.yaml`](config/ownership.yaml) — przy rozbieżności config wygrywa.

| Typ | Owner (wdrożenie) | Próg wystąpień |
|---|---|---|
| **SOP** | autor wzorca (Wojciech triażuje kolejkę co tydzień) | ≥2 |
| **Skill Backlog** | Maciek (owner skilli) | ≥3 |
| **n8n Automation** | Maciek (n8n-admin) | ≥2 |
| **Pominięto** | — (ledger dolicza do progu) | poniżej progu |

---

## Compliance

- **Auto-redact (deterministyczny):** PESEL, NIP, IBAN, email, telefon — `scripts/compliance.py`
- **Auto-skip:** sesje legal (akta-kcs, UDIP, KRS), NDA, `#mini-granty` (PII beneficjentów)
- **Stop condition:** klauzula anty-AI → STOP + Wojciech (wfs@off.org.pl)

---

## Harmonogram

Strefa Europe/Warsaw, dni robocze.

| Czas | Akcja |
|---|---|
| **poniedziałek 10:00** | Weekly scan (ostatnie 7 dni) — wszystkie źródła |
| **po skanie** | Zapis do Notion + (jeśli High) post na `#ai-feedback` |
| jednorazowo | Bootstrap — pełny lifetime scan przy pierwszym użyciu |

---

## Struktura projektu

```
knowledge-base/
├── SKILL.md                  # Główny skill — proces 8-krokowy
├── FLOW.md                   # Diagramy Mermaid przepływu danych
├── COLUMNS.md                # Glossary kolumn Notion KB DB
├── config/
│   ├── notion.yaml           # Notion DB IDs + Person IDs zespołu
│   ├── sources.yaml          # Źródła, progi, dedup, state, modele, scan ownership
│   ├── ownership.yaml        # KANON owner mappingu + eskalacja
│   ├── skills_catalog.yaml   # Katalog skilli OFF (cross-check)
│   ├── n8n_nodes.yaml        # Grounded katalog node'ów n8n per system OFF
│   └── connectors.yaml       # Grounded katalog konektorów MCP + funkcji
├── scripts/                  # Deterministyczny rdzeń (Python, stdlib + PyYAML)
│   ├── kb_lib.py             # similarity/dedup, ROI, normalizacja, fuzzy match
│   ├── compliance.py         # gate PII (PESEL/NIP/IBAN/email/telefon)
│   ├── kb_state.py           # ledger kandydatów + watermarki
│   ├── kb_setup.py           # walidacja configu (gate) + resolve
│   ├── metrics.py            # rollup skuteczności systemu
│   ├── sop_schema.py         # walidacja artefaktów (binding io + SAFETY gate + grounding katalogów)
│   ├── skill_manifest.py     # gate instalowalności skilla (frontmatter name/description wg spec Claude)
│   └── tests/                # testy jednostkowe (60): test_kb.py + test_sop_schema.py + test_skill_manifest.py
├── state/                    # Trwała pamięć między skanami (commitowana)
│   ├── candidates.json
│   └── watermarks.json
├── prompts/                  # Gotowe prompty: BOOTSTRAP/WEEKLY × Chat/Cowork/CC
└── artifacts/                # Auto-gen drafts (SOP/n8n/skill) — cykl życia w README
```

---

## Wkład w projekt

Pull requesty mile widziane:

1. **Fork** repo i stwórz branch od `main`
2. Brak konektorów Notion/Slack nie blokuje developmentu rdzenia — `scripts/` działają lokalnie
3. Przed PR: `python3 -m unittest discover -s scripts/tests` musi przechodzić
4. Zmieniasz reguły (drzewo, progi, owner)? Edytuj **`config/`** — nie powielaj w docach
5. `python3 scripts/kb_setup.py validate` przed zmianami w configu
6. Zmieniasz frontmatter `SKILL.md`? `python3 scripts/skill_manifest.py validate` (gate instalowalności)

Eskalacja: **tech / compliance** → Wojciech (wfs@off.org.pl) · **strategia** → Michał (mmm@off.org.pl)

---

<div align="center">

Zbudowany dla **Fundacji OFF** · Claude AI · Notion · Python · Slack · Gmail · Google Drive

*knowledge-base v2.3 · OFF AI v3.0 · 2026-07-14*

</div>
