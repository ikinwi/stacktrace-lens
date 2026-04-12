"""Tests for stacktrace_lens.highlighter."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.highlighter import (
    HighlightOptions,
    HighlightedFrame,
    HighlightReport,
    highlight_frames,
    format_highlight,
)


def _frame(filename: str = "/app/main.py", lineno: int = 10, function: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _trace(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "bad value") -> StackTrace:
    return StackTrace(
        frames=list(frames) if frames else [_frame()],
        exception_type=exc_type,
        exception_message=exc_msg,
    )


# --- highlight_frames ---

def test_highlight_frames_returns_report():
    report = highlight_frames(_trace())
    assert isinstance(report, HighlightReport)


def test_report_frames_are_highlighted_frames():
    report = highlight_frames(_trace())
    for hf in report.frames:
        assert isinstance(hf, HighlightedFrame)


def test_frame_count_matches_trace():
    t = _trace(_frame(), _frame(), _frame())
    report = highlight_frames(t)
    assert report.count == 3


def test_default_highlights_last_frame_as_origin():
    t = _trace(_frame("/app/a.py"), _frame("/app/b.py"))
    report = highlight_frames(t)
    assert report.frames[-1].highlighted is True
    assert report.frames[-1].reason == "exception origin"


def test_default_does_not_highlight_non_last_frames():
    t = _trace(_frame("/app/a.py"), _frame("/app/b.py"))
    report = highlight_frames(t)
    assert report.frames[0].highlighted is False


def test_pattern_highlights_matching_frame():
    t = _trace(_frame("/app/models.py"), _frame("/app/views.py"))
    opts = HighlightOptions(patterns=["models"], highlight_exception_origin=False)
    report = highlight_frames(t, opts)
    assert report.frames[0].highlighted is True
    assert report.frames[1].highlighted is False


def test_pattern_no_match_leaves_frame_unhighlighted():
    t = _trace(_frame("/app/utils.py"))
    opts = HighlightOptions(patterns=["nonexistent"], highlight_exception_origin=False)
    report = highlight_frames(t, opts)
    assert report.frames[0].highlighted is False


def test_user_code_highlights_non_stdlib():
    t = _trace(_frame("/app/main.py"))
    opts = HighlightOptions(highlight_user_code=True, highlight_exception_origin=False)
    report = highlight_frames(t, opts)
    assert report.frames[0].highlighted is True
    assert report.frames[0].reason == "user code"


def test_user_code_does_not_highlight_stdlib():
    t = _trace(_frame("/usr/lib/python3.11/os.py"))
    opts = HighlightOptions(highlight_user_code=True, highlight_exception_origin=False)
    report = highlight_frames(t, opts)
    assert report.frames[0].highlighted is False


def test_highlighted_count_reflects_highlights():
    t = _trace(_frame("/app/a.py"), _frame("/app/b.py"))
    opts = HighlightOptions(patterns=["a.py"], highlight_exception_origin=False)
    report = highlight_frames(t, opts)
    assert report.highlighted_count == 1


def test_summary_line_contains_exception_type():
    t = _trace(exc_type="RuntimeError")
    report = highlight_frames(t)
    assert "RuntimeError" in report.summary_line()


def test_summary_line_contains_counts():
    t = _trace(_frame(), _frame())
    report = highlight_frames(t)
    line = report.summary_line()
    assert "/" in line


# --- format_highlight ---

def test_format_highlight_returns_string():
    report = highlight_frames(_trace())
    result = format_highlight(report)
    assert isinstance(result, str)


def test_format_highlight_contains_filename():
    t = _trace(_frame("/app/main.py"))
    report = highlight_frames(t)
    result = format_highlight(report)
    assert "/app/main.py" in result


def test_format_highlight_marks_highlighted_frame():
    t = _trace(_frame("/app/only.py"))
    opts = HighlightOptions(highlight_exception_origin=True)
    report = highlight_frames(t, opts)
    result = format_highlight(report)
    assert ">>>" in result


def test_format_highlight_colour_adds_escape_codes():
    report = highlight_frames(_trace())
    result = format_highlight(report, colour=True)
    assert "\033[" in result
