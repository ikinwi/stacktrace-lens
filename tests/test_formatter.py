"""Tests for the StackTraceFormatter and format_stacktrace helper."""

import pytest
from stacktrace_lens.parser import StackTrace, Frame
from stacktrace_lens.formatter import (
    StackTraceFormatter,
    FormatOptions,
    format_stacktrace,
)


SAMPLE_STACKTRACE = StackTrace(
    frames=[
        Frame(
            filename="app/main.py",
            lineno=42,
            function="run",
            code_line="  result = compute(value)",
        ),
        Frame(
            filename="app/utils.py",
            lineno=17,
            function="compute",
            code_line="  return 1 / x",
        ),
    ],
    exception_type="ZeroDivisionError",
    exception_message="division by zero",
)


def test_format_returns_string():
    result = format_stacktrace(SAMPLE_STACKTRACE)
    assert isinstance(result, str)


def test_format_contains_exception_type():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "ZeroDivisionError" in result


def test_format_contains_exception_message():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "division by zero" in result


def test_format_contains_filenames():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "app/main.py" in result
    assert "app/utils.py" in result


def test_format_contains_function_names():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "run" in result
    assert "compute" in result


def test_format_contains_code_lines():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "result = compute(value)" in result
    assert "return 1 / x" in result


def test_max_frames_option():
    options = FormatOptions(color=False, max_frames=1)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "app/main.py" in result
    assert "app/utils.py" not in result


def test_color_disabled_no_ansi_codes():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "\033[" not in result


def test_color_enabled_contains_ansi_codes():
    options = FormatOptions(color=True)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "\033[" in result


def test_format_traceback_header():
    options = FormatOptions(color=False)
    result = format_stacktrace(SAMPLE_STACKTRACE, options)
    assert "Traceback (most recent call last):" in result
