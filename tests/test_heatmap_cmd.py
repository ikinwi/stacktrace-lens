"""Tests for stacktrace_lens.heatmap_cmd."""
from __future__ import annotations

import argparse
import json
import textwrap
from io import StringIO
from pathlib import Path

import pytest

from stacktrace_lens.heatmap_cmd import _build_subparser, heatmap_command


_RAW_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "lib.py", line 5, in do_thing
        raise ValueError("bad")
    ValueError: bad
""")


def _args(files=None, top=10, as_json=False) -> argparse.Namespace:
    return argparse.Namespace(files=files or [], top=top, as_json=as_json)


def test_build_subparser_registers_heatmap():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_heatmap_command_returns_one_on_no_files():
    out, err = StringIO(), StringIO()
    rc = heatmap_command(_args(files=[]), out=out, err=err)
    assert rc == 1
    assert "no input files" in err.getvalue()


def test_heatmap_command_returns_one_on_missing_file():
    out, err = StringIO(), StringIO()
    rc = heatmap_command(_args(files=["/nonexistent/trace.txt"]), out=out, err=err)
    assert rc == 1
    assert "not found" in err.getvalue()


def test_heatmap_command_returns_zero_on_valid_file(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_RAW_TRACE, encoding="utf-8")
    out, err = StringIO(), StringIO()
    rc = heatmap_command(_args(files=[str(f)]), out=out, err=err)
    assert rc == 0
    assert "app.py" in out.getvalue() or "lib.py" in out.getvalue()


def test_heatmap_command_json_output(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_RAW_TRACE, encoding="utf-8")
    out, err = StringIO(), StringIO()
    rc = heatmap_command(_args(files=[str(f)], as_json=True), out=out, err=err)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert "total_frames" in data
    assert "by_file" in data
    assert "by_function" in data


def test_heatmap_command_json_trace_file(tmp_path: Path):
    payload = json.dumps({"raw": _RAW_TRACE})
    f = tmp_path / "trace.json"
    f.write_text(payload, encoding="utf-8")
    out, err = StringIO(), StringIO()
    rc = heatmap_command(_args(files=[str(f)]), out=out, err=err)
    assert rc == 0


def test_heatmap_command_multiple_files(tmp_path: Path):
    f1 = tmp_path / "t1.txt"
    f2 = tmp_path / "t2.txt"
    f1.write_text(_RAW_TRACE, encoding="utf-8")
    f2.write_text(_RAW_TRACE, encoding="utf-8")
    out, err = StringIO(), StringIO()
    rc = heatmap_command(_args(files=[str(f1), str(f2)], as_json=True), out=out, err=err)
    assert rc == 0
    data = json.loads(out.getvalue())
    # Two identical traces → total_frames should be double
    assert data["total_frames"] >= 2
