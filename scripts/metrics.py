#!/usr/bin/env python3
"""
metrics — rollup skuteczności samego knowledge-base (item #9, feedback loop).

Bez tego nie da się stroić progów ani wiedzieć czy system działa. Liczy z
eksportu wpisów Knowledge Base DB (JSON: lista wpisów z polami Type, Status,
Priority, ROI score, Scan type, Date).

Skąd wziąć wejście: LLM odpytuje Notion (notion-query-database-view) i zrzuca
wynik do JSON, albo Notion → Export → przerób do JSON. Format wejścia:
  [ {"Type": "...", "Status": "...", "Priority": "...", "ROI score": 12,
     "Scan type": "Weekly"}, ... ]

Liczy:
  - rozkład Type / Status / Priority (czy High% mieści się w celu 20%)
  - implemented_rate = Implemented+Validated / wszystkie nie-Rejected
  - rejected_rate = Rejected / wszystkie  (proxy false-positive klasyfikacji)
  - backlog_open = New+Triaged  (ile czeka)
  - mediana/suma ROI wśród otwartych (co bierzemy najpierw)

CLI:
  python3 scripts/metrics.py --file export.json
  python3 scripts/metrics.py --file export.json --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

DONE = {"Implemented", "Validated"}
OPEN = {"New", "Triaged", "In Progress"}


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    n = len(xs)
    mid = n // 2
    return xs[mid] if n % 2 else round((xs[mid - 1] + xs[mid]) / 2, 2)


def rollup(entries: list[dict]) -> dict:
    total = len(entries)
    by_type = Counter(e.get("Type", "?") for e in entries)
    by_status = Counter(e.get("Status", "?") for e in entries)
    by_priority = Counter(e.get("Priority", "?") for e in entries)
    by_scan = Counter(e.get("Scan type", "?") for e in entries)

    non_rejected = [e for e in entries if e.get("Status") != "Rejected"]
    done = [e for e in entries if e.get("Status") in DONE]
    rejected = [e for e in entries if e.get("Status") == "Rejected"]
    open_items = [e for e in entries if e.get("Status") in OPEN]

    def roi(e):
        try:
            return float(e.get("ROI score", 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    high = by_priority.get("High", 0)
    return {
        "total": total,
        "by_type": dict(by_type),
        "by_status": dict(by_status),
        "by_priority": dict(by_priority),
        "by_scan_type": dict(by_scan),
        "high_pct": round(high / total, 3) if total else 0.0,
        "high_pct_target": 0.20,
        "high_pct_alert": (high / total > 0.35) if total else False,
        "implemented_rate": round(len(done) / len(non_rejected), 3) if non_rejected else 0.0,
        "rejected_rate": round(len(rejected) / total, 3) if total else 0.0,
        "backlog_open": len(open_items),
        "roi_open_sum": round(sum(roi(e) for e in open_items), 2),
        "roi_open_median": _median([roi(e) for e in open_items]),
    }


def render(m: dict) -> str:
    lines = [
        "📊 Knowledge Base — metryki systemu",
        "",
        f"  Wpisów łącznie      : {m['total']}",
        f"  Typy                : " + ", ".join(f"{k}={v}" for k, v in m["by_type"].items()),
        f"  Statusy             : " + ", ".join(f"{k}={v}" for k, v in m["by_status"].items()),
        f"  Priorytety          : " + ", ".join(f"{k}={v}" for k, v in m["by_priority"].items()),
        "",
        f"  High%               : {m['high_pct']:.0%}  (cel {m['high_pct_target']:.0%}"
        + ("  ⚠️ INFLACJA >35%" if m["high_pct_alert"] else "  ✅") + ")",
        f"  Implemented rate    : {m['implemented_rate']:.0%}  (Implemented+Validated / nie-Rejected)",
        f"  Rejected rate       : {m['rejected_rate']:.0%}  (proxy false-positive klasyfikacji)",
        f"  Backlog otwarty     : {m['backlog_open']}  (ROI suma {m['roi_open_sum']}, mediana {m['roi_open_median']})",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="metrics — rollup knowledge-base")
    p.add_argument("--file", help="JSON z wpisami (domyślnie stdin)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    entries = json.loads(raw)
    if isinstance(entries, dict) and "results" in entries:
        entries = entries["results"]
    m = rollup(entries)
    print(json.dumps(m, ensure_ascii=False, indent=2) if args.json else render(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
