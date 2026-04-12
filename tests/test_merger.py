"""Tests for stacktrace_lens.merger."""
from __future__ import annotations

from collections import Counter

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.merger import (
    MergeReport,
    merge_traces,
    format_merge,
)


def _frame(filename: str = "app.py", lineno: int = 1, func: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=func, context=None)


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


# --- merge_traces ---

def test_merge_returns_merge_report():
    report = merge_traces([_trace()])
    assert isinstance(report, MergeReport)


def test_merge_empty_list_returns_zero_totals():
    report = merge_traces([])
    assert report.total_traces == 0
    assert report.merged_frames == []
    assert report.common_exception is None


def test_total_traces_count():
    report = merge_traces([_trace(), _trace()])
    assert report.total_traces == 2


def test_merged_frames_combines_all():
    t1 = _trace(frames=[_frame("a.py"), _frame("b.py")])
    t2 = _trace(frames=[_frame("c.py")])
    report = merge_traces([t1, t2])
    assert len(report.merged_frames) == 3


def test_common_exception_most_frequent():
    traces = [
        _trace(exc_type="ValueError"),
        _trace(exc_type="ValueError"),
        _trace(exc_type="KeyError"),
    ]
    report = merge_traces(traces)
    assert report.common_exception == "ValueError"


def test_unique_exceptions_count():
    traces = [_trace("ValueError"), _trace("KeyError"), _trace("ValueError")]
    report = merge_traces(traces)
    assert report.unique_exceptions == 2


def test_unique_files_count():
    t1 = _trace(frames=[_frame("x.py"), _frame("y.py")])
    t2 = _trace(frames=[_frame("x.py"), _frame("z.py")])
    report = merge_traces([t1, t2])
    assert report.unique_files == 3


def test_common_file_most_frequent():
    t1 = _trace(frames=[_frame("hot.py"), _frame("cold.py")])
    t2 = _trace(frames=[_frame("hot.py")])
    report = merge_traces([t1, t2])
    assert report.common_file == "hot.py"


def test_exception_counts_is_counter():
    report = merge_traces([_trace("TypeError")])
    assert isinstance(report.exception_counts, Counter)
    assert report.exception_counts["TypeError"] == 1


# --- format_merge ---

def test_format_merge_returns_string():
    report = merge_traces([_trace()])
    assert isinstance(format_merge(report), str)


def test_format_merge_contains_total():
    report = merge_traces([_trace(), _trace()])
    assert "2" in format_merge(report)


def test_format_merge_contains_exception():
    report = merge_traces([_trace(exc_type="RuntimeError")])
    assert "RuntimeError" in format_merge(report)


def test_summary_line_contains_trace_count():
    report = merge_traces([_trace(), _trace()])
    assert "2" in report.summary_line()
