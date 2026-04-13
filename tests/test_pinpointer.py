"""Tests for stacktrace_lens.pinpointer."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.pinpointer import (
    PinpointResult,
    format_pinpoint,
    pinpoint_trace,
)


def _frame(filename: str, lineno: int = 10, function: str = "func") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame, exc: str = "ValueError", msg: str = "bad") -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=list(frames),
    )


# --- PinpointResult ---

def test_pinpoint_returns_pinpoint_result():
    t = _trace(_frame("app/main.py"))
    result = pinpoint_trace(t)
    assert isinstance(result, PinpointResult)


def test_empty_trace_best_frame_is_none():
    t = _trace(exc="RuntimeError", msg="oops")
    result = pinpoint_trace(t)
    assert result.best_frame is None
    assert result.best_index is None


def test_single_frame_is_best():
    f = _frame("app/views.py", lineno=42)
    t = _trace(f)
    result = pinpoint_trace(t)
    assert result.best_frame is f
    assert result.best_index == 0


def test_scores_length_matches_frames():
    frames = [_frame(f"app/mod{i}.py") for i in range(5)]
    t = _trace(*frames)
    result = pinpoint_trace(t)
    assert len(result.scores) == 5


def test_noise_frame_scores_lower_than_user_frame():
    noise = _frame("/usr/lib/python3.11/traceback.py", lineno=5)
    user = _frame("app/service.py", lineno=20)
    t = _trace(noise, user)
    result = pinpoint_trace(t)
    assert result.scores[1] > result.scores[0]


def test_innermost_user_frame_preferred():
    f1 = _frame("app/a.py", lineno=1)
    f2 = _frame("app/b.py", lineno=2)
    f3 = _frame("app/c.py", lineno=3)
    t = _trace(f1, f2, f3)
    result = pinpoint_trace(t)
    # Last frame should have highest position bonus
    assert result.best_index == 2


def test_frozen_module_is_noise():
    frozen = _frame("<frozen importlib._bootstrap>", lineno=1)
    user = _frame("myapp/loader.py", lineno=8)
    t = _trace(frozen, user)
    result = pinpoint_trace(t)
    assert result.best_frame is user


def test_summary_line_contains_filename():
    f = _frame("app/handler.py", lineno=99, function="handle")
    t = _trace(f)
    result = pinpoint_trace(t)
    assert "app/handler.py" in result.summary_line


def test_summary_line_no_frames():
    t = _trace(exc="IOError", msg="missing")
    result = pinpoint_trace(t)
    assert "No frames" in result.summary_line


# --- format_pinpoint ---

def test_format_pinpoint_returns_string():
    t = _trace(_frame("app/x.py"))
    result = pinpoint_trace(t)
    out = format_pinpoint(result)
    assert isinstance(out, str)


def test_format_pinpoint_contains_exception_type():
    t = _trace(_frame("app/x.py"), exc="KeyError")
    result = pinpoint_trace(t)
    out = format_pinpoint(result, colour=False)
    assert "KeyError" in out


def test_format_pinpoint_marks_best_frame():
    f1 = _frame("app/a.py", lineno=1)
    f2 = _frame("app/b.py", lineno=2)
    t = _trace(f1, f2)
    result = pinpoint_trace(t)
    out = format_pinpoint(result, colour=False)
    assert ">>" in out
