"""Tests for stacktrace_lens.extractor."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.extractor import (
    ExtractOptions,
    ExtractReport,
    extract_frames,
)


def _frame(filename: str, lineno: int, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=name, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# Basic return-type checks
# ---------------------------------------------------------------------------

def test_extract_returns_report():
    t = _trace(_frame("a.py", 1))
    report = extract_frames(t)
    assert isinstance(report, ExtractReport)


def test_no_options_keeps_all_frames():
    t = _trace(_frame("a.py", 1), _frame("b.py", 2), _frame("c.py", 3))
    report = extract_frames(t)
    assert report.extracted_count == 3
    assert report.original_count == 3


# ---------------------------------------------------------------------------
# head / tail
# ---------------------------------------------------------------------------

def test_head_keeps_first_n_frames():
    t = _trace(_frame("a.py", 1), _frame("b.py", 2), _frame("c.py", 3))
    report = extract_frames(t, ExtractOptions(head=2))
    assert report.extracted_count == 2
    assert report.frames[0].filename == "a.py"
    assert report.frames[1].filename == "b.py"


def test_tail_keeps_last_n_frames():
    t = _trace(_frame("a.py", 1), _frame("b.py", 2), _frame("c.py", 3))
    report = extract_frames(t, ExtractOptions(tail=1))
    assert report.extracted_count == 1
    assert report.frames[0].filename == "c.py"


def test_tail_zero_returns_empty():
    t = _trace(_frame("a.py", 1), _frame("b.py", 2))
    report = extract_frames(t, ExtractOptions(tail=0))
    assert report.extracted_count == 0


# ---------------------------------------------------------------------------
# filename_contains
# ---------------------------------------------------------------------------

def test_filename_contains_filters_correctly():
    t = _trace(_frame("app/views.py", 10), _frame("lib/utils.py", 20))
    report = extract_frames(t, ExtractOptions(filename_contains="app"))
    assert report.extracted_count == 1
    assert report.frames[0].filename == "app/views.py"


def test_filename_contains_no_match_returns_empty():
    t = _trace(_frame("a.py", 1), _frame("b.py", 2))
    report = extract_frames(t, ExtractOptions(filename_contains="zzz"))
    assert report.extracted_count == 0


# ---------------------------------------------------------------------------
# around_line
# ---------------------------------------------------------------------------

def test_around_line_returns_matching_frame():
    frames = [_frame("a.py", i) for i in range(1, 11)]
    t = _trace(*frames)
    report = extract_frames(t, ExtractOptions(around_line=5, window=0))
    assert all(f.lineno == 5 for f in report.frames)


def test_around_line_no_match_returns_empty():
    t = _trace(_frame("a.py", 1), _frame("a.py", 2))
    report = extract_frames(t, ExtractOptions(around_line=99, window=0))
    assert report.extracted_count == 0


# ---------------------------------------------------------------------------
# summary_line / as_trace
# ---------------------------------------------------------------------------

def test_summary_line_contains_counts():
    t = _trace(_frame("a.py", 1), _frame("b.py", 2))
    report = extract_frames(t, ExtractOptions(head=1))
    summary = report.summary_line()
    assert "1" in summary
    assert "2" in summary


def test_as_trace_returns_stack_trace():
    from stacktrace_lens.parser import StackTrace as ST
    t = _trace(_frame("a.py", 1), _frame("b.py", 2))
    report = extract_frames(t, ExtractOptions(head=1))
    result = report.as_trace()
    assert isinstance(result, ST)
    assert len(result.frames) == 1
