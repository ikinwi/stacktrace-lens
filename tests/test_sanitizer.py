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
    assert "<IP_ADDRESS>" in result.exception_message


def test_sanitize_trace_no_redact_message_keeps_message():
    original_msg = "password=topsecret"
    t = _trace(message=original_msg)
    opts = SanitizeOptions(redact_message=False)
    result = sanitize_trace(t, opts)
    assert result.exception_message == original_msg


def test_sanitize_trace_extra_patterns():
    t = _trace(message="session_id=abc123xyz")
    opts = SanitizeOptions(extra_patterns=[(r'session_id=\S+', 'session_id=<REDACTED>')])
    result = sanitize_trace(t, opts)
    assert "abc123xyz" not in result.exception_message


def test_sanitize_trace_preserves_exception_type():
    t = _trace(exc_type="RuntimeError")
    result = sanitize_trace(t)
    assert result.exception_type == "RuntimeError"


# ---------------------------------------------------------------------------
# format_sanitize_report
# ---------------------------------------------------------------------------

def test_format_sanitize_report_returns_string():
    t = _trace()
    result = format_sanitize_report(t, sanitize_trace(t))
    assert isinstance(result, str)


def test_format_sanitize_report_shows_message_redaction():
    original = _trace(message="password=secret")
    sanitized = sanitize_trace(original)
    report = format_sanitize_report(original, sanitized)
    assert "message" in report


def test_format_sanitize_report_no_changes_noted():
    t = _trace(message="simple error")
    sanitized = sanitize_trace(t)
    report = format_sanitize_report(t, sanitized)
    assert "no sensitive data detected" in report
