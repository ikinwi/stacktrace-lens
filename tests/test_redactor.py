"""Tests for stacktrace_lens.redactor."""
from __future__ import annotations

import re
import argparse

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.redactor import (
    RedactOptions,
    RedactReport,
    redact_trace,
)


def _frame(filename="app.py", lineno=10, function="run", line="") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line=line)


def _trace(msg="error", exc="ValueError", framesn    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=frames or [_frame()],
    )


def test_redact_returns_report():
    t = _trace()
    report = redact_trace(t)
    assert isinstance(report, RedactReport)


def test_report_trace_is_stack_trace():
    t = _trace()
    report = redact_trace(t)
    assert isinstance(report.trace, StackTrace)


def test_no_sensitive_data_zero_redactions():
    t = _trace(msg="simple error")
    report = redact_trace(t)
    assert report.redacted_count == 0


def test_password_in_message_is_redacted():
    t = _trace(msg="login failed password=s3cr3t")
    report = redact_trace(t)
    assert "password=" not in report.trace.exception_message
    assert report.redacted_count >= 1


def test_token_in_message_is_redacted():
    t = _trace(msg="request failed token=abc123")
    report = redact_trace(t)
    assert "token=abc123" not in report.trace.exception_message


def test_jwt_in_message_is_redacted():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    t = _trace(msg=f"auth error: {jwt}")
    report = redact_trace(t)
    assert jwt not in report.trace.exception_message
    assert report.redacted_count >= 1


def test_ip_not_redacted_by_default():
    t = _trace(msg="connect failed to 192.168.1.1")
    report = redact_trace(t)
    assert "192.168.1.1" in report.trace.exception_message


def test_ip_redacted_when_option_set():
    t = _trace(msg="connect failed to 192.168.1.1")
    opts = RedactOptions(redact_ips=True)
    report = redact_trace(t, opts)
    assert "192.168.1.1" not in report.trace.exception_message


def test_frame_line_is_redacted():
    fr = _frame(line="db.connect(password=hunter2)")
    t = _trace(frames=[fr])
    report = redact_trace(t)
    assert "hunter2" not in report.trace.frames[0].line


def test_extra_pattern_is_applied():
    pat = re.compile(r"ACCT-\d+")
    t = _trace(msg="failed for ACCT-99887")
    opts = RedactOptions(extra_patterns=[pat])
    report = redact_trace(t, opts)
    assert "ACCT-99887" not in report.trace.exception_message
    assert report.redacted_count >= 1


def test_custom_placeholder_used():
    t = _trace(msg="token=abc")
    opts = RedactOptions(placeholder="***")
    report = redact_trace(t, opts)
    assert "***" in report.trace.exception_message


def test_affected_fields_recorded():
    t = _trace(msg="token=abc password=xyz")
    report = redact_trace(t)
    assert "token" in report.affected_fields
    assert "password" in report.affected_fields


def test_summary_line_no_redactions():
    t = _trace(msg="simple")
    report = redact_trace(t)
    assert "No sensitive" in report.summary_line()


def test_summary_line_with_redactions():
    t = _trace(msg="token=abc")
    report = redact_trace(t)
    line = report.summary_line()
    assert "redaction" in line.lower()
