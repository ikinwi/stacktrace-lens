"""Tests for stacktrace_lens.capper."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.capper import CapOptions, CapReport, cap_trace


def _frame(filename: str = "app.py", lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(n: int = 5) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=[_frame(lineno=i) for i in range(1, n + 1)],
    )


# ── basic return type ────────────────────────────────────────────────────────

def test_cap_returns_cap_report():
    report = cap_trace(_trace())
    assert isinstance(report, CapReport)


def test_cap_report_original_count_matches_trace():
    t = _trace(7)
    report = cap_trace(t)
    assert report.original_count == 7


# ── tail (default) behaviour ─────────────────────────────────────────────────

def test_default_keeps_tail_frames():
    t = _trace(10)
    report = cap_trace(t, CapOptions(max_frames=3, keep="tail"))
    assert report.kept_count == 3
    # last 3 linenos are 8, 9, 10
    assert [f.lineno for f in report.frames] == [8, 9, 10]


def test_tail_no_truncation_when_under_limit():
    t = _trace(4)
    report = cap_trace(t, CapOptions(max_frames=10, keep="tail"))
    assert report.kept_count == 4
    assert not report.was_capped


# ── head behaviour ───────────────────────────────────────────────────────────

def test_head_keeps_first_frames():
    t = _trace(10)
    report = cap_trace(t, CapOptions(max_frames=3, keep="head"))
    assert report.kept_count == 3
    assert [f.lineno for f in report.frames] == [1, 2, 3]


def test_head_no_truncation_when_under_limit():
    t = _trace(3)
    report = cap_trace(t, CapOptions(max_frames=10, keep="head"))
    assert not report.was_capped


# ── edge cases ───────────────────────────────────────────────────────────────

def test_zero_max_frames_returns_empty():
    t = _trace(5)
    report = cap_trace(t, CapOptions(max_frames=0))
    assert report.kept_count == 0
    assert report.was_capped


def test_exact_limit_does_not_cap():
    t = _trace(5)
    report = cap_trace(t, CapOptions(max_frames=5))
    assert not report.was_capped
    assert report.kept_count == 5


# ── derived properties ────────────────────────────────────────────────────────

def test_dropped_count_is_difference():
    t = _trace()
    report = cap_trace(t, CapOptions(max_frames=3))
    assert report.dropped_count == 5


def test_summary_cap():
    t = _trace(3)
    report = cap_trace(t, CapOptions(max))
    assert "No frames dropped" in report.summary_line()


def test_summary_line_with_cap():
    t = _trace(6)
    report = cap_trace(t, CapOptions(max_frames=2))
    line = report.summary_line()
    assert "6" in line
    assert "2" in line


# ── as_trace round-trip ───────────────────────────────────────────────────────

def test_as_trace_returns_stack_trace():
    from stacktrace_lens.parser import StackTrace as ST
    t = _trace(5)
    report = cap_trace(t, CapOptions(max_frames=3))
    result = report.as_trace()
    assert isinstance(result, ST)
    assert len(result.frames) == 3
    assert result.exception_type == "ValueError"
