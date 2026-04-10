"""Tests for stacktrace_lens.classifier and classifier_cmd."""

from __future__ import annotations

import argparse
import io
import json
from unittest.mock import patch

import pytest

from stacktrace_lens.classifier import (
    ClassificationResult,
    classify_trace,
    format_classification,
)
from stacktrace_lens.classifier_cmd import classifier_command
from stacktrace_lens.parser import Frame, StackTrace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(exc_type: str = "ValueError", msg: str = "bad value") -> StackTrace:
    frame = Frame(filename="app.py", lineno=10, function="run", source_line="x = int(y)")
    return StackTrace(frames=[frame], exception_type=exc_type, exception_message=msg)


def _args(file=None, json_flag=False) -> argparse.Namespace:
    return argparse.Namespace(file=file, json=json_flag)


# ---------------------------------------------------------------------------
# classify_trace
# ---------------------------------------------------------------------------

def test_classify_returns_classification_result():
    trace = _make_trace("ValueError")
    result = classify_trace(trace)
    assert isinstance(result, ClassificationResult)


def test_classify_value_error_category():
    result = classify_trace(_make_trace("ValueError"))
    assert result.category == "value"


def test_classify_import_error_category():
    result = classify_trace(_make_trace("ImportError"))
    assert result.category == "dependency"


def test_classify_module_not_found_category():
    result = classify_trace(_make_trace("ModuleNotFoundError"))
    assert result.category == "dependency"


def test_classify_os_error_category():
    result = classify_trace(_make_trace("FileNotFoundError"))
    assert result.category == "io"


def test_classify_unknown_exception_category():
    result = classify_trace(_make_trace("WeirdCustomError"))
    assert result.category == "unknown"
    assert result.confidence == 0.5


def test_classify_exact_match_higher_confidence():
    result = classify_trace(_make_trace("TypeError"))
    assert result.confidence == 1.0


def test_classify_substring_match_lower_confidence():
    result = classify_trace(_make_trace("MyTypeError"))
    assert result.confidence == 0.85


def test_classify_dependency_note_present():
    result = classify_trace(_make_trace("ImportError"))
    assert result.note is not None
    assert "packages" in result.note.lower() or "install" in result.note.lower()


# ---------------------------------------------------------------------------
# format_classification
# ---------------------------------------------------------------------------

def test_format_classification_returns_string():
    result = classify_trace(_make_trace("KeyError"))
    text = format_classification(result)
    assert isinstance(text, str)


def test_format_classification_contains_category():
    result = classify_trace(_make_trace("KeyError"))
    text = format_classification(result)
    assert "key" in text


def test_format_classification_contains_exception_type():
    result = classify_trace(_make_trace("KeyError"))
    text = format_classification(result)
    assert "KeyError" in text


# ---------------------------------------------------------------------------
# classifier_command
# ---------------------------------------------------------------------------

SAMPLE = (
    "Traceback (most recent call last):\n"
    '  File "app.py", line 5, in main\n'
    "    run()\n"
    "TypeError: unsupported operand\n"
)


def test_classifier_command_returns_zero_on_valid_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(SAMPLE)):
        code = classifier_command(_args(), out=out, err=err)
    assert code == 0


def test_classifier_command_returns_one_on_empty_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO("")):
        code = classifier_command(_args(), out=out, err=err)
    assert code == 1


def test_classifier_command_output_contains_category():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(SAMPLE)):
        classifier_command(_args(), out=out, err=err)
    assert "type" in out.getvalue()


def test_classifier_command_json_flag_emits_json():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(SAMPLE)):
        classifier_command(_args(json_flag=True), out=out, err=err)
    payload = json.loads(out.getvalue())
    assert "category" in payload
    assert "confidence" in payload


def test_classifier_command_returns_one_on_missing_file():
    out, err = io.StringIO(), io.StringIO()
    code = classifier_command(_args(file="/no/such/file.txt"), out=out, err=err)
    assert code == 1
