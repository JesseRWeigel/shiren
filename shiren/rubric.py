"""Judgment lives here, in one place, on purpose.

Everything else in Shiren is arithmetic. These two functions encode what
"good" means for YOUR agent team, and that is a human decision. Implement
them and every command that renders verdicts starts working.
"""

from __future__ import annotations

from .loader import CycleResult


def is_pass(result: CycleResult) -> bool:
    """Decide whether a single cycle result counts as a pass.

    Things to weigh:
      - Score threshold: SIBT QA scores run 0-10 (crashes log negative
        penalty scores like -0.5) and the team has averaged
        around 6.6. A bar of 7.0 is aspirational; 5.0 is lenient. Where the
        bar sits determines whether pass-rate trends feel motivating or noisy.
      - Status: a high score with status "discard" means QA rejected the
        artifact anyway. Should status veto score, or should score speak
        for itself?

    Current policy (Jesse, 2026-07-03): status veto plus a score floor of 6.0,
    matching the QA agent's observed acceptance bar (historical keeps min out
    at exactly 6.0). Ratchet to 7.0 once the team clears 90% consistently.
    """
    if result.status != "keep":
        return False  # crashes and QA rejections always fail
    return result.score >= 6.0


def is_regression(before_mean: float, after_mean: float, after_n: int) -> bool:
    """Decide whether a task got worse after a model swap.

    Things to weigh:
      - Noise floor: with small sample sizes (some tasks have <10 cycles),
        a raw `after < before` check will flag phantom regressions. A minimum
        delta (e.g. 0.5 points) or a minimum sample size gate trades
        sensitivity for stability.
      - Asymmetry: a regression verdict blocks a model promotion, so a false
        positive costs you an upgrade while a false negative ships a worse
        model. Pick which mistake you'd rather make.

    Current policy (Jesse, 2026-07-03): require 3+ post-swap samples, then
    flag drops of 0.5+ points. Kept scores cluster 7.0-8.0, so half a point
    clears normal wobble. Note the low-sample behavior: fewer than 3 samples
    returns False ("not flagged"), so thin evidence does not block promotion.
    """
    if after_n < 3:
        return False  # too little evidence to flag either way
    return before_mean - after_mean >= 0.5
