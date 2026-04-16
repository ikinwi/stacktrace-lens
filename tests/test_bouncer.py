"""Tests for stacktrace_lens.bouncer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.bouncer import (
    BounceOptions,
    BounceResult,
    bounce_trace,
    format_bounce,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "main") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(
    exc_type: str = "ValueError",
    message: str = "bad value",
    depth: int = 3,
) -> StackTrace:
    frames = [_frame(lineno=i) for i in range(depth)]
    return StackTrace(exception_type=exc_type, exception_message=message, frames=frames)


def test_bounce_returns_bounce_result():
    result = bounce_trace(_trace())
    assert isinstance(result, BounceResult)


def test_no_options_accepts_trace():
    result = bounce_trace(_trace())
    assert result.accepted is True
    assert result.reason is None


def test_max_depth_accepts_within_limit():
    result = bounce_trace(_trace(depth=3), BounceOptions(max_depth=5))
    assert result.accepted is True


def test_max_depth_rejects_when_exceeded():
    result = bounce_trace(_trace(depth=10), BounceOptions(max_depth=5))
    assert result.accepted is False
    assert "depth" in result.reason


def test_blocked_exceptions_rejects_match():
    opts = BounceOptions(blocked_exceptions=["ValueError"])
    result = bounce_trace(_trace(exc_type="ValueError"), opts)
    assert result.accepted is False
    assert "blocked" in result.reason


def test_blocked_exceptions_accepts_non_match():
    opts = BounceOptions(blocked_exceptions=["RuntimeError"])
    result = bounce_trace(_trace(exc_type="ValueError"), opts)
    assert result.accepted is True


def test_allowed_exceptions_accepts_match():
    opts = BounceOptions(allowed_exceptions=["ValueError", "TypeError"])
    result = bounce_trace(_trace(exc_type="TypeError"), opts)
    assert result.accepted is True


def test_allowed_exceptions_rejects_non_match():
    opts = BounceOptions(allowed_exceptions=["RuntimeError"])
    result = bounce_trace(_trace(exc_type="ValueError"), opts)
    assert result.accepted is False
    assert "allowed" in result.reason


def test_max_message_length_accepts_short():
    opts = BounceOptions(max_message_length=100)
    result = bounce_trace(_trace(message="short"), opts)
    assert result.accepted is True


def test_max_message_length_rejects_long():
    opts = BounceOptions(max_message_length=5)
    result = bounce_trace(_trace(message="this message is too long"), opts)
    assert result.accepted is False
    assert "message length" in result.reason


def test_str_accepted():
    result = bounce_trace(_trace())
    assert "ACCEPTED" in str(result)


def test_str_rejected_contains_reason():
    opts = BounceOptions(max_depth=1)
    result = bounce_trace(_trace(depth=5), opts)
    assert "REJECTED" in str(result)


def test_format_bounce_returns_string():
    result = bounce_trace(_trace())
    output = format_bounce(result)
    assert isinstance(output, str)
    assert "Exception" in output
    assert "Frames" in output
