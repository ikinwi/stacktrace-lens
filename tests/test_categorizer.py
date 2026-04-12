"""Tests for stacktrace_lens.categorizer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.categorizer import (
    CategorizationResult,
    categorize_trace,
    format_categorization,
)


def _make_trace(exc_type: str = "ValueError", msg: str = "bad value") -> StackTrace:
    frames = [
        Frame(filename="app.py", lineno=10, function="run", source_line="x = int(y)"),
    ]
    return StackTrace(exception_type=exc_type, exception_message=msg, frames=frames)


# --- CategorizationResult ---

def test_categorize_returns_result_instance():
    trace = _make_trace()
    result = categorize_trace(trace)
    assert isinstance(result, CategorizationResult)


def test_value_error_category_is_runtime():
    result = categorize_trace(_make_trace("ValueError"))
    assert result.category == "runtime"


def test_import_error_category_is_dependency():
    result = categorize_trace(_make_trace("ImportError"))
    assert result.category == "dependency"


def test_module_not_found_is_dependency():
    result = categorize_trace(_make_trace("ModuleNotFoundError"))
    assert result.category == "dependency"


def test_os_error_is_io():
    result = categorize_trace(_make_trace("OSError"))
    assert result.category == "io"


def test_file_not_found_is_io():
    result = categorize_trace(_make_trace("FileNotFoundError"))
    assert result.category == "io"


def test_connection_error_is_network():
    result = categorize_trace(_make_trace("ConnectionError"))
    assert result.category == "network"


def test_memory_error_is_resource():
    result = categorize_trace(_make_trace("MemoryError"))
    assert result.category == "resource"


def test_recursion_error_is_resource():
    result = categorize_trace(_make_trace("RecursionError"))
    assert result.category == "resource"


def test_assertion_error_is_assertion():
    result = categorize_trace(_make_trace("AssertionError"))
    assert result.category == "assertion"


def test_syntax_error_is_syntax():
    result = categorize_trace(_make_trace("SyntaxError"))
    assert result.category == "syntax"


def test_unknown_exception_category_is_unknown():
    result = categorize_trace(_make_trace("MyWeirdException"))
    assert result.category == "unknown"


def test_unknown_exception_confidence_is_zero():
    result = categorize_trace(_make_trace("MyWeirdException"))
    assert result.confidence == 0.0


def test_known_exception_confidence_is_one():
    result = categorize_trace(_make_trace("ValueError"))
    assert result.confidence == 1.0


def test_partial_match_has_reduced_confidence():
    # "CustomImportError" contains "ImportError" → partial match
    result = categorize_trace(_make_trace("CustomImportError"))
    assert result.category == "dependency"
    assert result.confidence == pytest.approx(0.7)


def test_unknown_exception_has_note():
    result = categorize_trace(_make_trace("MyWeirdException"))
    assert any("not recognised" in n for n in result.notes)


def test_no_frames_adds_note():
    trace = StackTrace(exception_type="ValueError", exception_message="x", frames=[])
    result = categorize_trace(trace)
    assert any("no frames" in n for n in result.notes)


# --- format_categorization ---

def test_format_returns_string():
    result = categorize_trace(_make_trace())
    assert isinstance(format_categorization(result), str)


def test_format_contains_exception_type():
    result = categorize_trace(_make_trace("KeyError"))
    text = format_categorization(result)
    assert "KeyError" in text


def test_format_contains_category():
    result = categorize_trace(_make_trace("KeyError"))
    text = format_categorization(result)
    assert "runtime" in text


def test_summary_line_format():
    result = CategorizationResult(
        exception_type="ValueError",
        category="runtime",
        confidence=1.0,
    )
    line = result.summary_line()
    assert "ValueError" in line
    assert "runtime" in line
    assert "100%" in line
