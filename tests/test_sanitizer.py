"""Tests for stacktrace_lens.sanitizer."""

from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.sanitizer import (
    SanitizeOptions,
    format_sanitize_report,
    sanitize_frame,
    sanitize_trace,
)


def _frame(filename: str = "app.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source="x = 1")


def _trace(
    exc_type: str = "ValueError",
    message: str = "bad value",
    frames=None,
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=message, frames=frames)


# ---------------------------------------------------------------------------
# sanitize_frame
# ---------------------------------------------------------------------------

def test_sanitize_frame_returns_frame():
    result = sanitize_frame(_frame())
    assert isinstance(result, Frame)


def test_sanitize_frame_redacts_home_path():
    f = _frame(filename="/home/alice/project/app.py")
    result = sanitize_frame(f)
    assert "alice" not in result.filename
    assert "<USER>" in result.filename


def test_sanitize_frame_redacts_users_path():
    f = _frame(filename="/Users/bob/dev/app.py")
    result = sanitize_frame(f)
    assert "bob" not in result.filename


def test_sanitize_frame_preserves_lineno_and_function():
    f = _frame(lineno=42, function="my_func")
    result = sanitize_frame(f)
    assert result.lineno == 42
    assert result.function == "my_func"


def test_sanitize_frame_no_redact_paths_keeps_path():
    f = _frame(filename="/home/alice/app.py")
    opts = SanitizeOptions(redact_paths=False)
    result = sanitize_frame(f, opts)
    assert result.filename == "/home/alice/app.py"


# ---------------------------------------------------------------------------
# sanitize_trace
# ---------------------------------------------------------------------------

def test_sanitize_trace_returns_stacktrace():
    result = sanitize_trace(_trace())
    assert isinstance(result, StackTrace)


def test_sanitize_trace_redacts_password_in_message():
    t = _trace(message="login failed password=secret123")
    result = sanitize_trace(t)
    assert "secret123" not in result.exception_message
    assert "<REDACTED>" in result.exception_message


def test_sanitize_trace_redacts_token_in_message():
    t = _trace(message="request failed token=abc.def.ghi")
    result = sanitize_trace(t)
    assert "abc.def.ghi" not in result.exception_message


def test_sanitize_trace_redacts_email_in_message():
    t = _trace(message="user alice@example.com not found")
    result = sanitize_trace(t)
    assert "alice@example.com" not in result.exception_message
    assert "<EMAIL>" in result.exception_message


def test_sanitize_trace_redacts_ip_in_message():
    t = _trace(message="connection refused 192.168.1.100")
    result = sanitize_trace(t)
    assert "192.168.1.100" not in result.exception_message
    assert "<IP>" in result.exception_message


def test_sanitize_trace_sanitizes_all_frames():
    """All frames in a trace should have paths sanitized."""
    frames = [
        _frame(filename="/home/alice/project/app.py"),
        _frame(filename="/home/alice/project/utils.py"),
    ]
    result = sanitize_trace(_trace(frames=frames))
    for frame in result.frames:
        assert "alice" not in frame.filename
        assert "<USER>" in frame.filename
