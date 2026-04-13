"""Tests for stacktrace_lens.streaker."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.streaker import (
    Streak,
    StreakReport,
    detect_streaks,
    format_streaks,
)


def _make_trace(exc_type: str, msg: str = "err") -> StackTrace:
    frame = Frame(filename="app.py", lineno=1, function="main", context="pass")
    return StackTrace(exception_type=exc_type, exception_message=msg, frames=[frame])


# ---------------------------------------------------------------------------
# StreakReport helpers
# ---------------------------------------------------------------------------

def test_streak_report_count_empty():
    r = StreakReport()
    assert r.count == 0


def test_streak_report_longest_none_when_empty():
    r = StreakReport()
    assert r.longest is None


def test_streak_report_longest_returns_max():
    r = StreakReport(
        streaks=[
            Streak("ValueError", 2, 0, 1),
            Streak("KeyError", 5, 2, 6),
        ],
        total_traces=7,
    )
    assert r.longest.exception_type == "KeyError"
    assert r.longest.count == 5


def test_summary_line_no_streaks():
    r = StreakReport(total_traces=3)
    assert "No streaks" in r.summary_line()


def test_summary_line_with_streaks():
    r = StreakReport(
        streaks=[Streak("RuntimeError", 3, 0, 2)],
        total_traces=5,
    )
    line = r.summary_line()
    assert "RuntimeError" in line
    assert "3" in line


# ---------------------------------------------------------------------------
# detect_streaks
# ---------------------------------------------------------------------------

def test_detect_empty_traces():
    report = detect_streaks([])
    assert report.count == 0
    assert report.total_traces == 0


def test_detect_single_trace_no_streak():
    report = detect_streaks([_make_trace("ValueError")])
    assert report.count == 0


def test_detect_two_identical_forms_streak():
    traces = [_make_trace("ValueError"), _make_trace("ValueError")]
    report = detect_streaks(traces)
    assert report.count == 1
    assert report.streaks[0].exception_type == "ValueError"
    assert report.streaks[0].count == 2


def test_detect_streak_indices():
    traces = [
        _make_trace("KeyError"),
        _make_trace("KeyError"),
        _make_trace("KeyError"),
    ]
    report = detect_streaks(traces)
    assert report.streaks[0].start_index == 0
    assert report.streaks[0].end_index == 2


def test_detect_no_streak_when_alternating():
    traces = [_make_trace("A"), _make_trace("B"), _make_trace("A")]
    report = detect_streaks(traces, min_length=2)
    assert report.count == 0


def test_detect_multiple_streaks():
    traces = (
        [_make_trace("ValueError")] * 3
        + [_make_trace("KeyError")]
        + [_make_trace("RuntimeError")] * 2
    )
    report = detect_streaks(traces)
    assert report.count == 2
    types = {s.exception_type for s in report.streaks}
    assert "ValueError" in types
    assert "RuntimeError" in types


def test_detect_min_length_respected():
    traces = [_make_trace("X"), _make_trace("X"), _make_trace("X")]
    report = detect_streaks(traces, min_length=4)
    assert report.count == 0


def test_total_traces_recorded():
    traces = [_make_trace("E")] * 5
    report = detect_streaks(traces)
    assert report.total_traces == 5


# ---------------------------------------------------------------------------
# format_streaks
# ---------------------------------------------------------------------------

def test_format_streaks_returns_string():
    traces = [_make_trace("ValueError")] * 3
    report = detect_streaks(traces)
    result = format_streaks(report)
    assert isinstance(result, str)


def test_format_streaks_contains_exception_type():
    traces = [_make_trace("TypeError")] * 2
    report = detect_streaks(traces)
    assert "TypeError" in format_streaks(report)


def test_streak_str():
    s = Streak("OSError", 4, 1, 4)
    assert "OSError" in str(s)
    assert "x4" in str(s)
