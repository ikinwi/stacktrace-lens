"""Tests for stacktrace_lens.splitter2."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.splitter2 import (
    Segment,
    SegmentReport,
    _package_of,
    segment_trace,
)


def _frame(filename: str = "app/main.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(*frames: Frame, exc_type: str = "ValueError") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message="oops",
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# _package_of
# ---------------------------------------------------------------------------

def test_package_of_returns_top_level_dir() -> None:
    frame = _frame(filename="myapp/utils/helper.py")
    assert _package_of(frame) == "myapp"


def test_package_of_unknown_for_empty_filename() -> None:
    frame = _frame(filename="")
    assert _package_of(frame) == "<unknown>"


def test_package_of_handles_windows_paths() -> None:
    frame = _frame(filename="myapp\\module\\core.py")
    assert _package_of(frame) == "myapp"


# ---------------------------------------------------------------------------
# segment_trace
# ---------------------------------------------------------------------------

def test_segment_trace_returns_segment_report() -> None:
    trace = _trace(_frame())
    report = segment_trace(trace)
    assert isinstance(report, SegmentReport)


def test_segment_report_stores_trace() -> None:
    trace = _trace(_frame())
    report = segment_trace(trace)
    assert report.trace is trace


def test_single_frame_produces_one_segment() -> None:
    trace = _trace(_frame(filename="app/main.py"))
    report = segment_trace(trace)
    assert report.count == 1


def test_consecutive_same_package_merged() -> None:
    f1 = _frame(filename="app/a.py")
    f2 = _frame(filename="app/b.py")
    trace = _trace(f1, f2)
    report = segment_trace(trace)
    assert report.count == 1
    assert report.segments[0].count == 2


def test_different_packages_produce_multiple_segments() -> None:
    f1 = _frame(filename="app/a.py")
    f2 = _frame(filename="lib/x.py")
    f3 = _frame(filename="app/b.py")
    trace = _trace(f1, f2, f3)
    report = segment_trace(trace)
    assert report.count == 3


def test_segment_labels() -> None:
    f1 = _frame(filename="django/db/models.py")
    f2 = _frame(filename="myapp/views.py")
    trace = _trace(f1, f2)
    report = segment_trace(trace)
    assert report.segments[0].label == "django"
    assert report.segments[1].label == "myapp"


def test_segment_str_contains_label() -> None:
    seg = Segment(label="myapp", frames=[_frame()])
    assert "myapp" in str(seg)


def test_summary_line_contains_exception_type() -> None:
    trace = _trace(_frame(), exc_type="RuntimeError")
    report = segment_trace(trace)
    assert "RuntimeError" in report.summary_line()


def test_empty_trace_produces_no_segments() -> None:
    trace = _trace()
    report = segment_trace(trace)
    assert report.count == 0
