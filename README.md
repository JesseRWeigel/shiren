# Shiren (試練)

An eval harness for autonomous agent teams. It reads an orchestrator's run log and tells you how the agents did, whether a model swap made them worse, and whether the log itself can be trusted.

## Why the third part matters

I ran it on 93 cycles from my own 5-agent team (local models, one RTX 5090). The headline came out at **84% pass rate**. Then `shiren audit` compared the orchestrator's keep/discard decision against the verdict the QA agent actually wrote:

```
KEPT WITH QA PASS: 5/39  (FAIL: 28, UNKNOWN: 6)
```

The gate decided on the numeric score alone and never read the reviewer's verdict. On 28 of 39 kept cycles, the reviewer's text said FAIL. The verdict parser was a crude substring match, so not every one of those is a real failure, but the two signals disagreed far too often for 84% to mean anything. That number measured the orchestrator, not the work.

## Usage

```bash
pip install -e .
shiren report examples/sibt-results.tsv                 # per-agent and per-task stats, pass rate
shiren compare examples/sibt-results.tsv --at 2026-04-01  # before/after a model swap, per task
shiren audit examples/sibt-results.tsv                  # status vs logged QA verdict; exits 1 on disagreement
```

Input is a TSV with columns `timestamp, cycle, task, agent, score, status, description`. Malformed rows raise instead of being skipped, since silently dropping rows biases every number downstream.

## Rubric

Pass and regression rules live in `shiren/rubric.py`, in one place on purpose:

- **Pass:** status is `keep` and score is at least 6.0.
- **Regression:** at least 3 samples after the swap and a drop of 0.5 points or more. Thinner evidence never blocks a promotion.

## Limits

The example log is small: 93 rows, 79 of them from a single day. Treat its numbers as a demonstration of the method.

## Tests

```bash
pip install -e '.[test]' && pytest
```

MIT licensed.
