"""Tests for stacktrace_lens.validator_cmd."""
from __future__ import annotations

import argparse
import io
import tempfile
import os
from unittest.mock import patch

import pytest

from stacktrace_lens.validator_cmd import _build_subparser, validator_command

_SAMPLE = """Traceback (most recent call last):
  File \"app.py\", line 10, in run
    do_thing()
ValueError: something went wrong
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file=None,
        max_depth=None,
        require_message=False,
        allow_empty_frames=False,
        known_types=None,
        no_colour=True,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_validate():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    _build_subparser(subs)
    parsed = parser.parse_args(["validate"])
    assert parsed is not None


def test_command_returns_zero_on_valid_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        code = validator_command(_args(), out=out, err=err)
    assert code == 0


def test_command_returns_one_on_empty_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO("")):
        code = validator_command(_args(), out=out, err=err)
    assert code == 1


def test_command_returns_one_on_missing_file():
    out, err = io.StringIO(), io.StringIO()
    code = validator_command(_args(file="/nonexistent/path.txt"), out=out, err=err)
    assert code == 1


def test_command_reads_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(_SAMPLE)
        name = f.name
    try:
        out, err = io.StringIO(), io.StringIO()
        code = validator_command(_args(file=name), out=out, err=err)
        assert code == 0
        assert "ValueError" in out.getvalue()
    finally:
        os.unlink(name)


def test_command_returns_two_on_violation():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        code = validator_command(_args(max_depth=0), out=out, err=err)
    assert code == 2


def test_command_output_contains_exception_type():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(_SAMPLE)):
        validator_command(_args(), out=out, err=err)
    assert "ValueError" in out.getvalue()
