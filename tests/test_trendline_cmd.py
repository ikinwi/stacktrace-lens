"""Tests for stacktrace_lens.trendline_cmd."""
from __future__ import annotations

import argparse
import json
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest

from stacktrace_lens.trendline_cmd import trendline_command, _build_subparser

_SAMPLE_TRACE = (
    "Traceback (most recent call last):\n"
    '  File "app.py", line 5, in run\n'
    "    do_thing()\n"
    "ValueError: something went wrong\n"
)


def _write_entry(tmp_path: Path, name: str, epoch: float, exc_type: str = "ValueError") -> Path:
    ts = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    data = {"timestamp": ts, "text": _SAMPLE_TRACE, "label": exc_type}
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "bucket": 60, "no_color": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_trendline():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    ns = parser.parse_args(["trendline"])
    assert hasattr(ns, "bucket")


def test_trendline_command_returns_one_on_no_files():
    err = io.StringIO()
    rc = trendline_command(_args(files=[]), err=err)
    assert rc == 1
    assert "no input" in err.getvalue()


def test_trendline_command_returns_one_on_missing_file():
    err = io.StringIO()
    rc = trendline_command(_args(files=["/nonexistent/trace.json"]), err=err)
    assert rc == 1
    assert "not found" in err.getvalue()


def test_trendline_command_returns_zero_on_valid_file(tmp_path):
    f = _write_entry(tmp_path, "t1.json", 0.0)
    out = io.StringIO()
    rc = trendline_command(_args(files=[str(f)]), out=out)
    assert rc == 0


def test_trendline_command_output_contains_summary(tmp_path):
    f = _write_entry(tmp_path, "t1.json", 0.0)
    out = io.StringIO()
    trendline_command(_args(files=[str(f)]), out=out)
    assert "Trend:" in out.getvalue()


def test_trendline_command_multiple_files(tmp_path):
    f1 = _write_entry(tmp_path, "t1.json", 0.0)
    f2 = _write_entry(tmp_path, "t2.json", 60.0)
    out = io.StringIO()
    rc = trendline_command(_args(files=[str(f1), str(f2)]), out=out)
    assert rc == 0
    assert "2" in out.getvalue()
