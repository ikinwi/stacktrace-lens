"""Tests for stacktrace_lens.replayer2."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.replayer2 import (
    ReplayOptions,
    ReplayReport2,
    replay_traces,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(exc_type: str = "ValueError", msg: str = "bad") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=msg,
        frames=[_frame()],
        raw="",
    )


def test_replay_returns_report_instance():
    report = replay_traces([_trace()])
    assert isinstance(report, ReplayReport2)


def test_replay_event_count_matches_input():
    traces = [_trace(), _trace("KeyError", "key")]
    report = replay_traces(traces)
    assert report.count == 2


def test_replay_no_options_all_replayed():
    traces = [_trace(), _trace("KeyError", "k")]
    report = replay_traces(traces)
    assert report.replayed_count == 2
    assert report.skipped_count == 0


def test_replay_skip_duplicates_removes_second():
    t = _trace()
    report = replay_traces([t, t], ReplayOptions(skip_duplicates=True))
    assert report.replayed_count == 1
    assert report.skipped_count == 1


def test_replay_max_events_limits_output():
    traces = [_trace(f"E{i}", str(i)) for i in range(10)]
    report = replay_traces(traces, ReplayOptions(max_events=3))
    assert report.count == 3


def test_replay_reverse_reverses_order():
    traces = [_trace("A", "1"), _trace("B", "2")]
    report = replay_traces(traces, ReplayOptions(reverse=True))
    assert report.events[0].trace.exception_type == "B"
    assert report.events[1].trace.exception_type == "A"


def test_replay_event_str_contains_index():
    report = replay_traces([_trace()])
    assert "#0" in str(report.events[0])


def test_replay_event_str_contains_exception_type():
    report = replay_traces([_trace("TypeError", "bad type")])
    assert "TypeError" in str(report.events[0])


def test_replay_summary_line_format():
    traces = [_trace(), _trace("KeyError", "k")]
    report = replay_traces(traces)
    line = report.summary_line()
    assert "2/2" in line
    assert "skipped" in line


def test_replay_empty_traces_returns_empty_report():
    report = replay_traces([])
    assert report.count == 0
    assert report.replayed_count == 0


def test_replay_skipped_event_str_contains_skipped():
    t = _trace()
    report = replay_traces([t, t], ReplayOptions(skip_duplicates=True))
    skipped = [e for e in report.events if e.skipped]
    assert len(skipped) == 1
    assert "skipped" in str(skipped[0])
