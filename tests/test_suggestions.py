"""Tests for the context-aware suggestions engine."""

import pytest
from stacktrace_lens.parser import StackTrace, Frame
from stacktrace_lens.suggestions import get_suggestion, get_all_suggestions


def make_trace(exc_type: str, message: str = "") -> StackTrace:
    return StackTrace(
        frames=[
            Frame(filename="test.py", lineno=1, function="test", code_line="pass")
        ],
        exception_type=exc_type,
        exception_message=message,
    )


def test_known_exception_returns_suggestion():
    trace = make_trace("KeyError")
    result = get_suggestion(trace)
    assert result is not None
    assert len(result) > 0


def test_unknown_exception_returns_none():
    trace = make_trace("MyCustomError")
    result = get_suggestion(trace)
    assert result is None


def test_zero_division_error_suggestion():
    trace = make_trace("ZeroDivisionError")
    result = get_suggestion(trace)
    assert result is not None
    assert "zero" in result.lower()


def test_import_error_suggestion():
    trace = make_trace("ImportError")
    result = get_suggestion(trace)
    assert result is not None
    assert "pip" in result


def test_attribute_error_suggestion():
    trace = make_trace("AttributeError")
    result = get_suggestion(trace)
    assert result is not None
    assert "hasattr" in result or "attribute" in result.lower()


def test_get_all_suggestions_known():
    trace = make_trace("ImportError")
    results = get_all_suggestions(trace)
    assert isinstance(results, list)
    assert len(results) >= 1


def test_get_all_suggestions_unknown():
    trace = make_trace("ObscureError")
    results = get_all_suggestions(trace)
    assert results == []


def test_module_not_found_suggestion():
    trace = make_trace("ModuleNotFoundError")
    result = get_suggestion(trace)
    assert result is not None
    assert "PYTHONPATH" in result or "pip" in result


def test_recursion_error_suggestion():
    trace = make_trace("RecursionError")
    result = get_suggestion(trace)
    assert result is not None
    assert "recursion" in result.lower() or "base case" in result.lower()
