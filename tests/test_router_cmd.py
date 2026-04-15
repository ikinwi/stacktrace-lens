"""Tests for stacktrace_lens.router_cmd."""
from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from stacktrace_lens.router_cmd import _build_subparser, router_command

_VALID_TRACE = """Traceback (most recent call last):
  File \"app.py\", line 10, in run
    do_thing()
ValueError: something went wrong
"""


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "files": [],
        "exception": None,
        "file": None,
        "name": "default",
        "no_color": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_route():
    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers()
    _build_subparser(subs)
    ns = parent.parse_args(["route"])
    assert ns is not None


def test_router_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", io.StringIO(_VALID_TRACE)):
        assert router_command(_args()) == 0


def test_router_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", io.StringIO("")):
        assert router_command(_args()) == 1


def test_router_command_reads_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write(_VALID_TRACE)
        path = fh.name
    try:
        assert router_command(_args(files=[path])) == 0
    finally:
        os.unlink(path)


def test_router_command_returns_one_on_missing_file():
    assert router_command(_args(files=["/nonexistent/trace.txt"])) == 1


def test_router_command_with_exception_pattern():
    with patch("sys.stdin", io.StringIO(_VALID_TRACE)):
        assert router_command(_args(exception="ValueError")) == 0


def test_router_command_output_contains_result(capsys):
    with patch("sys.stdin", io.StringIO(_VALID_TRACE)):
        router_command(_args(name="myroute", exception="ValueError"))
    captured = capsys.readouterr()
    assert "myroute" in captured.out
