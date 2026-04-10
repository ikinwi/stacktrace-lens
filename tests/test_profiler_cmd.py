"""Tests for stacktrace_lens.profiler_cmd."""

from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_lens.profiler_cmd import _build_subparser, profiler_command

_SAMPLE_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in main
        result = compute()
      File "utils.py", line 42, in compute
        return 1 / 0
    ZeroDivisionError: division by zero
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "top": 10, "no_colour": True, "func": profiler_command}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_profile():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    ns = parser.parse_args(["profile"])
    assert hasattr(ns, "func")


def test_profiler_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        assert profiler_command(_args()) == 0


def test_profiler_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert profiler_command(_args()) == 1


def test_profiler_command_reads_from_file(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE_TRACE, encoding="utf-8")
    assert profiler_command(_args(files=[str(f)])) == 0


def test_profiler_command_returns_one_on_missing_file():
    assert profiler_command(_args(files=["/no/such/file.txt"])) == 1


def test_profiler_command_multiple_files(tmp_path: Path):
    f1 = tmp_path / "t1.txt"
    f2 = tmp_path / "t2.txt"
    f1.write_text(_SAMPLE_TRACE, encoding="utf-8")
    f2.write_text(_SAMPLE_TRACE, encoding="utf-8")
    assert profiler_command(_args(files=[str(f1), str(f2)])) == 0


def test_profiler_command_top_n_respected(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE_TRACE, encoding="utf-8")
    # Should not crash with top=1
    assert profiler_command(_args(files=[str(f)], top=1)) == 0
