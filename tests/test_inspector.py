"""Tests for stacktrace_lens.inspector."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.inspector import (
    InspectionResult,
    inspect_trace,
    format_inspection,
    _detect_recursion,
)


def _frame(filename: str = "app.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(
    exc_type: str = "ValueError",
    message: str = "bad value",
    frames=None,
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=message, frames=frames)


# --- inspect_trace ---

def test_inspect_returns_inspection_result():
    result = inspect_trace(_trace())
    assert isinstance(result, InspectionResult)


def test_inspect_exception_type():
    result = inspect_trace(_trace(exc_type="TypeError"))
    assert result.exception_type == "TypeError"


def test_inspect_exception_message():
    result = inspect_trace(_trace(message="oops"))
    assert result.exception_message == "oops"


def test_inspect_depth_matches_frame_count():
    frames = [_frame("a.py"), _frame("b.py"), _frame("c.py")]
    result = inspect_trace(_trace(frames=frames))
    assert result.depth == 3


def test_inspect_root_and_tip():
    frames = [_frame("first.py", "entry"), _frame("last.py", "crash")]
    result = inspect_trace(_trace(frames=frames))
    assert result.root_file == "first.py"
    assert result.root_function == "entry"
    assert result.tip_file == "last.py"
    assert result.tip_function == "crash"


def test_inspect_unique_files():
    frames = [_frame("a.py"), _frame("b.py"), _frame("a.py")]
    result = inspect_trace(_trace(frames=frames))
    assert sorted(result.unique_files) == ["a.py", "b.py"]


def test_inspect_unique_functions():
    frames = [_frame(function="foo"), _frame(function="bar"), _frame(function="foo")]
    result = inspect_trace(_trace(frames=frames))
    assert sorted(result.unique_functions) == ["bar", "foo"]


def test_inspect_no_recursion_when_all_unique():
    frames = [_frame("a.py", "f1"), _frame("b.py", "f2")]
    result = inspect_trace(_trace(frames=frames))
    assert result.has_recursion is False


def test_inspect_detects_recursion():
    frames = [_frame("a.py", "recurse"), _frame("b.py", "other"), _frame("a.py", "recurse")]
    result = inspect_trace(_trace(frames=frames))
    assert result.has_recursion is True


def test_inspect_empty_frames():
    result = inspect_trace(_trace(frames=[]))
    assert result.depth == 0
    assert result.root_file is None
    assert result.tip_file is None


# --- summary_line ---

def test_summary_line_contains_exception_type():
    result = inspect_trace(_trace(exc_type="KeyError"))
    assert "KeyError" in result.summary_line()


def test_summary_line_contains_depth():
    frames = [_frame(), _frame("b.py")]
    result = inspect_trace(_trace(frames=frames))
    assert "depth=2" in result.summary_line()


# --- format_inspection ---

def test_format_inspection_returns_string():
    result = inspect_trace(_trace())
    out = format_inspection(result)
    assert isinstance(out, str)


def test_format_inspection_contains_exception_type():
    result = inspect_trace(_trace(exc_type="RuntimeError"))
    out = format_inspection(result, colour=False)
    assert "RuntimeError" in out


def test_format_inspection_recursion_warning_present():
    frames = [_frame("a.py", "f"), _frame("b.py", "g"), _frame("a.py", "f")]
    result = inspect_trace(_trace(frames=frames))
    out = format_inspection(result, colour=False)
    assert "recursion" in out.lower()


def test_format_inspection_no_recursion_warning_absent():
    result = inspect_trace(_trace())
    out = format_inspection(result, colour=False)
    assert "recursion" not in out.lower()
