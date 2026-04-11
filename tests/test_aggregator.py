"""Tests for stacktrace_lens.aggregator."""
from __future__ import annotations

from collections import Counter

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.aggregator import (
    AggregationReport,
    aggregate_traces,
    format_aggregation,
)


def _frame(filename: str = "app.py", function: str = "main", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line=None)


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames=None,
) -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=frames or [_frame()],
    )


# --- aggregate_traces ---

def test_aggregate_returns_report():
    report = aggregate_traces([_trace()])
    assert isinstance(report, AggregationReport)


def test_total_traces_count():
    report = aggregate_traces([_trace(), _trace()])
    assert report.total_traces == 2


def test_empty_traces_produces_zero_total():
    report = aggregate_traces([])
    assert report.total_traces == 0


def test_exception_counts_single():
    report = aggregate_traces([_trace("TypeError")])
    assert report.exception_counts["TypeError"] == 1


def test_exception_counts_multiple_same():
    report = aggregate_traces([_trace("TypeError"), _trace("TypeError")])
    assert report.exception_counts["TypeError"] == 2


def test_most_common_exception():
    traces = [_trace("TypeError"), _trace("TypeError"), _trace("ValueError")]
    report = aggregate_traces(traces)
    assert report.most_common_exception == "TypeError"


def test_most_common_exception_none_when_empty():
    report = aggregate_traces([])
    assert report.most_common_exception is None


def test_file_counts():
    frames = [_frame("a.py"), _frame("a.py"), _frame("b.py")]
    report = aggregate_traces([_trace(frames=frames)])
    assert report.file_counts["a.py"] == 2
    assert report.file_counts["b.py"] == 1


def test_most_common_file():
    frames = [_frame("a.py"), _frame("a.py"), _frame("b.py")]
    report = aggregate_traces([_trace(frames=frames)])
    assert report.most_common_file == "a.py"


def test_function_counts():
    frames = [_frame(function="foo"), _frame(function="foo"), _frame(function="bar")]
    report = aggregate_traces([_trace(frames=frames)])
    assert report.function_counts["foo"] == 2


def test_most_common_function():
    frames = [_frame(function="foo"), _frame(function="foo")]
    report = aggregate_traces([_trace(frames=frames)])
    assert report.most_common_function == "foo"


def test_traces_stored_on_report():
    t = _trace()
    report = aggregate_traces([t])
    assert t in report.traces


# --- format_aggregation ---

def test_format_returns_string():
    report = aggregate_traces([_trace()])
    result = format_aggregation(report)
    assert isinstance(result, str)


def test_format_contains_total():
    report = aggregate_traces([_trace(), _trace()])
    result = format_aggregation(report)
    assert "2" in result


def test_format_contains_exception_type():
    report = aggregate_traces([_trace("RuntimeError")])
    result = format_aggregation(report)
    assert "RuntimeError" in result
