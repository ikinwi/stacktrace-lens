"""Tests for stacktrace_lens.slicer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.slicer import SliceOptions, SliceReport, slice_trace


def _frame(filename: str, lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=name, context=None)


def _trace(*filenames: str) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=[_frame(f) for f in filenames],
    )


# --- return type ---

def test_slice_returns_report():
    t = _trace("a.py", "b.py", "c.py")
    result = slice_trace(t)
    assert isinstance(result, SliceReport)


def test_default_options_keeps_all_frames():
    t = _trace("a.py", "b.py", "c.py")
    r = slice_trace(t)
    assert r.sliced_count == 3
    assert r.removed_count == 0


# --- start / end ---

def test_start_trims_leading_frames():
    t = _trace("a.py", "b.py", "c.py", "d.py")
    r = slice_trace(t, SliceOptions(start=2))
    assert [f.filename for f in r.frames] == ["c.py", "d.py"]


def test_end_trims_trailing_frames():
    t = _trace("a.py", "b.py", "c.py", "d.py")
    r = slice_trace(t, SliceOptions(end=2))
    assert [f.filename for f in r.frames] == ["a.py", "b.py"]


def test_start_and_end_together():
    t = _trace("a.py", "b.py", "c.py", "d.py")
    r = slice_trace(t, SliceOptions(start=1, end=3))
    assert [f.filename for f in r.frames] == ["b.py", "c.py"]


# --- step ---

def test_step_two_returns_every_other_frame():
    t = _trace("a.py", "b.py", "c.py", "d.py")
    r = slice_trace(t, SliceOptions(step=2))
    assert [f.filename for f in r.frames] == ["a.py", "c.py"]


def test_invalid_step_treated_as_one():
    t = _trace("a.py", "b.py", "c.py")
    r = slice_trace(t, SliceOptions(step=0))
    assert r.sliced_count == 3


# --- counts ---

def test_original_count_reflects_input():
    t = _trace("a.py", "b.py", "c.py")
    r = slice_trace(t, SliceOptions(start=1))
    assert r.original_count == 3


def test_removed_count_is_difference():
    t = _trace("a.py", "b.py", "c.py", "d.py")
    r = slice_trace(t, SliceOptions(start=1, end=3))
    assert r.removed_count == 2


# --- summary_line ---

def test_summary_line_returns_string():
    t = _trace("a.py", "b.py")
    r = slice_trace(t)
    assert isinstance(r.summary_line(), str)


def test_summary_line_mentions_kept_count():
    t = _trace("a.py", "b.py", "c.py")
    r = slice_trace(t, SliceOptions(start=1))
    assert "2/3" in r.summary_line()


# --- as_trace ---

def test_as_trace_returns_stack_trace():
    from stacktrace_lens.parser import StackTrace as ST
    t = _trace("a.py", "b.py", "c.py")
    r = slice_trace(t, SliceOptions(end=2))
    st = r.as_trace()
    assert isinstance(st, ST)
    assert len(st.frames) == 2
