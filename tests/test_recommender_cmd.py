"""Tests for stacktrace_lens.recommender_cmd."""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
from unittest import mock

import pytest

from stacktrace_lens.recommender_cmd import _build_subparser, recommender_command

_SAMPLE_TRACE = """\
Traceback (most recent call last):
  File "app/main.py", line 10, in run
    result = compute(0)
  File "app/math_utils.py", line 5, in compute
    return 1 / value
ZeroDivisionError: division by zero
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "no_colour": True, "top": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _build_subparser
# ---------------------------------------------------------------------------

def test_build_subparser_registers_recommend():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    args = root.parse_args(["recommend"])
    assert hasattr(args, "file")


# ---------------------------------------------------------------------------
# recommender_command — stdin path
# ---------------------------------------------------------------------------

def test_command_returns_zero_on_valid_stdin():
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        with mock.patch("sys.stdin.isatty", return_value=False):
            code = recommender_command(_args(), out=out, err=err)
    assert code == 0


def test_command_returns_one_on_empty_stdin():
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO("")):
        with mock.patch("sys.stdin.isatty", return_value=False):
            code = recommender_command(_args(), out=out, err=err)
    assert code == 1


def test_command_output_contains_exception_type():
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(_SAMPLE_TRACE)):
        with mock.patch("sys.stdin.isatty", return_value=False):
            recommender_command(_args(), out=out, err=err)
    assert "ZeroDivisionError" in out.getvalue()


# ---------------------------------------------------------------------------
# recommender_command — file path
# ---------------------------------------------------------------------------

def test_command_returns_zero_on_valid_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write(_SAMPLE_TRACE)
        path = fh.name
    try:
        out, err = io.StringIO(), io.StringIO()
        code = recommender_command(_args(file=path), out=out, err=err)
        assert code == 0
    finally:
        os.unlink(path)


def test_command_returns_one_on_missing_file():
    out, err = io.StringIO(), io.StringIO()
    code = recommender_command(_args(file="/nonexistent/trace.txt"), out=out, err=err)
    assert code == 1
    assert "not found" in err.getvalue()


# ---------------------------------------------------------------------------
# --top flag
# ---------------------------------------------------------------------------

def test_top_flag_prints_single_recommendation():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write(_SAMPLE_TRACE)
        path = fh.name
    try:
        out, err = io.StringIO(), io.StringIO()
        code = recommender_command(_args(file=path, top=True), out=out, err=err)
        assert code == 0
        # Output should be a single line (the top recommendation)
        non_empty = [l for l in out.getvalue().splitlines() if l.strip()]
        assert len(non_empty) == 1
    finally:
        os.unlink(path)
