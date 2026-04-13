"""Tests for stacktrace_lens.replayer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.replayer import (
    ReplayEvent,
    ReplayOptions,
    ReplayReport,
    replay_traces,
)


def _frame(filename="app.py", lineno=10, function="run"):
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(exc_type="ValueError", msg="bad value", frames=None):
    return StackTrace(
        exception_type=exc_type,
        exception_message=msg,
        frames=frames or [_frame()],
    )


def _entries(n=3):
    return [(_trace(exc_type=f"Error{i}"), f"label{i}") for i in range(n)]


def test_replay_returns_report_instance():
    report = replay_traces(_entries(2))
    assert isinstance(report, ReplayReport)


def test_replay_event_count_matches_entries():
    report = replay_traces(_entries(3))
    assert report.count == 3


def test_replay_events_are_replay_event_instances():
    report = replay_traces(_entries(2))
    for event in report.events:
        assert isinstance(event, ReplayEvent)


def test_replay_event_index_sequential():
    report = replay_traces(_entries(4))
    for i, event in enumerate(report.events):
        assert event.index == i


def test_replay_event_label_preserved():
    entries = [(_trace(), "my-label")]
    report = replay_traces(entries)
    assert report.events[0].label == "my-label"


def test_replay_event_no_label_is_none():
    entries = [(_trace(), None)]
    report = replay_traces(entries)
    assert report.events[0].label is None


def test_replay_max_entries_limits_output():
    options = ReplayOptions(max_entries=2)
    report = replay_traces(_entries(5), options)
    assert report.count == 2


def test_replay_empty_entries_returns_empty_report():
    report = replay_traces([])
    assert report.count == 0


def test_replay_event_elapsed_non_negative():
    report = replay_traces(_entries(2))
    for event in report.events:
        assert event.elapsed >= 0.0


def test_replay_summary_line_contains_count():
    report = replay_traces(_entries(3))
    assert "3" in report.summary_line()


def test_replay_event_str_contains_exception_type():
    entries = [(_trace(exc_type="RuntimeError"), None)]
    report = replay_traces(entries)
    assert "RuntimeError" in str(report.events[0])


def test_replay_speed_option_accepted():
    options = ReplayOptions(speed=2.0)
    report = replay_traces(_entries(2), options)
    assert report.count == 2


def test_replay_default_options_used_when_none_passed():
    report = replay_traces(_entries(1), None)
    assert report.count == 1
