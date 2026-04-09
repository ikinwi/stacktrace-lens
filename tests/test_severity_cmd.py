"""Tests for stacktrace_lens.severity_cmd."""

from __future__ import annotations

from argparse import Namespace
from unittest.mock import MagicMock, mock_open, patch

import pytest

from stacktrace_lens.severity_cmd import severity_command

_SAMPLE_TRACE = """
Traceback (most recent call last):
  File "app.py", line 10, in main
    result = 1 / 0
ZeroDivisionError: division by zero
""".strip()


def _args(file=None, no_colour=True, min_severity=None):
    return Namespace(file=file, no_colour=no_colour, min_severity=min_severity)


def test_severity_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = _SAMPLE_TRACE
        code = severity_command(_args())
    assert code == 0


def test_severity_command_returns_one_on_empty_stdin():
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = "   "
        code = severity_command(_args())
    assert code == 1


def test_severity_command_reads_from_file():
    m = mock_open(read_data=_SAMPLE_TRACE)
    with patch("builtins.open", m):
        code = severity_command(_args(file="trace.txt"))
    assert code == 0


def test_severity_command_returns_one_on_missing_file():
    with patch("builtins.open", side_effect=OSError("not found")):
        code = severity_command(_args(file="missing.txt"))
    assert code == 1


def test_severity_command_min_severity_pass():
    """ZeroDivisionError is LOW/MEDIUM; requiring LOW should pass."""
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = _SAMPLE_TRACE
        code = severity_command(_args(min_severity="LOW"))
    assert code == 0


def test_severity_command_min_severity_fail():
    """ZeroDivisionError score should be below CRITICAL threshold."""
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = _SAMPLE_TRACE
        code = severity_command(_args(min_severity="CRITICAL"))
    assert code == 2


def test_severity_command_prints_output(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = _SAMPLE_TRACE
        severity_command(_args())
    captured = capsys.readouterr()
    assert "Severity:" in captured.out
