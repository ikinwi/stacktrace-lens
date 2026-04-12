"""Tests for stacktrace_lens.validator."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.validator import (
    ValidateOptions,
    ValidationReport,
    ValidationViolation,
    format_validation,
    validate_trace,
)


def _make_trace(
    exception_type: str = "ValueError",
    exception_message: str = "bad value",
    frames: int = 2,
) -> StackTrace:
    fs = [
        Frame(filename=f"app/mod{i}.py", lineno=i + 1, function=f"func{i}", context="")
        for i in range(frames)
    ]
    return StackTrace(exception_type=exception_type, exception_message=exception_message, frames=fs)


def test_validate_returns_report():
    trace = _make_trace()
    report = validate_trace(trace)
    assert isinstance(report, ValidationReport)


def test_no_options_valid_trace_has_no_violations():
    trace = _make_trace()
    report = validate_trace(trace)
    assert report.is_valid
    assert report.violation_count == 0


def test_max_depth_no_violation_when_within_limit():
    trace = _make_trace(frames=3)
    report = validate_trace(trace, ValidateOptions(max_depth=5))
    assert report.is_valid


def test_max_depth_violation_when_exceeded():
    trace = _make_trace(frames=6)
    report = validate_trace(trace, ValidateOptions(max_depth=5))
    assert not report.is_valid
    assert any(v.rule == "max_depth" for v in report.violations)


def test_require_message_no_violation_when_present():
    trace = _make_trace(exception_message="something went wrong")
    report = validate_trace(trace, ValidateOptions(require_message=True))
    assert report.is_valid


def test_require_message_violation_when_empty():
    trace = _make_trace(exception_message="")
    report = validate_trace(trace, ValidateOptions(require_message=True))
    assert not report.is_valid
    assert any(v.rule == "require_message" for v in report.violations)


def test_disallow_empty_frames_violation():
    frames = [Frame(filename="", lineno=1, function="", context="")]
    trace = StackTrace(exception_type="E", exception_message="m", frames=frames)
    report = validate_trace(trace, ValidateOptions(disallow_empty_frames=True))
    assert not report.is_valid
    assert any(v.rule == "disallow_empty_frames" for v in report.violations)


def test_known_exception_types_no_violation():
    trace = _make_trace(exception_type="ValueError")
    report = validate_trace(trace, ValidateOptions(known_exception_types=["ValueError", "TypeError"]))
    assert report.is_valid


def test_known_exception_types_violation():
    trace = _make_trace(exception_type="CustomError")
    report = validate_trace(trace, ValidateOptions(known_exception_types=["ValueError"]))
    assert not report.is_valid
    assert any(v.rule == "known_exception_types" for v in report.violations)


def test_violation_str_contains_rule_and_message():
    v = ValidationViolation(rule="max_depth", message="too deep")
    assert "max_depth" in str(v)
    assert "too deep" in str(v)


def test_summary_line_valid():
    trace = _make_trace()
    report = validate_trace(trace)
    assert "valid" in report.summary_line().lower()


def test_summary_line_invalid():
    trace = _make_trace(frames=10)
    report = validate_trace(trace, ValidateOptions(max_depth=3))
    assert "violation" in report.summary_line().lower()


def test_format_validation_returns_string():
    trace = _make_trace()
    report = validate_trace(trace)
    assert isinstance(format_validation(report), str)


def test_format_validation_no_colour():
    trace = _make_trace()
    report = validate_trace(trace)
    result = format_validation(report, colour=False)
    assert "\033[" not in result
