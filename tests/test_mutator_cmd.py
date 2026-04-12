"""Tests for stacktrace_lens.mutator_cmd."""
from __future__ import annotations

import argparse
import io
import sys
import tempfile
import os
from unittest.mock import patch

import pytest

from stacktrace_lens.mutator_cmd import _build_subparser, mutator_command

_SAMPLE = """Traceback (most recent call last):
  File \"app.py\", line 5, in main
    run()
  File \"runner.py\", line 12, in run
    compute()
ValueError: something went wrong
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(strip_line_numbers=False, uppercase_filenames=False, file=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_mutate():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    p = _build_subparser(subs)
    assert p is not None


def test_mutator_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        assert mutator_command(_args()) == 0


def test_mutator_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert mutator_command(_args()) == 1


def test_mutator_command_reads_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(_SAMPLE)
        fname = f.name
    try:
        assert mutator_command(_args(file=fname)) == 0
    finally:
        os.unlink(fname)


def test_mutator_command_returns_one_on_missing_file():
    assert mutator_command(_args(file="/no/such/file.txt")) == 1


def test_strip_line_numbers_flag(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        ret = mutator_command(_args(strip_line_numbers=True))
    assert ret == 0


def test_uppercase_filenames_flag(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        ret = mutator_command(_args(uppercase_filenames=True))
    captured = capsys.readouterr()
    assert ret == 0
    assert "APP.PY" in captured.out or "RUNNER.PY" in captured.out
