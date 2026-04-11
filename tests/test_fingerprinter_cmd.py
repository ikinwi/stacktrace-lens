"""Tests for stacktrace_lens.fingerprinter_cmd."""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_lens.fingerprinter_cmd import _build_subparser, fingerprinter_command

_SAMPLE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 5, in run
        do_thing()
      File "lib.py", line 12, in do_thing
        raise ValueError("oops")
    ValueError: oops
""")


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(file=None, short=False, include_message=True, max_frames=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_fingerprint():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    parsed = root.parse_args(["fingerprint"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        assert fingerprinter_command(_args()) == 0


def test_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert fingerprinter_command(_args()) == 1


def test_command_reads_from_file(tmp_path: Path):
    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE)
    assert fingerprinter_command(_args(file=str(f))) == 0


def test_command_returns_one_on_missing_file():
    assert fingerprinter_command(_args(file="/no/such/file.txt")) == 1


def test_short_flag_produces_shorter_output(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        fingerprinter_command(_args(short=True))
    out = capsys.readouterr().out
    # The fingerprint line should contain only 8 hex chars, not 64
    fp_line = [l for l in out.splitlines() if "Fingerprint" in l][0]
    fp_value = fp_line.split(":", 1)[1].strip()
    assert len(fp_value) == 8


def test_no_message_flag_accepted(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        rc = fingerprinter_command(_args(include_message=False))
    assert rc == 0


def test_max_frames_flag_accepted(capsys):
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        rc = fingerprinter_command(_args(max_frames=1))
    assert rc == 0
