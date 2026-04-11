"""Tests for stacktrace_lens.normalizer."""

from __future__ import annotations

import os

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.normalizer import (
    NormalizeOptions,
    normalize_frame,
    normalize_trace,
)


def _frame(
    filename: str = "/project/app/main.py",
    lineno: int = 42,
    function: str = "run",
    source_line: str = "    run()",
) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line=source_line)


def _trace(frames=None, exc_type="ValueError", exc_msg="bad value") -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(frames=frames, exception_type=exc_type, exception_message=exc_msg)


# ---------------------------------------------------------------------------
# normalize_frame
# ---------------------------------------------------------------------------

def test_normalize_frame_returns_frame():
    result = normalize_frame(_frame(), NormalizeOptions())
    assert isinstance(result, Frame)


def test_normalize_frame_strips_cwd():
    cwd = os.getcwd()
    frame = _frame(filename=os.path.join(cwd, "app", "main.py"))
    opts = NormalizeOptions(strip_cwd=True)
    result = normalize_frame(frame, opts)
    assert result.filename.startswith("<cwd>")
    assert cwd not in result.filename


def test_normalize_frame_no_strip_cwd_keeps_path():
    cwd = os.getcwd()
    filename = os.path.join(cwd, "app", "main.py")
    frame = _frame(filename=filename)
    opts = NormalizeOptions(strip_cwd=False)
    result = normalize_frame(frame, opts)
    assert result.filename == filename


def test_normalize_frame_collapses_site_packages():
    frame = _frame(filename="/usr/lib/python3.11/site-packages/requests/api.py")
    opts = NormalizeOptions(collapse_site_packages=True)
    result = normalize_frame(frame, opts)
    assert result.filename.startswith("<site-packages>/")
    assert "site-packages" not in result.filename[len("<site-packages>/"):]


def test_normalize_frame_anonymize_line_numbers():
    frame = _frame(lineno=99)
    opts = NormalizeOptions(anonymize_line_numbers=True)
    result = normalize_frame(frame, opts)
    assert result.lineno == 0


def test_normalize_frame_keeps_line_number_when_not_anonymized():
    frame = _frame(lineno=55)
    opts = NormalizeOptions(anonymize_line_numbers=False)
    result = normalize_frame(frame, opts)
    assert result.lineno == 55


def test_normalize_frame_preserves_function_and_source():
    frame = _frame(function="handler", source_line="    handler()")
    result = normalize_frame(frame, NormalizeOptions())
    assert result.function == "handler"
    assert result.source_line == "    handler()"


# ---------------------------------------------------------------------------
# normalize_trace
# ---------------------------------------------------------------------------

def test_normalize_trace_returns_stacktrace():
    result = normalize_trace(_trace())
    assert isinstance(result, StackTrace)


def test_normalize_trace_default_opts():
    trace = _trace()
    result = normalize_trace(trace)
    assert result.exception_type == trace.exception_type
    assert len(result.frames) == len(trace.frames)


def test_normalize_trace_lowercase_exception_type():
    trace = _trace(exc_type="ValueError")
    opts = NormalizeOptions(lowercase_exception_type=True)
    result = normalize_trace(trace, opts)
    assert result.exception_type == "valueerror"


def test_normalize_trace_preserves_exception_message():
    trace = _trace(exc_msg="something went wrong")
    result = normalize_trace(trace)
    assert result.exception_message == "something went wrong"


def test_normalize_trace_all_frames_normalized():
    cwd = os.getcwd()
    frames = [
        _frame(filename=os.path.join(cwd, "a.py"), lineno=1),
        _frame(filename=os.path.join(cwd, "b.py"), lineno=2),
    ]
    opts = NormalizeOptions(strip_cwd=True, anonymize_line_numbers=True)
    result = normalize_trace(_trace(frames=frames), opts)
    for f in result.frames:
        assert f.filename.startswith("<cwd>")
        assert f.lineno == 0
