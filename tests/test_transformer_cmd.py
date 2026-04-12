"""Tests for stacktrace_lens.transformer_cmd"""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile

import pytest

from stacktrace_lens.transformer_cmd import _build_subparser, transformer_command

_SAMPLE = """Traceback (most recent call last):
  File "/app/main.py", line 5, in run
    result = compute()
  File "/app/utils.py", line 12, in compute
    return 1 / 0
ZeroDivisionError: division by zero
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "rename_file": [],
        "rename_func": [],
        "strip_prefix": [],
        "file": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_transform():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    assert transformer_command(_args(), out=out) == 0


def test_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    err = io.StringIO()
    assert transformer_command(_args(), err=err) == 1


def test_command_returns_one_on_missing_file():
    err = io.StringIO()
    assert transformer_command(_args(file="/no/such/file.txt"), err=err) == 1
    assert "error" in err.getvalue()


def test_command_reads_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write(_SAMPLE)
        name = fh.name
    try:
        out = io.StringIO()
        rc = transformer_command(_args(file=name), out=out)
        assert rc == 0
    finally:
        os.unlink(name)


def test_rename_file_rule_applied(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    transformer_command(_args(rename_file=["/app/=src/"]), out=out)
    assert "src/" in out.getvalue()


def test_strip_prefix_rule_applied(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    transformer_command(_args(strip_prefix=["/app/"]), out=out)
    output = out.getvalue()
    assert "main.py" in output or "utils.py" in output
