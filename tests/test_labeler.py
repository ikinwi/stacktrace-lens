"""Tests for stacktrace_lens.labeler."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.labeler import (
    LabelResult,
    label_trace,
    format_labels,
    _depth_label,
    _exception_label,
)


def _make_trace(
    exc_type: str = "RuntimeError",
    exc_msg: str = "oops",
    n_frames: int = 3,
) -> StackTrace:
    frames = [
        Frame(filename=f"file{i}.py", lineno=i + 1, function=f"fn{i}", context="pass")
        for i in range(n_frames)
    ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# --- unit helpers ---

def test_exception_label_known():
    assert _exception_label("ZeroDivisionError") == "math-error"


def test_exception_label_unknown():
    assert _exception_label("SomeObscureError") is None


def test_exception_label_substring_match():
    assert _exception_label("ModuleNotFoundError") == "import-failure"


def test_depth_label_deep():
    assert _depth_label(10) == "deep-trace"


def test_depth_label_very_deep():
    assert _depth_label(25) == "deep-trace"


def test_depth_label_shallow():
    assert _depth_label(1) == "shallow-trace"


def test_depth_label_normal():
    assert _depth_label(5) == "normal-depth"


# --- label_trace ---

def test_label_trace_returns_label_result():
    trace = _make_trace()
    result = label_trace(trace)
    assert isinstance(result, LabelResult)


def test_label_trace_known_exception():
    trace = _make_trace(exc_type="TypeError")
    result = label_trace(trace)
    assert result.exception_label == "type-mismatch"


def test_label_trace_unknown_exception_is_none():
    trace = _make_trace(exc_type="WeirdError")
    result = label_trace(trace)
    assert result.exception_label is None


def test_label_trace_deep_trace():
    trace = _make_trace(n_frames=15)
    result = label_trace(trace)
    assert result.depth_label == "deep-trace"


def test_label_trace_shallow_trace():
    trace = _make_trace(n_frames=1)
    result = label_trace(trace)
    assert result.depth_label == "shallow-trace"


def test_label_trace_custom_labels_stored():
    trace = _make_trace()
    result = label_trace(trace, extra=["production", "critical"])
    assert "production" in result.custom_labels
    assert "critical" in result.custom_labels


def test_label_trace_no_extra_gives_empty_custom():
    trace = _make_trace()
    result = label_trace(trace)
    assert result.custom_labels == []


def test_all_labels_includes_exception_and_depth():
    trace = _make_trace(exc_type="ValueError", n_frames=5)
    result = label_trace(trace)
    assert "bad-value" in result.all_labels
    assert "normal-depth" in result.all_labels


def test_all_labels_excludes_none_exception():
    trace = _make_trace(exc_type="UnknownError")
    result = label_trace(trace)
    assert None not in result.all_labels


# --- format_labels ---

def test_format_labels_returns_string():
    trace = _make_trace(exc_type="KeyError")
    result = label_trace(trace)
    output = format_labels(result)
    assert isinstance(output, str)


def test_format_labels_contains_exception_label():
    trace = _make_trace(exc_type="KeyError")
    result = label_trace(trace)
    output = format_labels(result)
    assert "missing-key" in output


def test_format_labels_contains_depth_label():
    trace = _make_trace(n_frames=5)
    result = label_trace(trace)
    output = format_labels(result)
    assert "normal-depth" in output


def test_format_labels_contains_custom_labels():
    trace = _make_trace()
    result = label_trace(trace, extra=["staging"])
    output = format_labels(result)
    assert "staging" in output


def test_format_labels_no_exception_section_when_unknown():
    trace = _make_trace(exc_type="ObscureError")
    result = label_trace(trace)
    output = format_labels(result)
    assert "exception" not in output
