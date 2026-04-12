"""Tests for stacktrace_lens.splitter."""
from __future__ import annotations

import argparse
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from stacktrace_lens.splitter import SplitReport, format_split, split_trace
from stacktrace_lens.splitter_cmd import _build_subparser, splitter_command

_SINGLE = """\
Traceback (most recent call last):
  File "app.py", line 10, in run
    do_thing()
  File "app.py", line 5, in do_thing
    raise ValueError("oops")
ValueError: oops
"""

_CHAINED = """\
Traceback (most recent call last):
  File "app.py", line 5, in do_thing
    raise KeyError("missing")
KeyError: 'missing'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "app.py", line 10, in run
    handle()
  File "app.py", line 8, in handle
    raise RuntimeError("wrapped")
RuntimeError: wrapped
"""

_CAUSED_BY = """\
Traceback (most recent call last):
  File "a.py", line 1, in f
    raise IOError("disk")
IOError: disk

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "b.py", line 2, in g
    raise OSError("fatal")
OSError: fatal
"""


def test_split_single_returns_one_trace():
    report = split_trace(_SINGLE)
    assert report.count == 1


def test_split_chained_returns_two_traces():
    report = split_trace(_CHAINED)
    assert report.count == 2


def test_split_caused_by_returns_two_traces():
    report = split_trace(_CAUSED_BY)
    assert report.count == 2


def test_is_chained_false_for_single():
    report = split_trace(_SINGLE)
    assert report.is_chained is False


def test_is_chained_true_for_chained():
    report = split_trace(_CHAINED)
    assert report.is_chained is True


def test_split_report_exception_types():
    report = split_trace(_CHAINED)
    types = [t.exception_type for t in report.traces]
    assert "KeyError" in types
    assert "RuntimeError" in types


def test_format_split_returns_string():
    report = split_trace(_SINGLE)
    result = format_split(report)
    assert isinstance(result, str)


def test_format_split_contains_exception_type():
    report = split_trace(_SINGLE)
    result = format_split(report, colour=False)
    assert "ValueError" in result


def test_format_split_empty_report():
    report = SplitReport(traces=[])
    result = format_split(report)
    assert "no traces" in result


# --- CLI tests ---

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "no_color": True, "count_only": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_split():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    _build_subparser(sub)
    ns = root.parse_args(["split"])
    assert ns is not None


def test_splitter_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", StringIO(_SINGLE)):
        assert splitter_command(_args()) == 0


def test_splitter_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", StringIO("")):
        assert splitter_command(_args()) == 1


def test_splitter_command_count_only():
    with patch("sys.stdin", StringIO(_CHAINED)):
        with patch("builtins.print") as mock_print:
            code = splitter_command(_args(count_only=True))
    assert code == 0
    mock_print.assert_called_once_with(2)


def test_splitter_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(_CHAINED)
    assert splitter_command(_args(file=str(f))) == 0


def test_splitter_command_returns_one_on_missing_file():
    assert splitter_command(_args(file="/nonexistent/trace.txt")) == 1
