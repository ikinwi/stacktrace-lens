"""Tests for stacktrace_lens.deduplicator."""

from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.deduplicator import (
    DeduplicateOptions,
    DeduplicatedFrame,
    deduplicate_frames,
    format_deduplicated,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn", code: str = "") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, code=code)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        frames=list(frames),
        exception_type="ValueError",
        exception_message="oops",
    )


# --- basic return types ---

def test_deduplicate_returns_list():
    trace = _trace(_frame())
    result = deduplicate_frames(trace)
    assert isinstance(result, list)


def test_deduplicate_items_are_deduplicated_frames():
    trace = _trace(_frame())
    result = deduplicate_frames(trace)
    assert all(isinstance(df, DeduplicatedFrame) for df in result)


# --- no duplicates ---

def test_no_duplicates_preserves_all_frames():
    frames = [_frame("a.py"), _frame("b.py"), _frame("c.py")]
    trace = _trace(*frames)
    result = deduplicate_frames(trace)
    assert len(result) == 3


def test_no_duplicates_count_is_one():
    trace = _trace(_frame("a.py"), _frame("b.py"))
    result = deduplicate_frames(trace)
    assert all(df.count == 1 for df in result)


# --- consecutive duplicates ---

def test_consecutive_duplicates_collapsed():
    f = _frame("loop.py", function="recurse")
    trace = _trace(f, f, f)
    opts = DeduplicateOptions(min_repeat=2)
    result = deduplicate_frames(trace, opts)
    assert len(result) == 1
    assert result[0].count == 3


def test_repeated_frame_is_repeated_property():
    f = _frame("loop.py", function="recurse")
    trace = _trace(f, f, f)
    opts = DeduplicateOptions(min_repeat=2)
    result = deduplicate_frames(trace, opts)
    assert result[0].is_repeated is True


def test_below_min_repeat_expanded():
    f = _frame("loop.py", function="recurse")
    trace = _trace(f, f)  # only 2 repetitions
    opts = DeduplicateOptions(min_repeat=3)
    result = deduplicate_frames(trace, opts)
    # should be expanded back to 2 individual frames
    assert len(result) == 2
    assert all(df.count == 1 for df in result)


def test_non_consecutive_duplicates_not_collapsed():
    a = _frame("a.py", function="foo")
    b = _frame("b.py", function="bar")
    trace = _trace(a, b, a, b)
    result = deduplicate_frames(trace)
    assert len(result) == 4


# --- lineno keying ---

def test_key_on_lineno_distinguishes_same_function():
    f1 = _frame("app.py", lineno=1, function="fn")
    f2 = _frame("app.py", lineno=2, function="fn")
    trace = _trace(f1, f2, f1)
    opts = DeduplicateOptions(min_repeat=2, key_on_lineno=True)
    result = deduplicate_frames(trace, opts)
    assert len(result) == 3  # no collapse because linenos differ


# --- format_deduplicated ---

def test_format_returns_string():
    trace = _trace(_frame())
    result = format_deduplicated(deduplicate_frames(trace), colour=False)
    assert isinstance(result, str)


def test_format_contains_repeat_marker():
    f = _frame("loop.py", function="recurse")
    trace = _trace(f, f, f)
    opts = DeduplicateOptions(min_repeat=2)
    deduped = deduplicate_frames(trace, opts)
    output = format_deduplicated(deduped, colour=False)
    assert "repeated 3" in output


def test_format_no_marker_for_single_frame():
    trace = _trace(_frame("solo.py"))
    deduped = deduplicate_frames(trace)
    output = format_deduplicated(deduped, colour=False)
    assert "repeated" not in output
