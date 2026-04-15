"""Tests for stacktrace_lens.scorer6_cmd."""
from __future__ import annotations

import argparse
import io
import sys
from unittest.mock import patch

import pytest

from stacktrace_lens.scorer6_cmd import _build_subparser, scorer6_command

_SAMPLE = """\
Traceback (most recent call last):
  File "app/main.py", line 42, in run
    result = compute()
  File "app/compute.py", line 17, in compute
    return 1 / 0
ZeroDivisionError: division by zero
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "top": 10, "no_colour": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_score6():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        assert scorer6_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert scorer6_command(_args()) == 1


def test_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE)
    assert scorer6_command(_args(file=str(f))) == 0


def test_command_returns_one_on_missing_file():
    assert scorer6_command(_args(file="/nonexistent/trace.txt")) == 1


def test_command_output_contains_exception_type(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        scorer6_command(_args())
    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out


def test_command_top_limits_output(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        scorer6_command(_args(top=1))
    out = capsys.readouterr().out
    # Only one ranked frame line should appear (lines starting with 4 spaces + score)
    ranked_lines = [l for l in out.splitlines() if l.strip() and l.startswith("    ") and "." in l]
    assert len(ranked_lines) <= 1
