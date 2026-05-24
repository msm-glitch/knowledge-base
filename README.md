# knowledge-base

System zbierania wiedzy operacyjnej zespołu OFF z wielu źródeł (Gmail, Slack, Google Drive, sesje Claude) i klasyfikowania odkryć jako: **SOP**, **Skill Backlog** lub **n8n Automation** — bezpośrednio do Notion.

Zastępuje i rozszerza skill `team-knowledge-base` o wieloźródłowy skan + ustrukturyzowaną klasyfikację.

---

## Jak to działa (diagram)

```
Gmail ──┐
Slack ──┤──▶ Scheduled Prompt ──▶ SOP / Skill / n8n? ──▶ Notion KB
Drive ──┤        pn. 10:00            (jeśli NIE → pomiń)
Claude ─┘      lub Bootstrap
```

Szczegółowy diagram: [`FLOW.md`](FLOW.md)

---

## Struktura repozytorium

```
knowledge-base/
├── SKILL.md                     # Główny skill — 8-krokowy proces
├── FLOW.md                      # Diagramy Mermaid przepływu danych
├── README.md                    # Ten plik
├── config/
│   ├── notion.yaml              # Notion DB IDs, user map, Slack channel
│   └── sources.yaml             # Konfiguracja źródeł + skip patterns
└── prompts/
    ├── BOOTSTRAP_CHAT.md        # Lifetime scan w Claude Chat (jednorazowo)
    ├── BOOTSTRAP_COWORK.md      # Lifetime scan w Cowork (jednorazowo)
    ├── BOOTSTRAP_CC.md          # Lifetime scan w Claude Code (jednorazowo)
    ├── WEEKLY_CHAT.md           # 7-day scan w Chat (co poniedziałek)
    ├── WEEKLY_COWORK.md         # 7-day scan w Cowork (scheduled task)
    └── WEEKLY_CC.md             # 7-day scan w Claude Code (co poniedziałek)
```

---

## Quick Start — dla każdego członka zespołu OFF

### Krok 1: Bootstrap (jednorazowo)

Wybierz swój kanał i wklej odpowiedni prompt:

| Kanał | Prompt |
|---|---|
| Claude Chat (claude.ai) | [`prompts/BOOTSTRAP_CHAT.md`](prompts/BOOTSTRAP_CHAT.md) |
| Claude Cowork | [`prompts/BOOTSTRAP_COWORK.md`](prompts/BOOTSTRAP_COWORK.md) |
| Claude Code (CLI) | [`prompts/BOOTSTRAP_CC.md`](prompts/BOOTSTRAP_CC.md) |

**Kto używa jakich kanałów:**

| Osoba | Kanały do Bootstrap |
|---|---|
| Michał | Cowork + Chat + Claude Code |
| Wojciech | Cowork + Chat + Claude Code |
| Krzysztof | Chat + Cowork + Claude Code |
| Maciek | Chat + Cowork + Claude Code |
| Kamil, Zuzanna, Natalia, Weronika, Roksana, Bartosz, Natasza | Chat + Cowork |

Wykonaj bootstrap **sekwencyjnie** w każdym kanale (jeden po drugim).

### Krok 2: Weekly (co poniedziałek 10:00)

| Kanał | Prompt | Tryb |
|---|---|---|
| Chat | [`prompts/WEEKLY_CHAT.md`](prompts/WEEKLY_CHAT.md) | Manual (przypomnienie w kalendarzu) |
| Cowork | [`prompts/WEEKLY_COWORK.md`](prompts/WEEKLY_COWORK.md) | Scheduled task (Cowork auto) |
| Claude Code | [`prompts/WEEKLY_CC.md`](prompts/WEEKLY_CC.md) | Scheduled task lub manual |

---

## Notion — bazy danych

**Parent:** 🧠 Claude Knowledge Base (`356fab98-766f-81eb-8194-f33ebeed7f51`)

| Baza | Przeznaczenie |
|---|---|
| **Knowledge Base** | Odkrycia z weekly/bootstrap — SOP, Skill, n8n |
| Sessions | Wpisy per sesja Claude (skill `team-knowledge-base`) |
| SOPs | Zatwierdzone procedury operacyjne |
| Skills Backlog | Kandydaci na nowe skille OFF |

**Knowledge Base DB:** `3709c230152c40a2a46adbaf2b9f40b1`
**Collection:** `b01c168b-17f2-4267-91c6-9286a34e43c0`

### Kluczowe filtry:

- `Type = SOP, Status = New` → co wymaga standaryzacji
- `Type = Skill Backlog, Priority = High` → co warto zbudować
- `Type = n8n Automation` → co warto zautomatyzować
- `Title contains "team-wide"` → wzorce u wielu osób

---

## Klasyfikacja odkryć — drzewo 4-krokowe (rozłączne)

Pytania zadawaj po kolei — pierwszy TAK kończy klasyfikację.

| Krok | Pytanie | TAK → | NIE → |
|---|---|---|---|
| 1 | Merytoryczne + powtarzalne + jasny input/output? | krok 2 | **Pominięto** |
| 2 | Wymaga ludzkiego osądu / decyzji / accountability? | **SOP** (Human/Hybrid) | krok 3 |
| 3 | Output kreatywny / wariantowy / brand voice OFF? | **Skill Backlog** (min ≥3×) | krok 4 |
| 4 | Jasny deterministyczny trigger + pipeline? | **n8n Automation** (min ≥2×) | **SOP** (Human) |

**Kto działA:**

| Typ | Owner | Próg |
|---|---|---|
| **SOP** | Wojciech (przegląda co tydzień) | ≥2 wystąpienia |
| **Skill Backlog** | Michał (builduje skille) | ≥3 wystąpienia |
| **n8n Automation** | Wojciech / Michał | ≥2 wystąpienia |
| **Pominięto** | — | poniżej progu lub jednorazowe |

SOP jest encją root — Skill i n8n to sub-resources kroków SOPa (pole `Parent SOP`).

---

## Compliance

- **Auto-redact:** PESEL, NIP, dane beneficjentów Mini Granty
- **Auto-skip:** sesje legal (akta-kcs, UDIP, KRS), sesje NDA
- **Stop conditions:** anti-AI clause → STOP + Wojciech (wfs@off.org.pl)
- **Privacy:** Krzysztof Chojnowski i Roksana Dziura → `User name (fallback)` (brak Notion account)

---

## Konfiguracja

Przed pierwszym użyciem wypełnij `config/notion.yaml`:
- Notion Person IDs dla każdego membera (Settings → My account → User ID)
- Sprawdź czy masz dostęp do Knowledge Base DB w Notion

---

## Eskalacja

| Problem | Kontakt |
|---|---|
| Tech (skill nie działa, API error) | Wojciech (wfs@off.org.pl) |
| Compliance (NDA, RODO) | Wojciech |
| Strategia (jak interpretować wyniki) | Michał (mmm@off.org.pl) |

---

*knowledge-base v1.1 · OFF AI v3.0 · 2026-05-19*
