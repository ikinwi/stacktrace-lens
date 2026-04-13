"""Tests for stacktrace_lens.replayer_cmd."""
from __future__ import annotations

import argparse
import io
import json
import tempfile
from pathlib import Path

import pytest

from stacktrace_lens.replayer_cmd import _build_subparser, replayer_command


def _write(tmp_path: Path, name: str, data: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


def _trace_data(exc_type="ValueError", msg="oops", label="t1"):
    return {
        "exception_type": exc_type,
        "exception_message": msg,
        "label": label,
        "frames": [{"filename": "app.py", "lineno": 5, "function": "go"}],
    }


def _args(**kwargs):
    defaults = {"files": [], "speed": 1.0, "max_entries": None, "loop": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_replay():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    ns = root.parse_args(["replay"])
    assert hasattr(ns, "files")


def test_replayer_command_returns_one_on_no_files():
    out = io.StringIO()
    code = replayer_command(_args(files=[]), out=out)
    assert code == 1


def test_replayer_command_returns_one_on_missing_file():
    out = io.StringIO()
    code = replayer_command(_args(files=["/nonexistent/trace.json"]), out=out)
    assert code == 1


def test_replayer_command_returns_zero_on_valid_file(tmp_path):
    f = _write(tmp_path, "t.json", _trace_data())
    out = io.StringIO()
    code = replayer_command(_args(files=[f]), out=out)
    assert code == 0


def test_replayer_command_output_contains_exception_type(tmp_path):
    f = _write(tmp_path, "t.json", _trace_data(exc_type="KeyError"))
    out = io.StringIO()
    replayer_command(_args(files=[f]), out=out)
    assert "KeyError" in out.getvalue()


def test_replayer_command_output_contains_summary(tmp_path):
    f = _write(tmp_path, "t.json", _trace_data())
    out = io.StringIO()
    replayer_command(_args(files=[f]), out=out)
    assert "Replayed" in out.getvalue()


def test_replayer_command_max_entries_limits_output(tmp_path):
    files = [_write(tmp_path, f"t{i}.json", _trace_data(label=f"t{i}")) for i in range(4)]
    out = io.StringIO()
    replayer_command(_args(files=files, max_entries=2), out=out)
    assert "2" in out.getvalue()
