"""Tests for stacktrace_lens.tagger and stacktrace_lens.tagger_cmd."""
from __future__ import annotations

import argparse
import types
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.tagger import (
    TagResult,
    auto_tag,
    format_tags,
    tag_trace,
)


def _make_trace(exc_type: str = "ValueError", msg: str = "bad value") -> StackTrace:
    frame = Frame(filename="app.py", lineno=10, function="run", source_line="x = 1")
    return StackTrace(frames=[frame], exception_type=exc_type, exception_message=msg)


# --- auto_tag ---

def test_auto_tag_returns_list():
    trace = _make_trace("TypeError")
    result = auto_tag(trace)
    assert isinstance(result, list)


def test_auto_tag_type_error():
    assert "type" in auto_tag(_make_trace("TypeError"))


def test_auto_tag_import_error():
    assert "import" in auto_tag(_make_trace("ImportError"))


def test_auto_tag_module_not_found():
    assert "import" in auto_tag(_make_trace("ModuleNotFoundError"))


def test_auto_tag_unknown_falls_back():
    assert auto_tag(_make_trace("WeirdCustomError")) == ["unknown"]


def test_auto_tag_no_duplicates():
    tags = auto_tag(_make_trace("TypeError"))
    assert len(tags) == len(set(tags))


# --- tag_trace ---

def test_tag_trace_returns_tag_result():
    trace = _make_trace()
    result = tag_trace(trace)
    assert isinstance(result, TagResult)


def test_tag_trace_includes_auto_tags_by_default():
    result = tag_trace(_make_trace("KeyError"))
    assert "key" in result.tags


def test_tag_trace_extra_tags_appended():
    result = tag_trace(_make_trace(), extra_tags=["production", "critical"])
    assert "production" in result.tags
    assert "critical" in result.tags


def test_tag_trace_no_auto():
    result = tag_trace(_make_trace("ValueError"), include_auto=False)
    assert "value" not in result.tags


def test_tag_trace_note_stored():
    result = tag_trace(_make_trace(), note="seen in prod")
    assert result.note == "seen in prod"


def test_tag_result_has_tag():
    result = tag_trace(_make_trace("ZeroDivisionError"))
    assert result.has_tag("arithmetic")
    assert not result.has_tag("io")


# --- format_tags ---

def test_format_tags_returns_string():
    result = tag_trace(_make_trace())
    assert isinstance(format_tags(result), str)


def test_format_tags_contains_exception_type():
    result = tag_trace(_make_trace("RuntimeError"))
    assert "RuntimeError" in format_tags(result)


def test_format_tags_contains_tag_brackets():
    result = tag_trace(_make_trace("OSError"))
    text = format_tags(result)
    assert "[" in text and "]" in text


def test_format_tags_note_included():
    result = tag_trace(_make_trace(), note="urgent")
    assert "urgent" in format_tags(result)


def test_format_tags_colour_adds_ansi():
    result = tag_trace(_make_trace())
    assert "\033[" in format_tags(result, colour=True)


# --- tagger_cmd ---

def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(file=None, extra_tags=None, note=None, no_auto=False, no_colour=True)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


SAMPLE = """Traceback (most recent call last):
  File "app.py", line 5, in main
    run()
ValueError: bad input
"""


def test_tagger_command_returns_zero_on_valid_stdin():
    from stacktrace_lens.tagger_cmd import tagger_command
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = SAMPLE
        assert tagger_command(_args()) == 0


def test_tagger_command_returns_one_on_empty_stdin():
    from stacktrace_lens.tagger_cmd import tagger_command
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = "   "
        assert tagger_command(_args()) == 1


def test_tagger_command_reads_from_file(tmp_path):
    from stacktrace_lens.tagger_cmd import tagger_command
    f = tmp_path / "trace.txt"
    f.write_text(SAMPLE)
    assert tagger_command(_args(file=str(f))) == 0


def test_tagger_command_missing_file():
    from stacktrace_lens.tagger_cmd import tagger_command
    assert tagger_command(_args(file="/no/such/file.txt")) == 1
