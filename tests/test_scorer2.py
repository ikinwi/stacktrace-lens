"""Tests for stacktrace_lens.scorer2 and scorer2_cmd."""
from __future__ import annotations

import argparse
import io

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer2 import (
    ScoreReport2,
    ScoredFrame2,
    _base_score,
    score_frames,
)
from stacktrace_lens.scorer2_cmd import scorer2_command, _build_subparser


def _frame(filename: str = "app/main.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# scorer2 unit tests
# ---------------------------------------------------------------------------

def test_score_frames_returns_report():
    report = score_frames(_trace(_frame()))
    assert isinstance(report, ScoreReport2)


def test_report_frames_are_scored_frames():
    report = score_frames(_trace(_frame()))
    assert all(isinstance(f, ScoredFrame2) for f in report.frames)


def test_frame_count_matches_trace():
    trace = _trace(_frame(), _frame("other.py", "handle"))
    report = score_frames(trace)
    assert report.count == 2


def test_noise_frame_has_low_score():
    noise = _frame(filename="/usr/lib/python3.11/threading.py", function="_bootstrap")
    score = _base_score(noise)
    assert score <= 0.2


def test_user_frame_has_higher_score_than_noise():
    user = _frame(filename="app/service.py", function="process")
    noise = _frame(filename="/usr/lib/python3.11/abc.py", function="_call")
    assert _base_score(user) > _base_score(noise)


def test_score_capped_at_one():
    f = _frame(filename="app/main.py", function="main")
    assert _base_score(f) <= 1.0


def test_top_returns_n_frames():
    frames = [_frame(f"mod{i}.py") for i in range(6)]
    report = score_frames(_trace(*frames))
    assert len(report.top(3)) == 3


def test_highest_returns_none_for_empty_report():
    report = ScoreReport2(frames=[])
    assert report.highest() is None


def test_highest_returns_max_scored_frame():
    trace = _trace(
        _frame("/usr/lib/python3.11/abc.py", "_call"),
        _frame("app/main.py", "main"),
    )
    report = score_frames(trace)
    best = report.highest()
    assert best is not None
    assert best.frame.filename == "app/main.py"


# ---------------------------------------------------------------------------
# scorer2_cmd tests
# ---------------------------------------------------------------------------

SAMPLE = """Traceback (most recent call last):
  File \"app/main.py\", line 12, in run
    result = compute(x)
  File \"app/compute.py\", line 5, in compute
    return 1 / x
ZeroDivisionError: division by zero
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "top": 0, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_score2():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    parsed = root.parse_args(["score2"])
    assert hasattr(parsed, "top")


def test_scorer2_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE))
    out = io.StringIO()
    rc = scorer2_command(_args(), out=out)
    assert rc == 0


def test_scorer2_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    rc = scorer2_command(_args(), out=out)
    assert rc == 1


def test_scorer2_command_output_contains_scored(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE))
    out = io.StringIO()
    scorer2_command(_args(), out=out)
    assert "Scored" in out.getvalue()


def test_scorer2_command_reads_from_file(tmp_path):
    p = tmp_path / "trace.txt"
    p.write_text(SAMPLE)
    out = io.StringIO()
    rc = scorer2_command(_args(file=str(p)), out=out)
    assert rc == 0


def test_scorer2_command_returns_one_on_missing_file():
    out = io.StringIO()
    rc = scorer2_command(_args(file="/no/such/file.txt"), out=out)
    assert rc == 1


def test_scorer2_top_flag_limits_output(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE))
    out = io.StringIO()
    scorer2_command(_args(top=1), out=out)
    lines = [l for l in out.getvalue().splitlines() if "█" in l or "░" in l]
    assert len(lines) <= 1
