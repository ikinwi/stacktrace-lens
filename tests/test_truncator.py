"""Tests for stacktrace_lens.truncator."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.truncator import (
    TruncateOptions,
    TruncateReport,
    format_truncation,
    truncate_trace,
)


def _frame(filename: str, lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(n: int, exc: str = "ValueError", msg: str = "oops") -> StackTrace:
    frames = [_frame(f"file_{i}.py", lineno=i + 1) for i in range(n)]
    return StackTrace(frames=frames, exception_type=exc, exception_message=msg)


# --- TruncateReport properties ---

def test_truncate_returns_report():
    report = truncate_trace(_trace(10))
    assert isinstance(report, TruncateReport)


def test_original_count_matches_trace():
    report = truncate_trace(_trace(10))
    assert report.original_count == 10


def test_no_truncation_when_frames_fit():
    opts = TruncateOptions(head=5, tail=5)
    report = truncate_trace(_trace(8), opts)
    assert not report.was_truncated
    assert report.omitted_count == 0
    assert report.placeholder_index == -1


def test_truncation_omits_middle_frames():
    opts = TruncateOptions(head=2, tail=2)
    report = truncate_trace(_trace(10), opts)
    assert report.was_truncated
    assert report.omitted_count == 6
    assert report.kept_count == 4


def test_kept_frames_are_head_plus_tail():
    opts = TruncateOptions(head=2, tail=3)
    trace = _trace(10)
    report = truncate_trace(trace, opts)
    expected_filenames = (
        [f"file_{i}.py" for i in range(2)]
        + [f"file_{i}.py" for i in range(7, 10)]
    )
    assert [f.filename for f in report.frames] == expected_filenames


def test_placeholder_index_equals_head():
    opts = TruncateOptions(head=3, tail=2)
    report = truncate_trace(_trace(10), opts)
    assert report.placeholder_index == 3


def test_exception_type_preserved():
    report = truncate_trace(_trace(5, exc="TypeError"))
    assert report.exception_type == "TypeError"


def test_exception_message_preserved():
    report = truncate_trace(_trace(5, msg="bad value"))
    assert report.exception_message == "bad value"


def test_summary_line_no_truncation():
    opts = TruncateOptions(head=10, tail=10)
    report = truncate_trace(_trace(5), opts)
    assert "no truncation" in report.summary_line()


def test_summary_line_with_truncation():
    opts = TruncateOptions(head=1, tail=1)
    report = truncate_trace(_trace(8), opts)
    assert "omitted" in report.summary_line()


def test_zero_tail_keeps_only_head():
    opts = TruncateOptions(head=3, tail=0)
    report = truncate_trace(_trace(10), opts)
    assert report.kept_count == 3
    assert all(f.filename == f"file_{i}.py" for i, f in enumerate(report.frames))


# --- format_truncation ---

def test_format_truncation_returns_string():
    report = truncate_trace(_trace(10))
    result = format_truncation(report, colour=False)
    assert isinstance(result, str)


def test_format_contains_exception_type():
    report = truncate_trace(_trace(6, exc="RuntimeError"))
    out = format_truncation(report, colour=False)
    assert "RuntimeError" in out


def test_format_contains_placeholder_when_truncated():
    opts = TruncateOptions(head=1, tail=1, placeholder="... {n} frames omitted ...")
    report = truncate_trace(_trace(8), opts)
    out = format_truncation(report, opts, colour=False)
    assert "6 frames omitted" in out


def test_format_no_placeholder_when_not_truncated():
    opts = TruncateOptions(head=10, tail=10)
    report = truncate_trace(_trace(5), opts)
    out = format_truncation(report, opts, colour=False)
    assert "omitted" not in out
