"""Tests for stacktrace_lens.patcher_cmd."""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile

import pytest

from stacktrace_lens.patcher_cmd import patcher_command

_SAMPLE_TRACE = """\
Traceback (most recent call last):
  File "app/main.py", line 10, in run
    result = compute()
  File "app/core.py", line 42, in compute
    raise ValueError("bad")
ValueError: bad
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"input": None, "rules": None, "line_offset": 0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ── happy path via stdin ──────────────────────────────────────────────────────

def test_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    assert patcher_command(_args(), out=io.StringIO(), err=io.StringIO()) == 0


def test_command_output_contains_summary(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    patcher_command(_args(), out=out, err=io.StringIO())
    assert "frame" in out.getvalue().lower()


# ── empty input ───────────────────────────────────────────────────────────────

def test_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert patcher_command(_args(), out=io.StringIO(), err=io.StringIO()) == 1


# ── file input ────────────────────────────────────────────────────────────────

def test_command_reads_from_file(tmp_path):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(_SAMPLE_TRACE)
    assert patcher_command(_args(input=str(trace_file)), out=io.StringIO(), err=io.StringIO()) == 0


def test_command_returns_one_on_missing_file():
    assert patcher_command(_args(input="/no/such/file.txt"), out=io.StringIO(), err=io.StringIO()) == 1


# ── rules file ────────────────────────────────────────────────────────────────

def test_command_applies_rules_file(tmp_path, monkeypatch):
    rules = [{"filename_contains": "main", "replace_filename": "patched/main.py"}]
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps(rules))

    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    rc = patcher_command(_args(rules=str(rules_file)), out=out, err=io.StringIO())
    assert rc == 0
    assert "patched/main.py" in out.getvalue()


def test_command_returns_one_on_bad_rules_file(tmp_path, monkeypatch):
    bad_file = tmp_path / "rules.json"
    bad_file.write_text("not json at all")

    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    assert patcher_command(_args(rules=str(bad_file)), out=io.StringIO(), err=io.StringIO()) == 1


# ── line_offset flag ──────────────────────────────────────────────────────────

def test_command_applies_global_line_offset(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE_TRACE))
    out = io.StringIO()
    rc = patcher_command(_args(line_offset=100), out=out, err=io.StringIO())
    assert rc == 0
    # line 10 + 100 = 110, line 42 + 100 = 142
    assert "110" in out.getvalue() or "142" in out.getvalue()
