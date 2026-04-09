"""Tests for stacktrace_lens.severity."""

from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.severity import (
    SeverityResult,
    _depth_bonus,
    _label_for_score,
    format_severity,
    score_trace,
)


def _make_trace(exc_type: str, num_frames: int = 3) -> StackTrace:
    frames = [
        Frame(filename=f"file{i}.py", lineno=i, function=f"fn{i}", source=None)
        for i in range(num_frames)
    ]
    return StackTrace(exception_type=exc_type, message="msg", frames=frames)


def test_score_trace_returns_severity_result():
    trace = _make_trace("ValueError")
    result = score_trace(trace)
    assert isinstance(result, SeverityResult)


def test_score_trace_known_exception():
    trace = _make_trace("MemoryError")
    result = score_trace(trace)
    assert result.score >= 9
    assert result.label in ("HIGH", "CRITICAL")


def test_score_trace_unknown_exception_defaults_to_medium():
    trace = _make_trace("SomeObscureError")
    result = score_trace(trace)
    assert 1 <= result.score <= 6


def test_score_trace_stores_exception_type():
    trace = _make_trace("TypeError")
    result = score_trace(trace)
    assert result.exception_type == "TypeError"


def test_score_trace_stores_frame_count():
    trace = _make_trace("KeyError", num_frames=5)
    result = score_trace(trace)
    assert result.frame_count == 5


def test_depth_bonus_deep_trace():
    assert _depth_bonus(20) == 2
    assert _depth_bonus(25) == 2


def test_depth_bonus_medium_trace():
    assert _depth_bonus(10) == 1
    assert _depth_bonus(15) == 1


def test_depth_bonus_shallow_trace():
    assert _depth_bonus(3) == 0
    assert _depth_bonus(9) == 0


def test_label_for_score_low():
    assert _label_for_score(1) == "LOW"
    assert _label_for_score(2) == "LOW"


def test_label_for_score_medium():
    assert _label_for_score(3) == "MEDIUM"
    assert _label_for_score(5) == "MEDIUM"


def test_label_for_score_high():
    assert _label_for_score(6) == "HIGH"
    assert _label_for_score(7) == "HIGH"


def test_label_for_score_critical():
    assert _label_for_score(8) == "CRITICAL"
    assert _label_for_score(10) == "CRITICAL"


def test_format_severity_returns_string():
    result = SeverityResult(score=5, label="MEDIUM", exception_type="ValueError", frame_count=4)
    output = format_severity(result)
    assert isinstance(output, str)


def test_format_severity_contains_label():
    result = SeverityResult(score=8, label="CRITICAL", exception_type="MemoryError", frame_count=2)
    output = format_severity(result, colour=False)
    assert "CRITICAL" in output


def test_format_severity_contains_score():
    result = SeverityResult(score=5, label="MEDIUM", exception_type="TypeError", frame_count=3)
    output = format_severity(result, colour=False)
    assert "5" in output


def test_format_severity_no_colour_no_escape_codes():
    result = SeverityResult(score=3, label="MEDIUM", exception_type="KeyError", frame_count=1)
    output = format_severity(result, colour=False)
    assert "\033[" not in output
