"""Tests for stacktrace_lens.snapshotter_cmd."""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_lens.snapshotter_cmd import _build_subparser, snapshotter_command

_SAMPLE_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "lib.py", line 5, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"input": "-", "output": "-", "label": None, "list_snaps": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_snapshot():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin.read", return_value=_SAMPLE_TRACE):
        assert snapshotter_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin.read", return_value=""):
        assert snapshotter_command(_args()) == 1


def test_command_returns_one_on_missing_file():
    assert snapshotter_command(_args(input="/no/such/file.txt")) == 1


def test_command_reads_from_file(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE_TRACE)
    assert snapshotter_command(_args(input=str(f))) == 0


def test_command_writes_to_file(tmp_path: Path):
    src = tmp_path / "trace.txt"
    src.write_text(_SAMPLE_TRACE)
    out = tmp_path / "snap.json"
    code = snapshotter_command(_args(input=str(src), output=str(out)))
    assert code == 0
    data = json.loads(out.read_text())
    assert data["exception_type"] == "ValueError"


def test_command_stores_label(tmp_path: Path):
    src = tmp_path / "trace.txt"
    src.write_text(_SAMPLE_TRACE)
    out = tmp_path / "snap.json"
    snapshotter_command(_args(input=str(src), output=str(out), label="ci-run-42"))
    data = json.loads(out.read_text())
    assert data["label"] == "ci-run-42"


def test_list_command_returns_zero(tmp_path: Path):
    from stacktrace_lens.parser import Frame, StackTrace
    from stacktrace_lens.snapshotter import Snapshot, dump_snapshots

    trace = StackTrace(
        exception_type="RuntimeError",
        exception_message="boom",
        frames=[Frame(filename="a.py", lineno=1, function="f", source=None)],
    )
    snap_file = tmp_path / "snaps.json"
    snap_file.write_text(dump_snapshots([Snapshot(trace=trace, label="t1")]))
    assert snapshotter_command(_args(list_snaps=str(snap_file))) == 0


def test_list_command_returns_one_on_missing_file():
    assert snapshotter_command(_args(list_snaps="/no/such/snaps.json")) == 1
