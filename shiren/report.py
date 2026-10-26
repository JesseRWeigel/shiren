"""Summary statistics and model-swap comparisons over cycle results."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from typing import Callable, Iterable

from .loader import CycleResult

GroupStats = dict[str, dict]


def group_stats(
    records: Iterable[CycleResult], key: Callable[[CycleResult], str]
) -> GroupStats:
    """Aggregate records by a key function (e.g. lambda r: r.agent)."""
    groups: dict[str, list[CycleResult]] = defaultdict(list)
    for r in records:
        groups[key(r)].append(r)
    return {
        name: {
            "n": len(rs),
            "mean_score": round(mean(r.score for r in rs), 2),
            "statuses": dict(Counter(r.status for r in rs)),
        }
        for name, rs in sorted(groups.items())
    }


def split_at(
    records: list[CycleResult], when: datetime
) -> tuple[list[CycleResult], list[CycleResult]]:
    """Split history into (before, after) around a deployment moment."""
    before = [r for r in records if r.timestamp < when]
    after = [r for r in records if r.timestamp >= when]
    return before, after


def format_report(records: list[CycleResult]) -> str:
    lines = [f"cycles: {len(records)}"]
    if not records:
        return lines[0]
    lines.append(
        f"span: {records[0].timestamp.date()} .. {records[-1].timestamp.date()}"
    )
    for title, key in (("BY AGENT", lambda r: r.agent), ("BY TASK", lambda r: r.task)):
        lines.append(f"\n{title}")
        for name, s in group_stats(records, key).items():
            statuses = ", ".join(f"{k}={v}" for k, v in sorted(s["statuses"].items()))
            lines.append(
                f"  {name:<28} n={s['n']:<4} mean={s['mean_score']:<5} [{statuses}]"
            )
    return "\n".join(lines)


def format_comparison(
    before: list[CycleResult], after: list[CycleResult], label: str
) -> str:
    """Per-task before/after table for a model swap or config change."""
    b_stats = group_stats(before, lambda r: r.task)
    a_stats = group_stats(after, lambda r: r.task)
    lines = [
        f"comparison at {label}: before n={len(before)}, after n={len(after)}",
        f"  {'task':<28} {'before':>8} {'after':>8} {'delta':>8}",
    ]
    for task in sorted(set(b_stats) | set(a_stats)):
        b = b_stats.get(task, {}).get("mean_score")
        a = a_stats.get(task, {}).get("mean_score")
        delta = f"{a - b:+.2f}" if b is not None and a is not None else "n/a"
        fmt = lambda v: f"{v:.2f}" if v is not None else "-"
        lines.append(f"  {task:<28} {fmt(b):>8} {fmt(a):>8} {delta:>8}")
    return "\n".join(lines)
