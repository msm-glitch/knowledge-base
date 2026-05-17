# Knowledge Base — Bootstrap Chat (lifetime scan)

**Wersja:** 1.0 | **Data:** 2026-05-17 | **Tryb:** BOOTSTRAP (jednorazowy)

**Przeznaczenie:** Wklej w Claude Chat (claude.ai) jednorazowo — lifetime scan historii rozmów + Gmail + Slack + Drive. Po bootstrapie przełącz na `WEEKLY_CHAT.md`.

**Wymagania:**
- Konto claude.ai (Pro/Team)
- ⚠️ **"Search and reference chats" OBOWIĄZKOWO włączone** (Settings → Privacy)
- Dostęp do Gmail, Slack #ai-feedback, Google Drive OFF

**Czas:** ~20-30 min

---

## PROMPT BOOTSTRAP — skopiuj i wklej w Claude Chat:

```
# BOOTSTRAP KNOWLEDGE BASE v1.0 — LIFETIME SCAN (Chat)

Jestem członkiem zespołu Fundacji Our Future Foundation (OFF). Przeprowadź JEDNORAZOWY Bootstrap Knowledge Base — lifetime scan mojej historii rozmów z Claude.

## PRE-FLIGHT

Zanim zaczniesz, potwierdź:
1. Czy mam włączone "Search and reference chats"? Jeśli nie — przerwij i poproś o włączenie.
2. Moje imię i email @off.org.pl: [PODAJ SWOJE DANE]
3. Zakres: (a) Wszystkie rozmowy  (b) Tylko OFF-related  (c) Wybiórczo z datami
4. Compliance: potwierdzam auto-skip dla: Mini Granty PII, rozmowy legal/NDA

Jeśli (1)+(2)+(3)+(4) OK → kontynuuj. Inaczej → przerwij + wyjaśnij.

## PHASE 1: SCAN — Claude Chat history

Użyj "Search and reference chats" żeby przeskanować pełną historię moich rozmów.

Dla każdej rozmowy odnotuj:
- Data, temat/tytuł
- Cel zadania i wynik
- Domena: PM / Mini Granty / Marketing / Ops / Legal / Inne
- Czy zawierała PII? (Mini Granty, dane osobowe) → REDACT summary
- Czy zadanie się powtarzało w innych rozmowach?
- Skille/triggery użyte (jeśli widoczne)
- Czy Claude nie poradził sobie → potencjalna automatyzacja?

⚠️ Auto-skip:
- Rozmowy z tagiem legal/private (akta-kcs, UDIP, KRS)
- Rozmowy z NDA (PwC, Allegro, Forbes itp.) → FLAG w raporcie, nie cytuj
- Rozmowy osobiste (poza OFF) → skip lub user confirm

## PHASE 2: SCAN — Gmail

Przez Gmail MCP, szukaj wątków z ostatnich 90 dni:
- Query: `(decyzja OR pipeline OR "powtarzalny" OR automatyzacja) -label:SPAM`
- Dla każdego: temat, nadawca, czy sugeruje powtarzalny proces?
- SKIP: wątki z PESEL, NIP, danymi beneficjentów → REDACT

## PHASE 3: SCAN — Slack

Przez Slack MCP, kanały OFF z ostatnich 90 dni:
- #general, #ai-feedback, #planer-dnia, #brand-team, #mini-granty
- Szukaj: pytania które się powtarzają, frustrations, decyzje
- SKIP: hasła, tokeny

## PHASE 4: SCAN — Google Drive

Przez Drive MCP, pliki OFF zmienione w ostatnich 90 dniach:
- Odnotuj instrukcje, szablony, procedury → SOP candidates

## PHASE 5: KLASYFIKACJA

**Czy nadaje się na SOP / Skill / n8n?**

| Sygnał | Klasyfikacja |
|---|---|
| Ten sam proces ≥2× (różne rozmowy/maile/Slack) | SOP |
| Claude proszony o to samo zadanie wielokrotnie | Skill Backlog |
| Jasny trigger + sekwencja między narzędziami (Gmail→Slack→Drive) | n8n Automation |
| Jednorazowe, brak powtarzalności | POMIŃ |

Priority:
- High: ≥3 wystąpień LUB blokuje pracę
- Medium: 2 wystąpienia LUB przydatne dla ≥3 osób
- Low: 1 wystąpienie, warto zapamiętać

## PHASE 6: ZAPIS DO NOTION

Dla każdego odkrycia (Type ≠ POMIŃ) stwórz wpis:
- Notion Knowledge Base DB: `collection://b01c168b-17f2-4267-91c6-9286a34e43c0`
- Title: `{YYYY-MM-DD} · {Imię} · {Krótki opis}`
- Type: SOP | Skill Backlog | n8n Automation
- Source: [lista źródeł]
- Date: dziś, Week: `{ISO_YEAR}-W{ISO_WEEK}`
- Summary: 2-3 zdania
- Priority: High/Medium/Low, Status: New, Scan type: Bootstrap
- User: Notion Person ID z `config/notion.yaml`

## PHASE 7: OUTPUT

Po zapisie wydrukuj:
```
📊 Knowledge Base Bootstrap — [Imię] — [Data]

Przeskanowano:
  • Chat:   X rozmów / Y odkryć
  • Gmail:  X wątków / Y odkryć
  • Slack:  X wiadomości / Y odkryć
  • Drive:  X plików / Y odkryć

🎯 Łącznie: Z odkryć → Notion
  • SOP: N  • Skill: N  • n8n: N  • Pominięto: N

🏆 Top 3: 1. [High]... 2. [High]... 3. [Medium]...

📁 Notion: https://www.notion.so/3709c230152c40a2a46adbaf2b9f40b1
```

## PHASE 8: POST-BOOTSTRAP

1. Wyślij post do Slack #ai-feedback (C0AS00SNGQZ)
2. Przypomnij: ustaw przypomnienie Google Calendar co poniedziałek 10:00 z `WEEKLY_CHAT.md`
3. Zaktualizuj memory: `knowledge-base: last_run={DATE}, mode=bootstrap`
```

---

*Prompt: BOOTSTRAP_CHAT.md v1.0 · knowledge-base · msm-glitch/knowledge-base*
