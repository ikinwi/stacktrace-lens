"""Tests for the stacktrace_lens.parser module."""

import pytest
from stacktrace_lens.parser import parse_stacktrace, Frame, StackTrace


SAMPLE_TRACE = """\
Traceback (most recent call last):
  File "/app/main.py", line 42, in run
    result = compute(data)
  File "/app/utils.py", line 17, in compute
    return data["key"] / data["divisor"]
ZeroDivisionError: division by zero
"""

NO_SOURCE_TRACE = """\
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'foo' is not defined
"""

INVALID_TEXT = "This is just a regular log line with no traceback."


def test_parse_returns_stacktrace_instance():
    result = parse_stacktrace(SAMPLE_TRACE)
    assert isinstance(result, StackTrace)


def test_parse_exception_type():
    result = parse_stacktrace(SAMPLE_TRACE)
    assert result.exception_type == "ZeroDivisionError"


def test_parse_exception_message():
    result = parse_stacktrace(SAMPLE_TRACE)
    assert result.exception_message == "division by zero"


def test_parse_frame_count():
    result = parse_stacktrace(SAMPLE_TRACE)
    assert len(result.frames) == 2


def test_parse_first_frame():
    result = parse_stacktrace(SAMPLE_TRACE)
    frame = result.frames[0]
    assert frame.file_path == "/app/main.py"
    assert frame.line_number == 42
    assert frame.function_name == "run"
    assert frame.source_line == "result = compute(data)"


def test_parse_second_frame():
    result = parse_stacktrace(SAMPLE_TRACE)
    frame = result.frames[1]
    assert frame.file_path == "/app/utils.py"
    assert frame.line_number == 17
    assert frame.function_name == "compute"
    assert "divisor" in frame.source_line


def test_parse_no_source_line():
    result = parse_stacktrace(NO_SOURCE_TRACE)
    assert result is not None
    assert len(result.frames) == 1
    assert result.frames[0].source_line is None
    assert result.exception_type == "NameError"


def test_parse_invalid_text_returns_none():
    result = parse_stacktrace(INVALID_TEXT)
    assert result is None


def test_parse_empty_string_returns_none():
    result = parse_stacktrace("")
    assert result is None
