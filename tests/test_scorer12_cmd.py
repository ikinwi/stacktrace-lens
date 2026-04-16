"""Tests for stacktrace_lens.scorer12_cmd."""
import argparse
import io
import sys
import textwrap
from unittest.mock import patch

import pytest

from stacktrace_lens.scorer12_cmd import _build_subparser, scorer12_command

_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        result = 1 / 0
    ZeroDivisionError: division by zero
""")


def _args(**kwargs):
    defaults = {"file": None, "no_colour": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_score12():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    parsed = parser.parse_args(["score12"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_TRACE)):
        assert scorer12_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert scorer12_command(_args()) == 1


def test_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(_TRACE)
    assert scorer12_command(_args(file=str(f))) == 0


def test_command_returns_one_on_missing_file():
    assert scorer12_command(_args(file="/no/such/file.txt")) == 1


def test_command_output_contains_exception_type(capsys):
    with patch("sys.stdin", io.StringIO(_TRACE)):
        scorer12_command(_args())
    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out
