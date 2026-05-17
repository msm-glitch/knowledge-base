# Knowledge Base — Bootstrap Claude Code (lifetime scan)

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w sesji Claude Code (CLI) jednorazowo — lifetime scan wszystkich sesji terminalowych + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_CC.md`.

**Dla kogo:** Osoby używające Claude Code CLI (`claude` w terminalu) — Michał, Wojciech, Krzysztof, Maciek.

**Czas:** ~60-90 min (token strategy Medium)

---

## PROMPT BOOTSTRAP — skopiuj i wklej w sesji `claude`:

```
# BOOTSTRAP KNOWLEDGE BASE v1.0 — LIFETIME SCAN (Claude Code)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan.

Uruchom skill `knowledge-base` z repozytorium `msm-glitch/knowledge-base` w trybie `bootstrap`.

## PHASE 0: PRE-FLIGHT

**0.1 — Wykryj usera:**
- Sprawdź `git config user.email`
- Załaduj `~/.claude/projects/*/memory/user_profile.md` (jeśli istnieje)
- Zmapuj na Notion Person ID z `config/notion.yaml` → `users`
- Powiedz mi: "Wykryto użytkownika: [imię], email: [email], Notion ID: [ID lub FALLBACK]"

**0.2 — Załaduj config:**
- Odczytaj `config/notion.yaml` i `config/sources.yaml` z repo knowledge-base
- Potwierdź: "Notion Knowledge Base DB: [ID], Slack: [channel], źródła: [lista]"

**0.3 — Klasyfikuj cwd (Claude Code sessions):**
Glob `~/.claude/projects/**/*.jsonl` → zdekoduj cwd → pokaż listę:

```
PRE-FLIGHT — kandydaci do skip:

🚫 AUTO-SKIP (legal/private):
 [1] /path/to/akta-spraw — X sesji
 ...

⚠️ FLAG (NDA/confidential):
 [...]

❓ USER CONFIRM:
 [...]

✅ INCLUDE (OFF-related):
 [...]

CHCESZ:
 (a) Domyślnie
 (b) Override — podaj numery (np. "include 3" / "skip 7")
```

**0.4 — Token strategy:**
Oszacuj: Total sesji, avg size, wybierz:
- (A) Light — metadane + grep (~150K, 5 min)
- (B) Medium — + sampling 30 linii/sesja (~600K, 15 min) [DEFAULT]
- (C) Deep — full (~2M+, 60 min)

**0.5 — Scope potwierdzenie:**
Przed skanowaniem Gmail/Slack/Drive zapytaj:
"Skanować też: (a) Gmail (b) Slack (c) Google Drive (d) wszystkie (e) tylko Claude sessions"

## PHASE 1: SCAN — Claude Code (JSONL)

Przeskanuj WSZYSTKIE pliki JSONL (poza skip list) z `~/.claude/projects/`.

Dla każdej sesji wyciągnij:
- Data (`timestamp`), tytuł (`ai-title`), cwd (zdekodowany)
- Narzędzia użyte (`tool_use.name` — Bash, Edit, Read, Skill, Agent...)
- Skille wywołane (pattern: `"name":"Skill","input":{"skill":"..."}`)
- Powtarzające się komendy Bash (pierwsze 60 znaków)
- Czy sesja zawierała błędy/retry (sygnał frustration → SOP candidate)

## PHASE 2: SCAN — Gmail

Przez Gmail MCP, szukaj wątków z ostatnich 90 dni:
- Query: `(decyzja OR pipeline OR SOP OR "powtarzalny" OR automatyzacja) -label:SPAM`
- Dla każdego wątku: temat, nadawca, czy sugeruje powtarzalny proces?
- SKIP: wątki z PESEL, NIP, danymi osobowymi → REDACT summary

## PHASE 3: SCAN — Slack

Przez Slack MCP, przeszukaj kanały OFF z ostatnich 90 dni:
- Kanały: #general, #ai-feedback, #planer-dnia, #brand-team, #mini-granty, #full-team
- Szukaj: pytania które się powtarzają, prośby o pomoc, decyzje, frustracje
- SKIP: wiadomości z hasłami, tokenami, danymi poufnymi

## PHASE 4: SCAN — Google Drive

Przez Drive MCP, folder `1U10_VXe_qxoYOlrSyIpgQKXOUy-og1D-` (Weekly Skill Discovery) i parent:
- Pliki zmienione w ostatnich 90 dniach
- Odnotuj: tytuły, typy (instrukcja/szablon/raport), czy sugerują powtarzalny proces

## PHASE 5: KLASYFIKACJA

Dla każdego wykrytego wzorca/odkrycia:

Pytanie: **Czy nadaje się na SOP / Skill / n8n?**

| Sygnał | Klasyfikacja |
|---|---|
| Ten sam proces ≥2× (różne sesje/źródła) | SOP |
| Claude proszony o to samo wielokrotnie | Skill Backlog |
| Jasny trigger + sekwencja między narzędziami | n8n Automation |
| Jednorazowe, brak powtarzalności | POMIŃ |

Priority:
- High: ≥3 wystąpień LUB blokuje pracę LUB >30 min oszczędności
- Medium: 2 wystąpienia LUB przydatne dla ≥3 osób
- Low: 1 wystąpienie, warto zapamiętać

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ) stwórz wpis w Notion Knowledge Base DB:
- Collection: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Title: `{YYYY-MM-DD} · {Imię} · {Krótki opis}`
- Type: SOP | Skill Backlog | n8n Automation
- Source: [skąd pochodzi]
- Date: dziś
- Week: `{ISO_YEAR}-W{ISO_WEEK}`
- Summary: 2-3 zdania
- Priority: High/Medium/Low
- Status: New
- Scan type: Bootstrap
- User: Notion Person ID (lub User name fallback)

## PHASE 7: CROSS-SOURCE BOOST

Zdeduplikuj odkrycia:
- Wzorzec w ≥2 źródłach → priorytet +1
- Wzorzec u ≥2 userów → dodaj "(team-wide)" do tytułu

## PHASE 8: OUTPUT

Po zapisie wydrukuj podsumowanie:

```
📊 Knowledge Base Bootstrap — [Imię] — [Data]

Przeskanowano:
  • Claude Code:   X sesji / Y odkryć
  • Gmail:         X wątków / Y odkryć
  • Slack:         X wiadomości / Y odkryć
  • Drive:         X plików / Y odkryć

🎯 Łącznie: Z odkryć → Notion
  • SOP:             N wpisów
  • Skill Backlog:   N wpisów
  • n8n Automation:  N wpisów
  • Pominięto:       N
  • Cross-source boost: N wzorców

🏆 Top 3 priorytety:
1. [High] {tytuł} ({type}) — {1 zdanie}
2. [High] {tytuł} ({type}) — {1 zdanie}
3. [Medium] {tytuł} ({type}) — {1 zdanie}

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

## PHASE 9: POST-BOOTSTRAP

1. Wyślij Slack post do #ai-feedback (C0AS00SNGQZ) — format z SKILL.md Krok 6
2. Zaproponuj setup weekly scheduled task:
   - (a) Poniedziałek 10:00 [rekomendowane]
   - (b) Piątek 15:00
   - (c) Inny
   - (d) Nie
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap, discoveries={N}`
```

---

*Prompt: BOOTSTRAP_CC.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
