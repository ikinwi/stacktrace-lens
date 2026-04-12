"""Tests for stacktrace_lens.trimmer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.trimmer import TrimOptions, TrimReport, trim_trace


def _frame(filename: str, lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=name, context=None)


def _trace(*filenames: str) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=[_frame(f) for f in filenames],
    )


# --- return type ---

def test_trim_returns_report():
    t = _trace("a.py", "b.py")
    result = trim_trace(t)
    assert isinstance(result, TrimReport)


def test_trim_report_contains_trace():
    t = _trace("a.py", "b.py")
    result = trim_trace(t)
    assert isinstance(result.trace, StackTrace)


# --- no-op ---

def test_no_options_keeps_all_frames():
    t = _trace("a.py", "b.py", "c.py")
    r = trim_trace(t)
    assert r.trimmed_count == 3
    assert r.removed_count == 0


# --- strip_top ---

def test_strip_top_removes_from_start():
    t = _trace("a.py", "b.py", "c.py")
    r = trim_trace(t, TrimOptions(strip_top=1))
    assert r.trimmed_count == 2
    assert r.frames[0].filename == "b.py"
    assert r.stripped_top == 1


def test_strip_top_clamped_to_frame_count():
    t = _trace("a.py", "b.py")
    r = trim_trace(t, TrimOptions(strip_top=10))
    assert r.trimmed_count == 0


# --- strip_bottom ---

def test_strip_bottom_removes_from_end():
    t = _trace("a.py", "b.py", "c.py")
    r = trim_trace(t, TrimOptions(strip_bottom=1))
    assert r.trimmed_count == 2
    assert r.frames[-1].filename == "b.py"
    assert r.stripped_bottom == 1


def test_strip_bottom_clamped_to_remaining_frames():
    t = _trace("a.py", "b.py")
    r = trim_trace(t, TrimOptions(strip_bottom=5))
    assert r.trimmed_count == 0


# --- drop_prefix ---

def test_drop_prefix_removes_matching_frames():
    t = _trace("/usr/lib/python3/a.py", "app/b.py", "/usr/lib/python3/c.py")
    r = trim_trace(t, TrimOptions(drop_prefix="/usr/lib"))
    assert r.trimmed_count == 1
    assert r.frames[0].filename == "app/b.py"
    assert r.dropped_prefix == 2


def test_drop_prefix_no_match_keeps_all():
    t = _trace("a.py", "b.py")
    r = trim_trace(t, TrimOptions(drop_prefix="/no/match"))
    assert r.trimmed_count == 2
    assert r.dropped_prefix == 0


# --- drop_suffix ---

def test_drop_suffix_removes_matching_frames():
    t = _trace("module_test.py", "app.py", "other_test.py")
    r = trim_trace(t, TrimOptions(drop_suffix="_test.py"))
    assert r.trimmed_count == 1
    assert r.frames[0].filename == "app.py"
    assert r.dropped_suffix == 2


# --- combined ---

def test_combined_options():
    t = _trace("/usr/a.py", "b.py", "c.py", "d_test.py")
    opts = TrimOptions(strip_top=1, drop_suffix="_test.py")
    r = trim_trace(t, opts)
    # strip_top removes /usr/a.py; drop_suffix removes d_test.py
    assert r.trimmed_count == 2
    assert r.removed_count == 2


# --- summary_line ---

def test_summary_line_no_removal():
    t = _trace("a.py")
    r = trim_trace(t)
    assert "none" in r.summary_line()


def test_summary_line_shows_detail():
    t = _trace("a.py", "b.py", "c.py")
    r = trim_trace(t, TrimOptions(strip_top=1, strip_bottom=1))
    line = r.summary_line()
    assert "top:1" in line
    assert "bottom:1" in line
