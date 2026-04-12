"""Tests for stacktrace_lens.digester."""
from __future__ import annotations

from collections import Counter

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.digester import DigestReport, digest_traces, format_digest


def _frame(filename: str = "app.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames=None,
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# ---------------------------------------------------------------------------
# digest_traces
# ---------------------------------------------------------------------------

def test_digest_returns_report():
    report = digest_traces([_trace()])
    assert isinstance(report, DigestReport)


def test_empty_traces_returns_zero_total():
    report = digest_traces([])
    assert report.total_traces == 0


def test_empty_traces_avg_depth_is_zero():
    report = digest_traces([])
    assert report.avg_depth == 0.0


def test_empty_traces_most_common_exception_is_none():
    report = digest_traces([])
    assert report.most_common_exception is None


def test_total_traces_count():
    traces = [_trace(), _trace(exc_type="KeyError")]
    report = digest_traces(traces)
    assert report.total_traces == 2


def test_exception_counts_populated():
    traces = [_trace("ValueError"), _trace("ValueError"), _trace("KeyError")]
    report = digest_traces(traces)
    assert report.exception_counts["ValueError"] == 2
    assert report.exception_counts["KeyError"] == 1


def test_most_common_exception():
    traces = [_trace("ValueError"), _trace("ValueError"), _trace("KeyError")]
    report = digest_traces(traces)
    assert report.most_common_exception == "ValueError"


def test_file_counts_populated():
    frames = [_frame("a.py"), _frame("b.py"), _frame("a.py")]
    report = digest_traces([_trace(frames=frames)])
    assert report.file_counts["a.py"] == 2
    assert report.file_counts["b.py"] == 1


def test_most_common_file():
    frames = [_frame("a.py"), _frame("a.py"), _frame("b.py")]
    report = digest_traces([_trace(frames=frames)])
    assert report.most_common_file == "a.py"


def test_avg_depth_single_trace():
    frames = [_frame(), _frame(), _frame()]
    report = digest_traces([_trace(frames=frames)])
    assert report.avg_depth == pytest.approx(3.0)


def test_max_depth():
    t1 = _trace(frames=[_frame()])
    t2 = _trace(frames=[_frame(), _frame(), _frame()])
    report = digest_traces([t1, t2])
    assert report.max_depth == 3


def test_top_exceptions_limits_results():
    traces = [_trace(f"Exc{i}") for i in range(10)]
    report = digest_traces(traces)
    assert len(report.top_exceptions(3)) == 3


# ---------------------------------------------------------------------------
# format_digest
# ---------------------------------------------------------------------------

def test_format_digest_returns_string():
    report = digest_traces([_trace()])
    assert isinstance(format_digest(report), str)


def test_format_digest_contains_total():
    report = digest_traces([_trace(), _trace()])
    output = format_digest(report)
    assert "2" in output


def test_format_digest_contains_exception_type():
    report = digest_traces([_trace("RuntimeError")])
    output = format_digest(report)
    assert "RuntimeError" in output


def test_format_digest_contains_filename():
    report = digest_traces([_trace(frames=[_frame("mymodule.py")])])
    output = format_digest(report)
    assert "mymodule.py" in output
