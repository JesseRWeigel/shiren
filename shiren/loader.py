"""Load orchestrator results.tsv files into typed records."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class CycleResult:
    timestamp: datetime
    cycle: int
    task: str
    agent: str
    score: float  # QA score, nominally 0-10; crashes log negative penalties
    status: str  # e.g. "ratchet", "discard"
    description: str


def load_results(path: str | Path) -> list[CycleResult]:
    """Parse a results.tsv produced by the orchestrator.

    Expected columns: timestamp, cycle, task, agent, score, status, description.
    Malformed rows raise ValueError: a corrupted log should be fixed at the
    source, because silently skipping rows would bias every stat downstream.
    """
    records: list[CycleResult] = []
    with open(path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f, delimiter="\t"), start=2):
            try:
                records.append(
                    CycleResult(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        cycle=int(row["cycle"]),
                        task=row["task"],
                        agent=row["agent"],
                        score=float(row["score"]),
                        status=row["status"],
                        description=row.get("description") or "",
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_no}: malformed row {row!r}") from exc
    return records
