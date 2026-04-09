"""Tests for stacktrace_lens.annotator."""
from __future__ import annotations

import textwrap
from unittest.mock import patch

import pytest

from stacktrace_lens.annotator import (
    AnnotatedFrame,
    AnnotatedLine,
    AnnotationOptions,
    annotate_frame,
    annotate_trace,
)
from stacktrace_lens.parser import Frame, StackTrace


def _frame(filename: str = "/app/foo.py", lineno: int = 10, function: str = "bar") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="x = 1")


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        frames=list(frames),
        exception_type="ValueError",
        exception_message="bad value",
    )


_FAKE_SOURCE = {
    8: "def bar():\n",
    9: "    x = 0\n",
    10: "    return 1 / x\n",
    11: "\n",
    12: "bar()\n",
}


def _fake_getline(filename, lineno, *_):
    return _FAKE_SOURCE.get(lineno, "")


@patch("linecache.getline", side_effect=_fake_getline)
def test_annotate_frame_returns_annotated_frame(mock_gl):
    f = _frame(lineno=10)
    result = annotate_frame(f, AnnotationOptions(context_lines=2))
    assert isinstance(result, AnnotatedFrame)


@patch("linecache.getline", side_effect=_fake_getline)
def test_annotate_frame_source_available(mock_gl):
    f = _frame(lineno=10)
    result = annotate_frame(f, AnnotationOptions(context_lines=2))
    assert result.source_available is True


@patch("linecache.getline", side_effect=_fake_getline)
def test_annotate_frame_correct_line_count(mock_gl):
    f = _frame(lineno=10)
    result = annotate_frame(f, AnnotationOptions(context_lines=2))
    # lines 8..12 => 5 lines
    assert len(result.lines) == 5


@patch("linecache.getline", side_effect=_fake_getline)
def test_error_line_is_flagged(mock_gl):
    f = _frame(lineno=10)
    result = annotate_frame(f, AnnotationOptions(context_lines=2))
    error_lines = [ln for ln in result.lines if ln.is_error_line]
    assert len(error_lines) == 1
    assert error_lines[0].lineno == 10


def test_annotate_frame_no_source():
    f = _frame(filename="/nonexistent/path.py", lineno=1)
    result = annotate_frame(f, AnnotationOptions())
    assert result.source_available is False
    assert result.lines == []


@patch("linecache.getline", side_effect=_fake_getline)
def test_annotate_trace_returns_list(mock_gl):
    t = _trace(_frame(lineno=10), _frame(lineno=9))
    results = annotate_trace(t)
    assert isinstance(results, list)
    assert len(results) == 2


@patch("linecache.getline", side_effect=_fake_getline)
def test_annotate_trace_default_options(mock_gl):
    t = _trace(_frame(lineno=10))
    results = annotate_trace(t)
    assert results[0].source_available is True
