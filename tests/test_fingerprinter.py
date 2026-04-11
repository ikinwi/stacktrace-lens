"""Tests for stacktrace_lens.fingerprinter."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import StackTrace, Frame
from stacktrace_lens.fingerprinter import (
    FingerprintResult,
    _normalize_message,
    _frame_signature,
    fingerprint_trace,
    format_fingerprint,
)


def _frame(filename="app.py", lineno=10, function="main") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(
    exc_type="ValueError",
    exc_msg="bad value 42",
    frames=None,
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# --- _normalize_message ---

def test_normalize_removes_hex_addresses():
    assert "0xADDR" in _normalize_message("at 0xDEADBEEF")


def test_normalize_replaces_integers():
    assert "N" in _normalize_message("index 7 out of range")
    assert "7" not in _normalize_message("index 7 out of range")


def test_normalize_stable_for_same_input():
    assert _normalize_message("error 99") == _normalize_message("error 99")


# --- _frame_signature ---

def test_frame_signature_format():
    f = _frame(filename="foo.py", function="bar")
    assert _frame_signature(f) == "foo.py:bar"


# --- fingerprint_trace ---

def test_fingerprint_returns_result():
    result = fingerprint_trace(_trace())
    assert isinstance(result, FingerprintResult)


def test_fingerprint_is_64_hex_chars():
    result = fingerprint_trace(_trace())
    assert len(result.fingerprint) == 64
    assert all(c in "0123456789abcdef" for c in result.fingerprint)


def test_same_trace_produces_same_fingerprint():
    t = _trace()
    assert fingerprint_trace(t).fingerprint == fingerprint_trace(t).fingerprint


def test_different_exception_types_differ():
    a = fingerprint_trace(_trace(exc_type="ValueError"))
    b = fingerprint_trace(_trace(exc_type="TypeError"))
    assert a.fingerprint != b.fingerprint


def test_include_message_false_ignores_message():
    t1 = _trace(exc_msg="error 1")
    t2 = _trace(exc_msg="error 2")
    fp1 = fingerprint_trace(t1, include_message=False).fingerprint
    fp2 = fingerprint_trace(t2, include_message=False).fingerprint
    assert fp1 == fp2


def test_max_frames_limits_contribution():
    frames_a = [_frame("a.py"), _frame("b.py"), _frame("c.py")]
    frames_b = [_frame("z.py"), _frame("b.py"), _frame("c.py")]
    t_a = _trace(frames=frames_a)
    t_b = _trace(frames=frames_b)
    # With max_frames=2 only last two frames matter — both share b.py:main, c.py:main
    fp_a = fingerprint_trace(t_a, max_frames=2).fingerprint
    fp_b = fingerprint_trace(t_b, max_frames=2).fingerprint
    assert fp_a == fp_b


def test_short_returns_8_chars():
    result = fingerprint_trace(_trace())
    assert len(result.short()) == 8


# --- format_fingerprint ---

def test_format_returns_string():
    result = fingerprint_trace(_trace())
    output = format_fingerprint(result)
    assert isinstance(output, str)


def test_format_contains_exception_type():
    result = fingerprint_trace(_trace(exc_type="RuntimeError"))
    assert "RuntimeError" in format_fingerprint(result)


def test_format_short_uses_short_fp():
    result = fingerprint_trace(_trace())
    output_short = format_fingerprint(result, short=True)
    assert result.short() in output_short
    assert result.fingerprint not in output_short
