"""Tests for stacktrace_lens.zipper."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.zipper import (
    ZipReport,
    ZippedPair,
    zip_traces,
)


def _frame(filename: str, lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame, exc: str = "ValueError", msg: str = "oops") -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=list(frames),
    )


def test_zip_traces_returns_zip_report():
    t = _trace(_frame("a.py"))
    report = zip_traces(t, t)
    assert isinstance(report, ZipReport)


def test_zip_report_count_equals_longer_trace():
    left = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    right = _trace(_frame("a.py"))
    report = zip_traces(left, right)
    assert report.count == 3


def test_zip_report_stores_exception_types():
    left = _trace(_frame("a.py"), exc="ValueError")
    right = _trace(_frame("b.py"), exc="TypeError")
    report = zip_traces(left, right)
    assert report.left_exception == "ValueError"
    assert report.right_exception == "TypeError"


def test_zipped_pair_is_aligned_when_same_file_and_function():
    f = _frame("app.py", function="run")
    pair = ZippedPair(left=f, right=f)
    assert pair.is_aligned() is True


def test_zipped_pair_not_aligned_when_different_file():
    pair = ZippedPair(left=_frame("a.py"), right=_frame("b.py"))
    assert pair.is_aligned() is False


def test_zipped_pair_not_aligned_when_left_is_none():
    pair = ZippedPair(left=None, right=_frame("a.py"))
    assert pair.is_aligned() is False


def test_zipped_pair_not_aligned_when_right_is_none():
    pair = ZippedPair(left=_frame("a.py"), right=None)
    assert pair.is_aligned() is False


def test_aligned_count_all_matching():
    f = _frame("app.py", function="run")
    left = _trace(f, f)
    right = _trace(f, f)
    report = zip_traces(left, right)
    assert report.aligned_count == 2
    assert report.misaligned_count == 0


def test_misaligned_count_with_padding():
    left = _trace(_frame("a.py"), _frame("b.py"))
    right = _trace(_frame("a.py"))
    report = zip_traces(left, right)
    # second pair has right=None -> misaligned
    assert report.misaligned_count >= 1


def test_summary_line_contains_exception_types():
    left = _trace(_frame("a.py"), exc="KeyError")
    right = _trace(_frame("b.py"), exc="IndexError")
    report = zip_traces(left, right)
    summary = report.summary_line()
    assert "KeyError" in summary
    assert "IndexError" in summary


def test_zipped_pair_str_contains_filenames():
    pair = ZippedPair(left=_frame("left.py"), right=_frame("right.py"))
    s = str(pair)
    assert "left.py" in s
    assert "right.py" in s


def test_zipped_pair_str_missing_when_none():
    pair = ZippedPair(left=_frame("only.py"), right=None)
    assert "<missing>" in str(pair)


def test_empty_traces_produce_empty_report():
    left = _trace()
    right = _trace()
    report = zip_traces(left, right)
    assert report.count == 0
    assert report.aligned_count == 0
