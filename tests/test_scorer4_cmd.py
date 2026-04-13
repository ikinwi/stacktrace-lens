"""Tests for stacktrace_lens.scorer4_cmd."""
import argparse
import io
import sys
from unittest.mock import patch

import pytest

from stacktrace_lens.scorer4_cmd import _build_subparser, scorer4_command

_VALID_TRACE = """\
Traceback (most recent call last):
  File "app.py", line 42, in run
    result = compute()
  File "core.py", line 10, in compute
    raise ValueError("oops")
ValueError: oops
"""


def _args(**kwargs):
    base = {"file": None, "top": 0, "no_color": True}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_build_subparser_registers_score4():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    _build_subparser(sub)
    parsed = p.parse_args(["score4"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_VALID_TRACE)):
        assert scorer4_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert scorer4_command(_args()) == 1


def test_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(_VALID_TRACE)
    assert scorer4_command(_args(file=str(f))) == 0


def test_command_returns_one_on_missing_file():
    assert scorer4_command(_args(file="/nonexistent/trace.txt")) == 1


def test_command_output_contains_exception_type(capsys):
    with patch("sys.stdin", io.StringIO(_VALID_TRACE)):
        scorer4_command(_args())
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_top_flag_limits_output(capsys):
    with patch("sys.stdin", io.StringIO(_VALID_TRACE)):
        scorer4_command(_args(top=1))
    out = capsys.readouterr().out
    # Only 1 frame line expected after header
    frame_lines = [l for l in out.splitlines() if "score=" in l]
    assert len(frame_lines) == 1
