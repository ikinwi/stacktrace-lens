"""Tests for stacktrace_lens.scorer_cmd."""
from __future__ import annotations

import argparse
import io
import textwrap
from unittest.mock import patch

import pytest

from stacktrace_lens.scorer_cmd import scorer_command, _build_subparser

_SAMPLE_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "myapp/main.py", line 12, in run
        result = compute(x)
      File "myapp/compute.py", line 7, in compute
        return 1 / x
    ZeroDivisionError: division by zero
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "top": 0, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# subparser registration
# ---------------------------------------------------------------------------

def test_build_subparser_registers_score():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    parsed = root.parse_args(["score"])
    assert parsed is not None


# ---------------------------------------------------------------------------
# scorer_command return codes
# ---------------------------------------------------------------------------

def test_scorer_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        assert scorer_command(_args()) == 0


def test_scorer_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert scorer_command(_args()) == 1


def test_scorer_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE_TRACE)
    assert scorer_command(_args(file=str(f))) == 0


def test_scorer_command_returns_one_on_missing_file():
    assert scorer_command(_args(file="/nonexistent/trace.txt")) == 1


# ---------------------------------------------------------------------------
# output content
# ---------------------------------------------------------------------------

def test_scorer_command_output_contains_filename(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        scorer_command(_args())
    out = capsys.readouterr().out
    assert "myapp" in out


def test_scorer_command_top_limits_output(capsys):
    trace = textwrap.dedent("""\
        Traceback (most recent call last):
          File "a.py", line 1, in f1
            pass
          File "b.py", line 2, in f2
            pass
          File "c.py", line 3, in f3
            pass
        RuntimeError: boom
    """)
    with patch("sys.stdin", io.StringIO(trace)):
        scorer_command(_args(top=1))
    out = capsys.readouterr().out
    # Only one scored line should appear (plus header)
    scored_lines = [l for l in out.splitlines() if "+" in l or "-" in l]
    assert len(scored_lines) == 1


def test_scorer_command_no_color_no_ansi(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        scorer_command(_args(no_color=True))
    out = capsys.readouterr().out
    assert "\033[" not in out
