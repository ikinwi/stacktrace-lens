"""Unit tests for stacktrace_lens.pattern_matcher."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.pattern_matcher import (
    MatchResult,
    PatternMatchReport,
    format_report,
    match_frames,
)


def _frame(filename: str, lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        message="oops",
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# match_frames
# ---------------------------------------------------------------------------

def test_match_frames_returns_report():
    trace = _trace(_frame("/app/views.py"))
    report = match_frames(trace, {"app": r"/app/"})
    assert isinstance(report, PatternMatchReport)


def test_no_patterns_yields_no_matches():
    trace = _trace(_frame("/app/views.py"), _frame("/lib/utils.py"))
    report = match_frames(trace, {})
    assert report.matched_frames == 0
    assert report.matches == []


def test_matching_pattern_captured():
    trace = _trace(_frame("/app/views.py"), _frame("/lib/utils.py"))
    report = match_frames(trace, {"app": r"/app/"})
    assert report.matched_frames == 1
    assert len(report.matches) == 1
    assert report.matches[0].label == "app"


def test_multiple_patterns_first_wins():
    frame = _frame("/app/models.py")
    trace = _trace(frame)
    report = match_frames(trace, {"first": r"/app/", "second": r"models"})
    assert report.matches[0].label == "first"


def test_match_ratio_all_matched():
    trace = _trace(_frame("/app/a.py"), _frame("/app/b.py"))
    report = match_frames(trace, {"app": r"/app/"})
    assert report.match_ratio == 1.0


def test_match_ratio_partial():
    trace = _trace(_frame("/app/a.py"), _frame("/lib/b.py"))
    report = match_frames(trace, {"app": r"/app/"})
    assert report.match_ratio == 0.5


def test_unmatched_count():
    trace = _trace(_frame("/app/a.py"), _frame("/lib/b.py"), _frame("/lib/c.py"))
    report = match_frames(trace, {"app": r"/app/"})
    assert report.unmatched_count == 2


def test_span_stored_on_match():
    trace = _trace(_frame("/app/views.py"))
    report = match_frames(trace, {"app": r"/app/"})
    assert report.matches[0].span is not None


def test_invalid_regex_does_not_raise():
    trace = _trace(_frame("/app/views.py"))
    # Invalid regex should simply not match rather than crash
    report = match_frames(trace, {"bad": r"[invalid"})
    assert report.matched_frames == 0


def test_empty_trace():
    trace = _trace()
    report = match_frames(trace, {"app": r"/app/"})
    assert report.total_frames == 0
    assert report.match_ratio == 0.0


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------

def test_format_report_returns_string():
    trace = _trace(_frame("/app/views.py"))
    report = match_frames(trace, {"app": r"/app/"})
    result = format_report(report)
    assert isinstance(result, str)


def test_format_report_contains_label():
    trace = _trace(_frame("/app/views.py"))
    report = match_frames(trace, {"myapp": r"/app/"})
    result = format_report(report, colour=False)
    assert "myapp" in result


def test_format_report_no_colour_has_no_escape_codes():
    trace = _trace(_frame("/app/views.py"))
    report = match_frames(trace, {"app": r"/app/"})
    result = format_report(report, colour=False)
    assert "\033[" not in result


def test_match_result_str():
    frame = _frame("/app/views.py", lineno=42, function="index")
    mr = MatchResult(frame=frame, pattern=r"/app/", label="app")
    assert "app" in str(mr)
    assert "views.py" in str(mr)
