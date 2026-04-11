"""Tests for stacktrace_lens.differ_cmd."""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.differ_cmd import _build_subparser, differ_command

_TRACE_TEXT = """Traceback (most recent call last):
  File \"app.py\", line 10, in run
    result = compute()
ValueError: bad value
"""

_TRACE_TEXT_2 = """Traceback (most recent call last):
  File \"app.py\", line 10, in run
    result = compute()
  File \"utils.py\", line 5, in compute
    return int(x)
TypeError: wrong type
"""


def _write(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "left": "",
        "right": "",
        "no_colour": True,
        "hide_unchanged": False,
        "summary": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_differ():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = _build_subparser(sub)
    assert p is not None


def test_differ_command_returns_zero_on_valid_files():
    left = _write(_TRACE_TEXT)
    right = _write(_TRACE_TEXT)
    try:
        args = _args(left=left, right=right)
        rc = differ_command(args, out=io.StringIO(), err=io.StringIO())
        assert rc == 0
    finally:
        os.unlink(left)
        os.unlink(right)


def test_differ_command_returns_one_on_missing_left():
    right = _write(_TRACE_TEXT)
    try:
        args = _args(left="/no/such/file.txt", right=right)
        rc = differ_command(args, out=io.StringIO(), err=io.StringIO())
        assert rc == 1
    finally:
        os.unlink(right)


def test_differ_command_returns_one_on_missing_right():
    left = _write(_TRACE_TEXT)
    try:
        args = _args(left=left, right="/no/such/file.txt")
        rc = differ_command(args, out=io.StringIO(), err=io.StringIO())
        assert rc == 1
    finally:
        os.unlink(left)


def test_differ_command_summary_flag():
    left = _write(_TRACE_TEXT)
    right = _write(_TRACE_TEXT_2)
    try:
        out = io.StringIO()
        args = _args(left=left, right=right, summary=True)
        rc = differ_command(args, out=out, err=io.StringIO())
        assert rc == 0
        text = out.getvalue()
        assert "TraceDiff" in text
    finally:
        os.unlink(left)
        os.unlink(right)


def test_differ_command_output_contains_exception_type():
    left = _write(_TRACE_TEXT)
    right = _write(_TRACE_TEXT)
    try:
        out = io.StringIO()
        args = _args(left=left, right=right)
        differ_command(args, out=out, err=io.StringIO())
        assert "ValueError" in out.getvalue()
    finally:
        os.unlink(left)
        os.unlink(right)
