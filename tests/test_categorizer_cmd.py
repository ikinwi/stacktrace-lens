"""Tests for stacktrace_lens.categorizer_cmd."""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile

import pytest

from stacktrace_lens.categorizer_cmd import _build_subparser, categorizer_command

_SAMPLE_TRACE = """Traceback (most recent call last):
  File "app.py", line 5, in main
    result = 1 / 0
ZeroDivisionError: division by zero
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_categorize():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    parsed = parser.parse_args(["categorize"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    err = io.StringIO()
    rc = categorizer_command(_args(), out=out, err=err)
    assert rc == 0


def test_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    err = io.StringIO()
    rc = categorizer_command(_args(), out=out, err=err)
    assert rc == 1


def test_command_output_contains_category(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    rc = categorizer_command(_args(), out=out)
    assert rc == 0
    assert "runtime" in out.getvalue()


def test_command_reads_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write(_SAMPLE_TRACE)
        path = fh.name
    try:
        out = io.StringIO()
        rc = categorizer_command(_args(file=path), out=out)
        assert rc == 0
        assert out.getvalue().strip() != ""
    finally:
        os.unlink(path)


def test_command_returns_one_on_missing_file():
    out = io.StringIO()
    err = io.StringIO()
    rc = categorizer_command(_args(file="/no/such/file.txt"), out=out, err=err)
    assert rc == 1
    assert "error" in err.getvalue()


def test_json_flag_emits_valid_json(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    rc = categorizer_command(_args(json=True), out=out)
    assert rc == 0
    payload = json.loads(out.getvalue())
    assert "category" in payload
    assert "exception_type" in payload
    assert "confidence" in payload


def test_json_output_category_is_runtime(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    categorizer_command(_args(json=True), out=out)
    payload = json.loads(out.getvalue())
    assert payload["category"] == "runtime"
