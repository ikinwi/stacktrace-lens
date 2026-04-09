"""Tests for stacktrace_lens.comparator."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.comparator import (
    FrameDiff,
    TraceDiff,
    compare_traces,
    format_diff,
)


def _frame(filename="app.py", function="run", lineno=10, code="pass"):
    return Frame(filename=filename, function=function, lineno=lineno, code=code)


def _trace(exc="ValueError", msg="oops", frames=None):
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc, exception_message=msg, frames=frames)


# --- compare_traces -----------------------------------------------------------

def test_compare_returns_trace_diff():
    diff = compare_traces(_trace(), _trace())
    assert isinstance(diff, TraceDiff)


def test_no_differences_when_identical():
    t = _trace()
    diff = compare_traces(t, t)
    assert not diff.has_differences


def test_exception_type_change_detected():
    left = _trace(exc="ValueError")
    right = _trace(exc="TypeError")
    diff = compare_traces(left, right)
    assert diff.exception_changed is True
    assert diff.left_exception == "ValueError"
    assert diff.right_exception == "TypeError"


def test_message_change_detected():
    left = _trace(msg="old message")
    right = _trace(msg="new message")
    diff = compare_traces(left, right)
    assert diff.message_changed is True


def test_added_frame_detected():
    left = _trace(frames=[_frame(lineno=1)])
    right = _trace(frames=[_frame(lineno=1), _frame(filename="extra.py", lineno=99)])
    diff = compare_traces(left, right)
    assert diff.added_count == 1
    assert diff.removed_count == 0


def test_removed_frame_detected():
    left = _trace(frames=[_frame(lineno=1), _frame(filename="extra.py", lineno=99)])
    right = _trace(frames=[_frame(lineno=1)])
    diff = compare_traces(left, right)
    assert diff.removed_count == 1
    assert diff.added_count == 0


def test_has_differences_true_when_frame_added():
    left = _trace(frames=[_frame(lineno=1)])
    right = _trace(frames=[_frame(lineno=1), _frame(filename="new.py", lineno=5)])
    diff = compare_traces(left, right)
    assert diff.has_differences is True


def test_frame_diff_kind_values():
    left = _trace(frames=[_frame(filename="a.py", lineno=1)])
    right = _trace(frames=[_frame(filename="b.py", lineno=2)])
    diff = compare_traces(left, right)
    kinds = {fd.kind for fd in diff.frame_diffs}
    assert kinds == {"added", "removed"}


# --- format_diff --------------------------------------------------------------

def test_format_diff_returns_string():
    diff = compare_traces(_trace(), _trace())
    result = format_diff(diff)
    assert isinstance(result, str)


def test_format_diff_no_differences_message():
    t = _trace()
    diff = compare_traces(t, t)
    result = format_diff(diff, colour=False)
    assert "No differences" in result


def test_format_diff_shows_added_frame():
    left = _trace(frames=[_frame(lineno=1)])
    right = _trace(frames=[_frame(lineno=1), _frame(filename="new.py", lineno=5)])
    diff = compare_traces(left, right)
    result = format_diff(diff, colour=False)
    assert "new.py" in result
    assert "+" in result


def test_format_diff_shows_removed_frame():
    left = _trace(frames=[_frame(lineno=1), _frame(filename="old.py", lineno=3)])
    right = _trace(frames=[_frame(lineno=1)])
    diff = compare_traces(left, right)
    result = format_diff(diff, colour=False)
    assert "old.py" in result
    assert "-" in result


def test_format_diff_no_colour_has_no_ansi():
    left = _trace(exc="ValueError")
    right = _trace(exc="TypeError")
    diff = compare_traces(left, right)
    result = format_diff(diff, colour=False)
    assert "\033[" not in result
