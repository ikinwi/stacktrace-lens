"""Tests for stacktrace_lens.summarizer."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.summarizer import (
    SummaryReport,
    summarize_traces,
    format_summary,
)


def _frame(filename: str = "app.py", function: str = "main", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames=None,
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# --- summarize_traces ---

def test_summarize_returns_summary_report():
    report = summarize_traces([_trace()])
    assert isinstance(report, SummaryReport)


def test_summarize_empty_list_returns_zero_totals():
    report = summarize_traces([])
    assert report.total_traces == 0
    assert report.total_frames == 0
    assert report.avg_depth == 0.0


def test_total_traces_count():
    report = summarize_traces([_trace(), _trace()])
    assert report.total_traces == 2


def test_total_frames_count():
    t = _trace(frames=[_frame(), _frame(), _frame()])
    report = summarize_traces([t])
    assert report.total_frames == 3


def test_avg_depth_calculation():
    t1 = _trace(frames=[_frame(), _frame()])
    t2 = _trace(frames=[_frame()])
    report = summarize_traces([t1, t2])
    assert report.avg_depth == pytest.approx(1.5)


def test_most_common_exception():
    traces = [
        _trace(exc_type="ValueError"),
        _trace(exc_type="ValueError"),
        _trace(exc_type="TypeError"),
    ]
    report = summarize_traces(traces)
    assert report.most_common_exception == "ValueError"


def test_most_common_file():
    t = _trace(frames=[_frame("a.py"), _frame("a.py"), _frame("b.py")])
    report = summarize_traces([t])
    assert report.most_common_file == "a.py"


def test_most_common_function():
    t = _trace(frames=[_frame(function="foo"), _frame(function="foo"), _frame(function="bar")])
    report = summarize_traces([t])
    assert report.most_common_function == "foo"


def test_empty_list_most_common_fields_are_none():
    report = summarize_traces([])
    assert report.most_common_exception is None
    assert report.most_common_file is None
    assert report.most_common_function is None


def test_summary_line_format():
    report = summarize_traces([_trace(frames=[_frame(), _frame()])])
    line = report.summary_line
    assert "1 trace" in line
    assert "2 frame" in line


# --- format_summary ---

def test_format_summary_returns_string():
    report = summarize_traces([_trace()])
    result = format_summary(report)
    assert isinstance(result, str)


def test_format_summary_contains_total_traces():
    report = summarize_traces([_trace(), _trace()])
    result = format_summary(report, colour=False)
    assert "2" in result


def test_format_summary_no_colour_has_no_escape_codes():
    report = summarize_traces([_trace()])
    result = format_summary(report, colour=False)
    assert "\033[" not in result


def test_format_summary_with_colour_has_escape_codes():
    report = summarize_traces([_trace()])
    result = format_summary(report, colour=True)
    assert "\033[" in result
