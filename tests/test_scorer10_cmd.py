"""Tests for stacktrace_lens.scorer10_cmd."""
import argparse
import io
import sys
import textwrap
import pytest
from unittest.mock import patch
from stacktrace_lens.scorer10_cmd import scorer10_command, _build_subparser

_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 5, in run
        result = 1 / 0
    ZeroDivisionError: division by zero
""")


def _args(**kwargs):
    ns = argparse.Namespace(file=None)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_build_subparser_registers_score10():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    parsed = parser.parse_args(["score10"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_TRACE)):
        assert scorer10_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert scorer10_command(_args()) == 1


def test_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(_TRACE)
    assert scorer10_command(_args(file=str(f))) == 0


def test_command_returns_one_on_missing_file():
    assert scorer10_command(_args(file="/no/such/file.txt")) == 1


def test_command_output_contains_exception_type(capsys):
    with patch("sys.stdin", io.StringIO(_TRACE)):
        scorer10_command(_args())
    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out
