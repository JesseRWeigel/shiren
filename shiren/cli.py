"""Command-line interface: shiren report | compare | audit."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from . import rubric
from .audit import audit, format_audit
from .loader import load_results
from .report import format_comparison, format_report, group_stats, split_at


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shiren", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_report = sub.add_parser("report", help="summary stats for a results.tsv")
    p_report.add_argument("results", help="path to results.tsv")

    p_compare = sub.add_parser(
        "compare", help="before/after comparison around a deployment date"
    )
    p_compare.add_argument("results", help="path to results.tsv")
    p_compare.add_argument(
        "--at", required=True, help="split moment, ISO format (e.g. 2026-05-22)"
    )

    p_audit = sub.add_parser(
        "audit", help="check orchestrator status against logged QA verdicts"
    )
    p_audit.add_argument("results", help="path to results.tsv")

    args = parser.parse_args(argv)
    records = sorted(load_results(args.results), key=lambda r: r.timestamp)

    if args.command == "report":
        print(format_report(records))
        _try_pass_rates(records)
    elif args.command == "compare":
        when = datetime.fromisoformat(args.at)
        before, after = split_at(records, when)
        print(format_comparison(before, after, args.at))
        _try_regression_verdicts(before, after)
    elif args.command == "audit":
        result = audit(records)
        print(format_audit(result))
        return 1 if result["kept_against_fail"] else 0
    return 0


def _try_pass_rates(records) -> None:
    """Render rubric-based pass rates if the rubric is implemented."""
    try:
        passes = sum(1 for r in records if rubric.is_pass(r))
    except NotImplementedError as exc:
        print(f"\n(pass rates unavailable: {exc})")
        return
    rate = 100 * passes / len(records) if records else 0.0
    print(f"\nPASS RATE: {passes}/{len(records)} ({rate:.0f}%)")


def _try_regression_verdicts(before, after) -> None:
    """Render per-task regression verdicts if the rubric is implemented."""
    b_stats = group_stats(before, lambda r: r.task)
    a_stats = group_stats(after, lambda r: r.task)
    shared = sorted(set(b_stats) & set(a_stats))
    if not shared:
        print("\n(no tasks appear on both sides of the split; nothing to judge)")
        return
    try:
        flagged = [
            task
            for task in shared
            if rubric.is_regression(
                b_stats[task]["mean_score"],
                a_stats[task]["mean_score"],
                a_stats[task]["n"],
            )
        ]
    except NotImplementedError as exc:
        print(f"\n(regression verdicts unavailable: {exc})")
        return
    if flagged:
        print(f"\nREGRESSIONS: {', '.join(flagged)}")
    else:
        print("\nREGRESSIONS: none")


if __name__ == "__main__":
    sys.exit(main())
