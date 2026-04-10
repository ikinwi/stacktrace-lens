"""Tests for stacktrace_lens.correlator."""

from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.correlator import (
    CorrelationGroup,
    CorrelationReport,
    correlate_traces,
    format_correlation,
)


def _frame(filename: str = "app.py", function: str = "main", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line="pass")


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames: list[Frame] | None = None,
) -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=frames or [_frame()],
    )


# --- correlate_traces ---

def test_correlate_returns_report():
    report = correlate_traces([_trace()])
    assert isinstance(report, CorrelationReport)


def test_total_traces_count():
    traces = [_trace(), _trace(exc_type="TypeError")]
    report = correlate_traces(traces)
    assert report.total_traces == 2


def test_by_exception_groups_correctly():
    traces = [_trace("ValueError"), _trace("ValueError"), _trace("TypeError")]
    report = correlate_traces(traces)
    assert report.by_exception["ValueError"].count == 2
    assert report.by_exception["TypeError"].count == 1


def test_by_file_groups_correctly():
    f1 = _frame(filename="app.py")
    f2 = _frame(filename="utils.py")
    t1 = _trace(frames=[f1])
    t2 = _trace(frames=[f1, f2])
    report = correlate_traces([t1, t2])
    assert report.by_file["app.py"].count == 2
    assert report.by_file["utils.py"].count == 1


def test_by_function_groups_correctly():
    f1 = _frame(function="run")
    f2 = _frame(function="setup")
    report = correlate_traces([_trace(frames=[f1, f2]), _trace(frames=[f1])])
    assert report.by_function["run"].count == 2
    assert report.by_function["setup"].count == 1


def test_empty_traces_returns_empty_report():
    report = correlate_traces([])
    assert report.total_traces == 0
    assert report.by_exception == {}


# --- most_common helpers ---

def test_most_common_exception():
    traces = [_trace("KeyError")] * 3 + [_trace("ValueError")]
    report = correlate_traces(traces)
    exc, cnt = report.most_common_exception()
    assert exc == "KeyError"
    assert cnt == 3


def test_most_common_exception_empty():
    report = correlate_traces([])
    assert report.most_common_exception() is None


def test_most_common_file_empty():
    report = correlate_traces([])
    assert report.most_common_file() is None


def test_most_common_function_empty():
    report = correlate_traces([])
    assert report.most_common_function() is None


# --- format_correlation ---

def test_format_returns_string():
    report = correlate_traces([_trace()])
    out = format_correlation(report)
    assert isinstance(out, str)


def test_format_contains_total():
    report = correlate_traces([_trace(), _trace()])
    out = format_correlation(report)
    assert "2" in out


def test_format_contains_exception_type():
    report = correlate_traces([_trace("ZeroDivisionError")])
    out = format_correlation(report)
    assert "ZeroDivisionError" in out
