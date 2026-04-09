"""Tests for stacktrace_lens.exporter."""

from __future__ import annotations

import json

import pytest

from stacktrace_lens.exporter import ExportOptions, StackTraceExporter
from stacktrace_lens.parser import Frame, StackTrace


def make_trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames: list[Frame] | None = None,
) -> StackTrace:
    if frames is None:
        frames = [
            Frame(filename="app.py", lineno=10, function="run", code="result = compute(x)"),
            Frame(filename="utils.py", lineno=42, function="compute", code="return 1 / value"),
        ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# ---------------------------------------------------------------------------
# Text export
# ---------------------------------------------------------------------------

def test_text_export_returns_string():
    exporter = StackTraceExporter(ExportOptions(fmt="text"))
    result = exporter.export(make_trace())
    assert isinstance(result, str)


def test_text_export_contains_exception_type():
    exporter = StackTraceExporter(ExportOptions(fmt="text"))
    result = exporter.export(make_trace(exc_type="TypeError"))
    assert "TypeError" in result


def test_text_export_contains_exception_message():
    exporter = StackTraceExporter(ExportOptions(fmt="text"))
    result = exporter.export(make_trace(exc_msg="something went wrong"))
    assert "something went wrong" in result


def test_text_export_contains_frame_info():
    exporter = StackTraceExporter(ExportOptions(fmt="text"))
    result = exporter.export(make_trace())
    assert "app.py" in result
    assert "compute" in result


def test_text_export_no_suggestions_flag():
    exporter = StackTraceExporter(ExportOptions(fmt="text", include_suggestions=False))
    result = exporter.export(make_trace(exc_type="ZeroDivisionError", exc_msg="division by zero"))
    assert "Suggestion" not in result


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def test_json_export_is_valid_json():
    exporter = StackTraceExporter(ExportOptions(fmt="json"))
    result = exporter.export(make_trace())
    parsed = json.loads(result)  # must not raise
    assert isinstance(parsed, dict)


def test_json_export_has_required_keys():
    exporter = StackTraceExporter(ExportOptions(fmt="json"))
    parsed = json.loads(exporter.export(make_trace()))
    assert "exception_type" in parsed
    assert "exception_message" in parsed
    assert "frames" in parsed


def test_json_export_frames_count():
    exporter = StackTraceExporter(ExportOptions(fmt="json"))
    parsed = json.loads(exporter.export(make_trace()))
    assert len(parsed["frames"]) == 2


def test_json_export_no_suggestions_key_when_disabled():
    exporter = StackTraceExporter(ExportOptions(fmt="json", include_suggestions=False))
    parsed = json.loads(exporter.export(make_trace()))
    assert "suggestions" not in parsed


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def test_markdown_export_contains_heading():
    exporter = StackTraceExporter(ExportOptions(fmt="markdown"))
    result = exporter.export(make_trace(exc_type="RuntimeError"))
    assert "## `RuntimeError`" in result


def test_markdown_export_contains_filename():
    exporter = StackTraceExporter(Exportn    result = exporter.export(make_trace())
    assert "app.py" in result


def test_markdown_export_contains_code_fence():
    exporter = StackTraceExporter(ExportOptions(fmt="markdown"))
    result = exporter.export(make_trace())
    assert "```python" in result
