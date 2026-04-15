"""Tests for stacktrace_lens.scorer7_cmd."""
import argparse
import io
import textwrap

import pytest

from stacktrace_lens.scorer7_cmd import _build_subparser, scorer7_command


SAMPLE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 5, in run
        result = 1 / 0
    ZeroDivisionError: division by zero
""")


def _args(**kwargs):
    base = {"file": None, "no_colour": True, "top": False}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_build_subparser_registers_score7():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    ns = root.parse_args(["score7"])
    assert ns is not None


def test_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE))
    out = io.StringIO()
    assert scorer7_command(_args(), out=out) == 0


def test_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    err = io.StringIO()
    assert scorer7_command(_args(), err=err) == 1


def test_command_output_contains_exception_type(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE))
    out = io.StringIO()
    scorer7_command(_args(), out=out)
    assert "ZeroDivisionError" in out.getvalue()


def test_command_reads_from_file(tmp_path, monkeypatch):
    f = tmp_path / "trace.txt"
    f.write_text(SAMPLE)
    out = io.StringIO()
    assert scorer7_command(_args(file=str(f)), out=out) == 0
    assert "ZeroDivisionError" in out.getvalue()


def test_command_returns_one_on_missing_file():
    err = io.StringIO()
    assert scorer7_command(_args(file="/nonexistent/trace.txt"), err=err) == 1
    assert "error" in err.getvalue()


def test_top_flag_returns_single_frame(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(SAMPLE))
    out = io.StringIO()
    scorer7_command(_args(top=True), out=out)
    # With --top only one frame line should appear (plus the header)
    lines = [l for l in out.getvalue().splitlines() if l.strip()]
    assert len(lines) == 2  # header + 1 frame
