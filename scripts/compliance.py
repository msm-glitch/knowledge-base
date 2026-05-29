#!/usr/bin/env python3
"""
compliance — deterministyczny gate PII dla knowledge-base (Krok 2 SKILL.md).

Zamiast "LLM sprawdzi czy są dane osobowe" — twarda, powtarzalna redakcja
zanim COKOLWIEK trafi do Notion / Git. To gate MUST-PASS: jeśli `scan()`
zwróci znaleziska o wysokiej pewności (PESEL/NIP/IBAN), wpis nie idzie dalej
bez redakcji.

Wykrywa:
  - PESEL  — 11 cyfr z poprawną sumą kontrolną (wysoka pewność)
  - NIP    — 10 cyfr z poprawną sumą kontrolną (wysoka pewność)
  - IBAN PL — PL + 26 cyfr (wysoka pewność)
  - email  — (średnia pewność)
  - telefon PL — +48 / 9 cyfr w formacie xxx-xxx-xxx (średnia pewność)

Świadomie NIE redagujemy każdej 11-cyfrowej liczby (np. timestampy) — tylko
te z poprawną sumą kontrolną PESEL/NIP, żeby ograniczyć false-positive.

Tylko stdlib.

CLI:
  echo "tekst" | python3 scripts/compliance.py redact
  python3 scripts/compliance.py scan --file plik.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys

HIGH_CONFIDENCE = {"PESEL", "NIP", "IBAN"}

_PESEL_W = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
_NIP_W = [6, 5, 7, 2, 3, 4, 5, 6, 7]


def pesel_valid(digits: str) -> bool:
    if not re.fullmatch(r"\d{11}", digits):
        return False
    # walidacja daty (miesiąc kodowany ze stuleciem) — luźna, by nie odrzucać
    s = sum(int(d) * w for d, w in zip(digits, _PESEL_W))
    control = (10 - (s % 10)) % 10
    return control == int(digits[10])


def nip_valid(digits: str) -> bool:
    if not re.fullmatch(r"\d{10}", digits):
        return False
    s = sum(int(d) * w for d, w in zip(digits[:9], _NIP_W))
    control = s % 11
    return control != 10 and control == int(digits[9])


def _iban_pl_valid(s: str) -> bool:
    compact = s.replace(" ", "")
    if not re.fullmatch(r"PL\d{26}", compact, re.IGNORECASE):
        return False
    # przeniesienie 4 znaków na koniec + zamiana liter na cyfry (A=10..)
    rearranged = compact[4:] + compact[:4]
    num = "".join(str(int(ch, 36)) if ch.isalpha() else ch for ch in rearranged)
    return int(num) % 97 == 1


# kandydaci: ciągi cyfr (z opcjonalnymi separatorami) o właściwej długości
_DIGIT_RUN = re.compile(r"(?<!\d)(\d[\d \-]{8,32}\d)(?!\d)")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?<!\d)(?:\+48[\s-]?)?(?:\d{3}[\s-]\d{3}[\s-]\d{3})(?!\d)")
_IBAN = re.compile(r"\bPL[\s]?(?:\d[\s]?){26}\b", re.IGNORECASE)


def scan(text: str) -> list[dict]:
    """Zwraca listę znalezisk [{type, value, start, end, confidence}] bez modyfikacji."""
    text = text or ""
    found: list[dict] = []
    spans: list[tuple[int, int]] = []

    def overlaps(a, b):
        return any(not (b <= s or a >= e) for s, e in spans)

    for m in _IBAN.finditer(text):
        if _iban_pl_valid(m.group(0)):
            found.append({"type": "IBAN", "value": m.group(0), "start": m.start(),
                          "end": m.end(), "confidence": "high"})
            spans.append((m.start(), m.end()))

    # Telefon PRZED ciągiem cyfrowym: '+48 501 602 703' (11 cyfr) potrafi przypadkiem
    # przejść sumę kontrolną PESEL. Grupowanie 3-3-3 / prefiks +48 to wyższa precyzja,
    # więc rezerwujemy ten span zanim zajmie go detektor PESEL/NIP.
    for m in _PHONE.finditer(text):
        if overlaps(m.start(), m.end()):
            continue
        found.append({"type": "PHONE", "value": m.group(0), "start": m.start(),
                      "end": m.end(), "confidence": "medium"})
        spans.append((m.start(), m.end()))

    for m in _DIGIT_RUN.finditer(text):
        if overlaps(m.start(), m.end()):
            continue
        raw = re.sub(r"[\s-]", "", m.group(1))
        if len(raw) == 11 and pesel_valid(raw):
            found.append({"type": "PESEL", "value": m.group(1), "start": m.start(),
                          "end": m.end(), "confidence": "high"})
            spans.append((m.start(), m.end()))
        elif len(raw) == 10 and nip_valid(raw):
            found.append({"type": "NIP", "value": m.group(1), "start": m.start(),
                          "end": m.end(), "confidence": "high"})
            spans.append((m.start(), m.end()))

    for m in _EMAIL.finditer(text):
        if overlaps(m.start(), m.end()):
            continue
        found.append({"type": "EMAIL", "value": m.group(0), "start": m.start(),
                      "end": m.end(), "confidence": "medium"})
        spans.append((m.start(), m.end()))

    return sorted(found, key=lambda f: f["start"])


def redact(text: str) -> tuple[str, list[dict]]:
    """Zwraca (tekst_z_redakcją, znaleziska). Zastępuje wartości tokenami [REDACTED:TYP]."""
    findings = scan(text)
    if not findings:
        return text, []
    out = []
    last = 0
    for f in findings:
        out.append(text[last:f["start"]])
        out.append(f"[REDACTED:{f['type']}]")
        last = f["end"]
    out.append(text[last:])
    return "".join(out), findings


def must_block(text: str) -> bool:
    """True jeśli tekst zawiera dane wysokiej pewności (PESEL/NIP/IBAN) —
    wpis NIE może iść do Notion/Git bez redakcji."""
    return any(f["type"] in HIGH_CONFIDENCE for f in scan(text))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="compliance — gate PII")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("redact", "scan"):
        sp = sub.add_parser(name)
        sp.add_argument("--file", help="plik wejściowy (domyślnie stdin)")
    args = p.parse_args(argv)

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()

    if args.cmd == "scan":
        findings = scan(text)
        print(json.dumps({"findings": findings, "must_block": must_block(text)},
                         ensure_ascii=False, indent=2))
    else:
        red, findings = redact(text)
        sys.stdout.write(red)
        if findings:
            sys.stderr.write(f"\n[compliance] zredagowano {len(findings)} znalezisk: "
                             + ", ".join(sorted({f['type'] for f in findings})) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
