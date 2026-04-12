"""Tests for stacktrace_lens.flattener."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.flattener import (
    FlattenReport,
    flatten_traces,
    format_flatten,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


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


def test_flatten_returns_report():
    report = flatten_traces([_trace()])
    assert isinstance(report, FlattenReport)


def test_flatten_single_trace_frame_count():
    frames = [_frame("a.py", 1), _frame("b.py", 2)]
    report = flatten_traces([_trace(frames=frames)])
    assert report.total_frames == 2


def test_flatten_multiple_traces_combines_frames():
    t1 = _trace(frames=[_frame("a.py", 1)])
    t2 = _trace(exc_type="KeyError", frames=[_frame("b.py", 2)])
    report = flatten_traces([t1, t2])
    assert report.total_frames == 2


def test_flatten_deduplicates_consecutive_identical_frames():
    frame = _frame("a.py", 5, "fn")
    t1 = _trace(frames=[frame])
    t2 = _trace(frames=[frame, _frame("b.py", 9)])
    report = flatten_traces([t1, t2])
    # The duplicate consecutive frame at the boundary should be collapsed
    assert report.total_frames == 2


def test_flatten_exception_chain_collected():
    t1 = _trace(exc_type="ValueError")
    t2 = _trace(exc_type="KeyError")
    report = flatten_traces([t1, t2])
    assert "ValueError" in report.exception_chain
    assert "KeyError" in report.exception_chain


def test_flatten_exception_chain_no_duplicates():
    t1 = _trace(exc_type="ValueError")
    t2 = _trace(exc_type="ValueError")
    report = flatten_traces([t1, t2])
    assert report.exception_chain.count("ValueError") == 1


def test_flatten_trace_count():
    report = flatten_traces([_trace(), _trace()])
    assert report.trace_count == 2


def test_flatten_empty_list():
    report = flatten_traces([])
    assert report.total_frames == 0
    assert report.trace_count == 0


def test_summary_line_contains_trace_count():
    report = flatten_traces([_trace(), _trace()])
    assert "2" in report.summary_line()


def test_format_flatten_returns_string():
    report = flatten_traces([_trace()])
    result = format_flatten(report)
    assert isinstance(result, str)


def test_format_flatten_contains_filename():
    report = flatten_traces([_trace(frames=[_frame("myapp.py", 42)])])
    result = format_flatten(report)
    assert "myapp.py" in result


def test_format_flatten_colour_flag_does_not_crash():
    report = flatten_traces([_trace()])
    result = format_flatten(report, colour=True)
    assert isinstance(result, str)
