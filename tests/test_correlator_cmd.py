"""Tests for stacktrace_lens.correlator_cmd."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from stacktrace_lens.correlator_cmd import correlator_command, _build_subparser


SAMPLE_TRACE = """Traceback (most recent call last):
  File "app.py", line 5, in run
    result = 1 / 0
ZeroDivisionError: division by zero
"""


def _write_trace(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_correlate():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    ns = parser.parse_args(["correlate", "file.txt"])
    assert ns.files == ["file.txt"]


def test_correlator_command_returns_zero_on_valid_file():
    path = _write_trace(SAMPLE_TRACE)
    try:
        result = correlator_command(_args(files=[path]))
        assert result == 0
    finally:
        os.unlink(path)


def test_correlator_command_returns_one_on_missing_file():
    result = correlator_command(_args(files=["/nonexistent/path/trace.txt"]))
    assert result == 1


def test_correlator_command_multiple_files():
    p1 = _write_trace(SAMPLE_TRACE)
    p2 = _write_trace(SAMPLE_TRACE.replace("ZeroDivisionError", "ValueError"))
    try:
        result = correlator_command(_args(files=[p1, p2]))
        assert result == 0
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_correlator_command_json_flag(capsys):
    path = _write_trace(SAMPLE_TRACE)
    try:
        result = correlator_command(_args(files=[path], json=True))
        assert result == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert "total_traces" in payload
        assert "by_exception" in payload
    finally:
        os.unlink(path)


def test_correlator_command_reads_stdin():
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = SAMPLE_TRACE
        result = correlator_command(_args(files=["-"]))
        assert result == 0
