"""Tests for stacktrace_lens.pivot."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.pivot import (
    PivotGroup,
    PivotReport,
    format_pivot,
    pivot_traces,
)


def _frame(filename: str = "app.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    filename: str = "app.py",
    function: str = "run",
) -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=[_frame(filename=filename, function=function)],
    )


# ---------------------------------------------------------------------------
# pivot_traces return type
# ---------------------------------------------------------------------------

def test_pivot_returns_pivot_report():
    report = pivot_traces([_trace()])
    assert isinstance(report, PivotReport)


def test_empty_traces_returns_empty_report():
    report = pivot_traces([])
    assert report.total_traces == 0
    assert report.group_count == 0


# ---------------------------------------------------------------------------
# grouping by exception (default)
# ---------------------------------------------------------------------------

def test_single_trace_produces_one_group():
    report = pivot_traces([_trace()])
    assert report.group_count == 1


def test_identical_exception_types_merged():
    traces = [_trace("ValueError"), _trace("ValueError"), _trace("ValueError")]
    report = pivot_traces(traces)
    assert report.group_count == 1
    assert report.groups[0].count == 3


def test_different_exception_types_split():
    traces = [_trace("ValueError"), _trace("KeyError"), _trace("TypeError")]
    report = pivot_traces(traces)
    assert report.group_count == 3


def test_groups_sorted_by_count_descending():
    traces = [
        _trace("KeyError"),
        _trace("ValueError"),
        _trace("ValueError"),
        _trace("ValueError"),
    ]
    report = pivot_traces(traces)
    assert report.groups[0].key == "ValueError"


# ---------------------------------------------------------------------------
# grouping by file / function
# ---------------------------------------------------------------------------

def test_pivot_by_file():
    traces = [
        _trace(filename="a.py"),
        _trace(filename="a.py"),
        _trace(filename="b.py"),
    ]
    report = pivot_traces(traces, pivot="file")
    assert report.group_count == 2
    assert report.groups[0].count == 2


def test_pivot_by_function():
    traces = [
        _trace(function="foo"),
        _trace(function="bar"),
        _trace(function="foo"),
    ]
    report = pivot_traces(traces, pivot="function")
    assert report.group_count == 2


# ---------------------------------------------------------------------------
# PivotReport helpers
# ---------------------------------------------------------------------------

def test_total_traces_count():
    traces = [_trace("ValueError")] * 4 + [_trace("KeyError")] * 2
    report = pivot_traces(traces)
    assert report.total_traces == 6


def test_by_key_returns_correct_group():
    report = pivot_traces([_trace("ValueError"), _trace("KeyError")])
    grp = report.by_key("ValueError")
    assert grp is not None
    assert grp.key == "ValueError"


def test_by_key_returns_none_for_missing():
    report = pivot_traces([_trace("ValueError")])
    assert report.by_key("ZeroDivisionError") is None


def test_representative_is_first_trace():
    t1 = _trace("ValueError")
    t2 = _trace("ValueError")
    report = pivot_traces([t1, t2])
    assert report.groups[0].representative is t1


# ---------------------------------------------------------------------------
# format_pivot
# ---------------------------------------------------------------------------

def test_format_pivot_returns_string():
    report = pivot_traces([_trace()])
    assert isinstance(format_pivot(report), str)


def test_format_pivot_contains_summary_line():
    report = pivot_traces([_trace()])
    text = format_pivot(report)
    assert "Pivoted" in text


def test_format_pivot_contains_group_key():
    report = pivot_traces([_trace("RuntimeError")])
    text = format_pivot(report)
    assert "RuntimeError" in text


def test_pivot_group_str_contains_key_and_count():
    grp = PivotGroup(key="ValueError", traces=[_trace(), _trace()])
    s = str(grp)
    assert "ValueError" in s
    assert "2" in s
