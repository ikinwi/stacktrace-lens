"""Tests for stacktrace_lens.ranker_cmd."""
from __future__ import annotations

import argparse
import json
import textwrap
from io import StringIO
from pathlib import Path

import pytest

from stacktrace_lens.ranker_cmd import _build_subparser, ranker_command

_SAMPLE_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        do_thing()
      File "app/utils.py", line 42, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def _write_trace(tmp_path: Path, name: str = "trace.txt") -> Path:
    p = tmp_path / name
    p.write_text(_SAMPLE_TRACE)
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "no_colour": True, "as_json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_rank():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    ns = root.parse_args(["rank", "some_file.txt"])
    assert ns.files == ["some_file.txt"]


def test_ranker_command_returns_zero_on_valid_file(tmp_path):
    p = _write_trace(tmp_path)
    out, err = StringIO(), StringIO()
    rc = ranker_command(_args(files=[str(p)]), out=out, err=err)
    assert rc == 0


def test_ranker_command_returns_one_on_missing_file(tmp_path):
    out, err = StringIO(), StringIO()
    rc = ranker_command(_args(files=[str(tmp_path / "missing.txt")]), out=out, err=err)
    assert rc == 1


def test_ranker_command_output_contains_exception_type(tmp_path):
    p = _write_trace(tmp_path)
    out, err = StringIO(), StringIO()
    ranker_command(_args(files=[str(p)]), out=out, err=err)
    assert "ValueError" in out.getvalue()


def test_ranker_command_json_flag(tmp_path):
    p = _write_trace(tmp_path)
    out, err = StringIO(), StringIO()
    rc = ranker_command(_args(files=[str(p)], as_json=True), out=out, err=err)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["exception_type"] == "ValueError"


def test_ranker_command_json_has_composite(tmp_path):
    p = _write_trace(tmp_path)
    out, err = StringIO(), StringIO()
    ranker_command(_args(files=[str(p)], as_json=True), out=out, err=err)
    data = json.loads(out.getvalue())
    assert "composite" in data[0]


def test_ranker_command_multiple_files_ranked(tmp_path):
    p1 = _write_trace(tmp_path, "t1.txt")
    p2 = _write_trace(tmp_path, "t2.txt")
    out, err = StringIO(), StringIO()
    rc = ranker_command(_args(files=[str(p1), str(p2)], as_json=True), out=out, err=err)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert len(data) == 2
