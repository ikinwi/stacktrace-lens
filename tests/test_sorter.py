"""Tests for stacktrace_lens.sorter."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.sorter import (
    SortKey,
    SortOptions,
    SortReport,
    format_sort,
    sort_traces,
)


def _frame(filename: str = "app.py", lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, context=None)


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames=None,
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=frames,
    )


def test_sort_traces_returns_sort_report():
    traces = [_trace()]
    report = sort_traces(traces)
    assert isinstance(report, SortReport)


def test_sort_traces_default_preserves_order():
    t1 = _trace(exc_type="ZeroDivisionError")
    t2 = _trace(exc_type="AttributeError")
    report = sort_traces([t1, t2])
    assert report.traces == [t1, t2]


def test_sort_by_depth_ascending():
    shallow = _trace(frames=[_frame()])
    deep = _trace(frames=[_frame(), _frame(), _frame()])
    opts = SortOptions(key=SortKey.DEPTH)
    report = sort_traces([deep, shallow], options=opts)
    assert report.traces[0] is shallow
    assert report.traces[1] is deep


def test_sort_by_depth_descending():
    shallow = _trace(frames=[_frame()])
    deep = _trace(frames=[_frame(), _frame(), _frame()])
    opts = SortOptions(key=SortKey.DEPTH, reverse=True)
    report = sort_traces([shallow, deep], options=opts)
    assert report.traces[0] is deep


def test_sort_by_exception_alphabetical():
    t1 = _trace(exc_type="ZeroDivisionError")
    t2 = _trace(exc_type="AttributeError")
    t3 = _trace(exc_type="ValueError")
    opts = SortOptions(key=SortKey.EXCEPTION)
    report = sort_traces([t1, t2, t3], options=opts)
    types = [t.exception_type for t in report.traces]
    assert types == sorted(types, key=str.lower)


def test_sort_by_exception_descending():
    t1 = _trace(exc_type="AttributeError")
    t2 = _trace(exc_type="ZeroDivisionError")
    opts = SortOptions(key=SortKey.EXCEPTION, reverse=True)
    report = sort_traces([t1, t2], options=opts)
    assert report.traces[0].exception_type == "ZeroDivisionError"


def test_sort_by_file():
    t1 = _trace(frames=[_frame(filename="zoo.py")])
    t2 = _trace(frames=[_frame(filename="alpha.py")])
    opts = SortOptions(key=SortKey.FILE)
    report = sort_traces([t1, t2], options=opts)
    assert report.traces[0] is t2


def test_report_count_matches_input():
    traces = [_trace(), _trace(), _trace()]
    report = sort_traces(traces)
    assert report.count == 3


def test_report_summary_line_contains_key():
    opts = SortOptions(key=SortKey.DEPTH)
    report = sort_traces([_trace()], options=opts)
    assert "depth" in report.summary_line()


def test_report_summary_line_contains_direction():
    opts = SortOptions(key=SortKey.DEPTH, reverse=True)
    report = sort_traces([_trace()], options=opts)
    assert "descending" in report.summary_line()


def test_format_sort_returns_string():
    report = sort_traces([_trace()])
    result = format_sort(report)
    assert isinstance(result, str)


def test_format_sort_contains_exception_type():
    report = sort_traces([_trace(exc_type="RuntimeError")])
    result = format_sort(report)
    assert "RuntimeError" in result
