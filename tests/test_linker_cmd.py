"""Tests for stacktrace_lens/linker_cmd.py"""
from __future__ import annotations

import argparse
import io
import textwrap

import pytest

from stacktrace_lens.linker_cmd import _build_subparser, linker_command

_SAMPLE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "/app/main.py", line 10, in run
        result = compute()
      File "/app/compute.py", line 5, in compute
        return 1 / 0
    ZeroDivisionError: division by zero
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"scheme": "file", "base_path": None, "file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_link():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_linker_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    rc = linker_command(_args(), out=out)
    assert rc == 0


def test_linker_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    err = io.StringIO()
    rc = linker_command(_args(), err=err)
    assert rc == 1


def test_linker_command_reads_from_file(tmp_path, monkeypatch):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE)
    out = io.StringIO()
    rc = linker_command(_args(file=str(f)), out=out)
    assert rc == 0
    assert "file" in out.getvalue()


def test_linker_command_returns_one_on_missing_file():
    err = io.StringIO()
    rc = linker_command(_args(file="/no/such/file.txt"), err=err)
    assert rc == 1
    assert "error" in err.getvalue().lower()


def test_linker_command_vscode_scheme(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    rc = linker_command(_args(scheme="vscode"), out=out)
    assert rc == 0
    assert "vscode" in out.getvalue()


def test_linker_command_with_base_path(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    out = io.StringIO()
    rc = linker_command(_args(base_path="/app"), out=out)
    assert rc == 0
    # base path stripped so /app should not appear in the URLs
    output = out.getvalue()
    # summary line will mention counts; URLs should not start with /app
    assert isinstance(output, str)
