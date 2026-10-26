from datetime import datetime
from pathlib import Path

import pytest

from shiren.audit import audit, parse_verdict
from shiren.cli import main
from shiren.loader import CycleResult, load_results
from shiren.rubric import is_pass, is_regression

EXAMPLE = Path(__file__).parent.parent / "examples" / "sibt-results.tsv"


def rec(status="keep", score=7.0, desc="QA approved: PASS", task="t"):
    return CycleResult(datetime(2026, 3, 13), 1, task, "coder", score, status, desc)


def test_parse_verdict():
    assert parse_verdict("QA approved: FAIL") == "FAIL"
    assert parse_verdict("QA approved after retry 1: PASS") == "PASS"
    assert parse_verdict("QA rejected (attempt 2): UNKNOWN") == "UNKNOWN"
    assert parse_verdict("research phase for write-skill") is None


def test_audit_counts_disagreement():
    result = audit([rec(desc="QA approved: FAIL"), rec(), rec(desc="research phase")])
    assert result["kept_total"] == 2
    assert result["kept_against_fail"] == 1
    assert result["unjudged"] == 1


def test_rubric():
    assert is_pass(rec(score=6.0))
    assert not is_pass(rec(score=9.0, status="discard"))
    assert not is_regression(8.0, 5.0, after_n=2)
    assert is_regression(8.0, 7.5, after_n=3)
    assert not is_regression(8.0, 7.6, after_n=3)


def test_malformed_row_raises(tmp_path):
    bad = tmp_path / "r.tsv"
    bad.write_text("timestamp\tcycle\ttask\tagent\tscore\tstatus\tdescription\nnope\t1\tt\ta\tx\tkeep\t\n")
    with pytest.raises(ValueError):
        load_results(bad)


def test_example_numbers_match_readme(capsys):
    assert main(["report", str(EXAMPLE)]) == 0
    assert "PASS RATE: 78/93 (84%)" in capsys.readouterr().out
    assert main(["audit", str(EXAMPLE)]) == 1
    assert "KEPT WITH QA PASS: 5/39" in capsys.readouterr().out
