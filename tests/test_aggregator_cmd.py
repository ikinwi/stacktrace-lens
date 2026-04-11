"""Tests for stacktrace_lens.aggregator_cmd."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from stacktrace_lens.aggregator_cmd import _build_subparser, aggregator_command

_SAMPLE_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in main
        result = 1 / 0
    ZeroDivisionError: division by zero
""")


def _write_trace(tmp_path: Path, name: str = "trace.txt") -> Path:
    p = tmp_path / name
    p.write_text(_SAMPLE_TRACE, encoding="utf-8")
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "top": 5, "no_color": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_aggregate():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    parsed = root.parse_args(["aggregate", "some_file.txt"])
    assert parsed.files == ["some_file.txt"]


def test_aggregator_command_returns_zero_on_valid_file(tmp_path):
    p = _write_trace(tmp_path)
    result = aggregator_command(_args(files=[str(p)]))
    assert result == 0


def test_aggregator_command_returns_one_on_missing_file(tmp_path):
    missing = str(tmp_path / "missing.txt")
    with pytest.raises(SystemExit):
        aggregator_command(_args(files=[missing]))


def test_aggregator_command_returns_one_on_no_valid_traces(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")
    result = aggregator_command(_args(files=[str(p)]))
    assert result == 1


def test_aggregator_command_multiple_files(tmp_path):
    p1 = _write_trace(tmp_path, "t1.txt")
    p2 = _write_trace(tmp_path, "t2.txt")
    result = aggregator_command(_args(files=[str(p1), str(p2)]))
    assert result == 0


def test_aggregator_command_respects_top_flag(tmp_path, capsys):
    p = _write_trace(tmp_path)
    aggregator_command(_args(files=[str(p)], top=3))
    captured = capsys.readouterr()
    assert "3" in captured.out
