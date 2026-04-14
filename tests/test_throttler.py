"""Tests for stacktrace_lens.throttler."""
from datetime import datetime, timedelta
from typing import List

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.throttler import (
    ThrottleOptions,
    ThrottleReport,
    throttle_traces,
)


def _make_trace(
    exc: str = "ValueError",
    msg: str = "oops",
    ts: datetime = None,
) -> StackTrace:
    trace = StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=[
            Frame(filename="app.py", lineno=1, function="run", context="x = 1")
        ],
    )
    if ts is not None:
        trace.timestamp = ts  # type: ignore[attr-defined]
    return trace


BASE = datetime(2024, 1, 1, 12, 0, 0)


def _ts(offset_seconds: float) -> datetime:
    return BASE + timedelta(seconds=offset_seconds)


# --- ThrottleReport helpers ---

def test_throttle_report_summary_line():
    report = ThrottleReport(
        total=10, allowed=5, dropped=5, traces=[],
        window_seconds=60.0, max_per_window=5,
    )
    line = report.summary_line()
    assert "5/10" in line
    assert "60" in line


# --- throttle_traces ---

def test_throttle_returns_report_instance():
    traces = [_make_trace()]
    result = throttle_traces(traces)
    assert isinstance(result, ThrottleReport)


def test_empty_traces_returns_zero_totals():
    report = throttle_traces([])
    assert report.total == 0
    assert report.allowed == 0
    assert report.dropped == 0


def test_traces_without_timestamp_always_allowed():
    traces = [_make_trace() for _ in range(20)]
    opts = ThrottleOptions(max_per_window=3)
    report = throttle_traces(traces, opts)
    assert report.allowed == 20
    assert report.dropped == 0


def test_within_limit_all_allowed():
    traces = [_make_trace(ts=_ts(i)) for i in range(5)]
    opts = ThrottleOptions(window_seconds=60.0, max_per_window=10)
    report = throttle_traces(traces, opts)
    assert report.allowed == 5
    assert report.dropped == 0


def test_exceeds_limit_drops_excess():
    traces = [_make_trace(ts=_ts(i)) for i in range(10)]
    opts = ThrottleOptions(window_seconds=60.0, max_per_window=4)
    report = throttle_traces(traces, opts)
    assert report.allowed == 4
    assert report.dropped == 6


def test_new_window_resets_counter():
    # 5 in first window, 5 in second window; limit=3 per window => 6 allowed
    traces = (
        [_make_trace(ts=_ts(i)) for i in range(5)] +
        [_make_trace(ts=_ts(60 + i)) for i in range(5)]
    )
    opts = ThrottleOptions(window_seconds=60.0, max_per_window=3)
    report = throttle_traces(traces, opts)
    assert report.allowed == 6
    assert report.dropped == 4


def test_report_traces_list_matches_allowed():
    traces = [_make_trace(ts=_ts(i)) for i in range(8)]
    opts = ThrottleOptions(window_seconds=60.0, max_per_window=3)
    report = throttle_traces(traces, opts)
    assert len(report.traces) == report.allowed


def test_default_options_applied_when_none():
    traces = [_make_trace(ts=_ts(i)) for i in range(5)]
    report = throttle_traces(traces, None)
    # default max_per_window=10, so all 5 should pass
    assert report.allowed == 5
