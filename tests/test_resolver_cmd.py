"""Tests for stacktrace_lens.resolver_cmd."""

from __future__ import annotations

import argparse
import io
import os
import textwrap

import pytest

from stacktrace_lens.resolver_cmd import _build_subparser, resolver_command

_SAMPLE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in main
        run()
      File "utils.py", line 5, in run
        raise ValueError("bad")
    ValueError: bad
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "search_paths": [], "resolve_symlinks": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_resolve():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    parsed = root.parse_args(["resolve"])
    assert parsed is not None


def test_resolver_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    result = resolver_command(_args(), out=out)
    assert result == 0


def test_resolver_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    err = io.StringIO()
    result = resolver_command(_args(), err=err)
    assert result == 1


def test_resolver_command_reads_from_file(tmp_path):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(_SAMPLE)
    out = io.StringIO()
    result = resolver_command(_args(file=str(trace_file)), out=out)
    assert result == 0
    assert "Resolved" in out.getvalue()


def test_resolver_command_returns_one_on_missing_file():
    err = io.StringIO()
    result = resolver_command(_args(file="/no/such/file.txt"), err=err)
    assert result == 1
    assert "not found" in err.getvalue()


def test_resolver_command_uses_search_path(tmp_path, monkeypatch):
    src = tmp_path / "app.py"
    src.write_text("x = 1\n")
    sample = _SAMPLE  # contains 'app.py' as relative path
    monkeypatch.setattr("sys.stdin", io.StringIO(sample))
    out = io.StringIO()
    result = resolver_command(_args(search_paths=[str(tmp_path)]), out=out)
    assert result == 0
    output = out.getvalue()
    assert "app.py" in output
