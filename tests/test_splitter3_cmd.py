"""Tests for stacktrace_lens.splitter3_cmd."""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_lens.splitter3_cmd import _build_subparser, partition_command

_SAMPLE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        do_thing()
      File "lib/helper.py", line 5, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "no_colour": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_partition():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    _build_subparser(subs)
    parsed = parser.parse_args(["partition"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        assert partition_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert partition_command(_args()) == 1


def test_command_returns_one_on_missing_file():
    assert partition_command(_args(file="/no/such/file.txt")) == 1


def test_command_reads_from_file(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE)
    assert partition_command(_args(file=str(f))) == 0


def test_command_output_contains_partition_count(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        partition_command(_args())
    out = capsys.readouterr().out
    assert "partition" in out.lower()


def test_command_output_contains_package_names(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        partition_command(_args())
    out = capsys.readouterr().out
    assert "app" in out or "lib" in out
