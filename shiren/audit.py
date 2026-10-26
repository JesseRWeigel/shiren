"""Check that the orchestrator's status agrees with the QA verdict it logged.

A results log has two opinions about each cycle: the `status` the orchestrator
acted on (keep, discard, crash) and the verdict the QA agent wrote into the
description ("QA approved: FAIL"). When those disagree, any pass rate computed
from status alone is measuring the orchestrator, not the work.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from .loader import CycleResult

_VERDICT = re.compile(r"\bQA (approved|rejected)\b.*:\s*(PASS|FAIL|UNKNOWN)\s*$")


def parse_verdict(description: str) -> str | None:
    """Return PASS, FAIL or UNKNOWN from a QA line, or None for non-QA rows."""
    m = _VERDICT.search(description)
    return m.group(2) if m else None


def audit(records: Iterable[CycleResult]) -> dict:
    """Cross-tabulate orchestrator status against the logged QA verdict."""
    table: Counter[tuple[str, str]] = Counter()
    unjudged = 0
    for r in records:
        verdict = parse_verdict(r.description)
        if verdict is None:
            unjudged += 1
        else:
            table[(r.status, verdict)] += 1
    kept = {v: n for (s, v), n in table.items() if s == "keep"}
    return {
        "table": dict(table),
        "unjudged": unjudged,
        "kept_total": sum(kept.values()),
        "kept_against_fail": kept.get("FAIL", 0),
        "kept_unknown": kept.get("UNKNOWN", 0),
        "kept_pass": kept.get("PASS", 0),
    }


def format_audit(result: dict) -> str:
    lines = ["STATUS vs QA VERDICT"]
    for (status, verdict), n in sorted(result["table"].items()):
        lines.append(f"  {status:<10} {verdict:<8} {n}")
    lines.append(f"  (rows with no QA verdict: {result['unjudged']})")
    total = result["kept_total"]
    if total:
        lines.append(
            f"\nKEPT WITH QA PASS: {result['kept_pass']}/{total}"
            f"  (FAIL: {result['kept_against_fail']}, UNKNOWN: {result['kept_unknown']})"
        )
        if result["kept_against_fail"]:
            lines.append(
                "WARNING: kept cycles whose QA verdict says FAIL. The gate and the "
                "reviewer disagree, so a status-based pass rate is not trustworthy."
            )
    return "\n".join(lines)
