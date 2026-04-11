"""Unit tests for stacktrace_lens.pattern_matcher_cmd."""
import argparse
import io
import json
from unittest.mock import patch

import pytest

from stacktrace_lens.pattern_matcher_cmd import _build_subparser, pattern_match_command

_SAMPLE_TRACE = """Traceback (most recent call last):
  File "/app/views.py", line 42, in get
    result = service.fetch()
  File "/lib/service.py", line 10, in fetch
    raise ValueError("bad")
ValueError: bad
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "files": [],
        "patterns": ["app=/app/"],
        "no_colour": True,
        "as_json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_pattern_match():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    ns = root.parse_args(["pattern-match", "-p", "app=/app/"])
    assert hasattr(ns, "patterns")


def test_command_returns_zero_on_valid_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        rc = pattern_match_command(_args(), out=out, err=err)
    assert rc == 0


def test_command_returns_one_on_empty_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO("")):
        rc = pattern_match_command(_args(), out=out, err=err)
    assert rc == 1


def test_command_returns_one_on_missing_file():
    out, err = io.StringIO(), io.StringIO()
    rc = pattern_match_command(_args(files=["/no/such/file.txt"]), out=out, err=err)
    assert rc == 1


def test_command_returns_one_when_no_patterns():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        rc = pattern_match_command(_args(patterns=[]), out=out, err=err)
    assert rc == 1


def test_command_returns_one_on_bad_pattern_format():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        rc = pattern_match_command(_args(patterns=["no-equals-sign"]), out=out, err=err)
    assert rc == 1


def test_json_output_is_valid_json():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        rc = pattern_match_command(_args(as_json=True), out=out, err=err)
    assert rc == 0
    payload = json.loads(out.getvalue())
    assert "total_frames" in payload
    assert "matches" in payload


def test_json_output_match_ratio_present():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        pattern_match_command(_args(as_json=True), out=out, err=err)
    payload = json.loads(out.getvalue())
    assert "match_ratio" in payload


def test_text_output_contains_label():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        pattern_match_command(_args(patterns=["myapp=/app/"]), out=out, err=err)
    assert "myapp" in out.getvalue()
