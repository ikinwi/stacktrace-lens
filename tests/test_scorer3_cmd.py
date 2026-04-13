"""Tests for stacktrace_lens.scorer3_cmd."""
import argparse
import io
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from stacktrace_lens.scorer3_cmd import _build_subparser, scorer3_command

_SAMPLE_TRACE = """Traceback (most recent call last):
  File \"app.py\", line 10, in main
    run()
  File \"core.py\", line 20, in run
    process()
ValueError: something went wrong
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "top": 0, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_score3():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        assert scorer3_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert scorer3_command(_args()) == 1


def test_command_reads_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write(_SAMPLE_TRACE)
        name = fh.name
    try:
        assert scorer3_command(_args(file=name)) == 0
    finally:
        os.unlink(name)


def test_command_returns_one_on_missing_file():
    assert scorer3_command(_args(file="/no/such/file.txt")) == 1


def test_command_output_contains_summary(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        scorer3_command(_args())
    captured = capsys.readouterr()
    assert "frames scored" in captured.out


def test_top_flag_limits_output(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        scorer3_command(_args(top=1))
    captured = capsys.readouterr()
    # summary line + 1 frame line = 2 non-empty lines
    lines = [l for l in captured.out.splitlines() if l.strip()]
    assert len(lines) == 2
