"""Tests for stacktrace_lens.timeline."""

from __future__ import annotations

import datetime

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.timeline import Timeline, TimestampedTrace, render_timeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    n_frames: int = 2,
) -> StackTrace:
    frames = [
        Frame(filename=f"file{i}.py", lineno=i * 10, function=f"fn{i}", source=None)
        for i in range(n_frames)
    ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


DT_BASE = datetime.datetime(2024, 6, 1, 12, 0, 0)


# ---------------------------------------------------------------------------
# TimestampedTrace
# ---------------------------------------------------------------------------

def test_timestamped_trace_stores_trace():
    trace = _make_trace()
    entry = TimestampedTrace(trace=trace, captured_at=DT_BASE)
    assert entry.trace is trace


def test_timestamped_trace_age_seconds():
    trace = _make_trace()
    entry = TimestampedTrace(trace=trace, captured_at=DT_BASE)
    reference = DT_BASE + datetime.timedelta(seconds=90)
    assert entry.age_seconds(reference) == pytest.approx(90.0)


def test_timestamped_trace_optional_label():
    trace = _make_trace()
    entry = TimestampedTrace(trace=trace, captured_at=DT_BASE, label="run-1")
    assert entry.label == "run-1"


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

def test_timeline_add_returns_entry():
    tl = Timeline()
    trace = _make_trace()
    entry = tl.add(trace, label="t1", captured_at=DT_BASE)
    assert isinstance(entry, TimestampedTrace)


def test_timeline_add_stores_entry():
    tl = Timeline()
    tl.add(_make_trace(), captured_at=DT_BASE)
    assert len(tl.entries) == 1


def test_timeline_sorted_entries_order():
    tl = Timeline()
    dt_later = DT_BASE + datetime.timedelta(hours=1)
    tl.add(_make_trace(exc_type="B"), captured_at=dt_later)
    tl.add(_make_trace(exc_type="A"), captured_at=DT_BASE)
    sorted_entries = tl.sorted_entries()
    assert sorted_entries[0].trace.exception_type == "A"
    assert sorted_entries[1].trace.exception_type == "B"


def test_timeline_most_recent():
    tl = Timeline()
    tl.add(_make_trace(exc_type="first"), captured_at=DT_BASE)
    tl.add(_make_trace(exc_type="last"), captured_at=DT_BASE + datetime.timedelta(days=1))
    assert tl.most_recent().trace.exception_type == "last"


def test_timeline_earliest():
    tl = Timeline()
    tl.add(_make_trace(exc_type="first"), captured_at=DT_BASE)
    tl.add(_make_trace(exc_type="last"), captured_at=DT_BASE + datetime.timedelta(days=1))
    assert tl.earliest().trace.exception_type == "first"


def test_timeline_empty_most_recent_returns_none():
    assert Timeline().most_recent() is None


def test_timeline_empty_earliest_returns_none():
    assert Timeline().earliest() is None


# ---------------------------------------------------------------------------
# render_timeline
# ---------------------------------------------------------------------------

def test_render_timeline_returns_string():
    tl = Timeline()
    tl.add(_make_trace(), captured_at=DT_BASE)
    result = render_timeline(tl, use_colour=False)
    assert isinstance(result, str)


def test_render_timeline_contains_exception_type():
    tl = Timeline()
    tl.add(_make_trace(exc_type="RuntimeError"), captured_at=DT_BASE)
    result = render_timeline(tl, use_colour=False)
    assert "RuntimeError" in result


def test_render_timeline_contains_label():
    tl = Timeline()
    tl.add(_make_trace(), label="my-label", captured_at=DT_BASE)
    result = render_timeline(tl, use_colour=False)
    assert "my-label" in result


def test_render_timeline_empty():
    result = render_timeline(Timeline(), use_colour=False)
    assert "no timeline entries" in result


def test_render_timeline_frame_count_mentioned():
    tl = Timeline()
    tl.add(_make_trace(n_frames=3), captured_at=DT_BASE)
    result = render_timeline(tl, use_colour=False)
    assert "3 frame" in result
