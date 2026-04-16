"""Tests for scorer13_cmd."""
import argparse
import json
import sys
from io import StringIO
from unittest.mock import patch
import pytest
from stacktrace_lens.scorer13_cmd import scorer13_command, _build_subparser

_TRACE = """Traceback (most recent call last):
  File \"app/main.py\", line 10, in run
    do_thing()
  File \"app/helper.py\", line 5, in do_thing
    raise ValueError('oops')
ValueError: oops
"""


def _args(file=None):
    ns = argparse.Namespace()
    ns.file = file
    return ns


def test_build_subparser_registers_score13():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    _build_subparser(sub)
    parsed = p.parse_args(["score13"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", StringIO(_TRACE)):
        assert scorer13_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", StringIO("")):
        assert scorer13_command(_args()) == 1


def test_command_reads_from_file(tmp_path):
    p = tmp_path / "trace.txt"
    p.write_text(_TRACE)
    assert scorer13_command(_args(file=str(p))) == 0


def test_command_returns_one_on_missing_file():
    assert scorer13_command(_args(file="/no/such/file.txt")) == 1


def test_command_output_contains_exception_type(capsys):
    with patch("sys.stdin", StringIO(_TRACE)):
        scorer13_command(_args())
    out = capsys.readouterr().out
    assert "ValueError" in out
