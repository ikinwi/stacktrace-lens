"""Tests for stacktrace_lens.chainer."""
from __future__ import annotations

import argparse
import io
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.chainer import (
    ChainLink,
    ChainReport,
    chain_traces,
    format_chain,
)
from stacktrace_lens.chainer_cmd import chainer_command, _build_subparser


def _make_trace(exc_type: str = "ValueError", exc_msg: str = "oops", n_frames: int = 2) -> StackTrace:
    frames = [
        Frame(filename=f"app/mod{i}.py", lineno=i * 10, function=f"fn{i}", context="pass")
        for i in range(n_frames)
    ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# ---------------------------------------------------------------------------
# ChainReport
# ---------------------------------------------------------------------------

def test_chain_report_count_empty():
    assert ChainReport().count == 0


def test_chain_report_is_chained_false_for_single():
    report = chain_traces([_make_trace()])
    assert report.is_chained is False


def test_chain_report_is_chained_true_for_two():
    report = chain_traces([_make_trace(), _make_trace("RuntimeError", "bad")])
    assert report.is_chained is True


def test_chain_report_count_matches_input():
    traces = [_make_trace(), _make_trace("KeyError", "k"), _make_trace("OSError", "io")]
    report = chain_traces(traces)
    assert report.count == 3


def test_first_link_has_no_cause():
    report = chain_traces([_make_trace(), _make_trace("RuntimeError", "bad")])
    assert report.links[0].cause is None


def test_subsequent_link_has_cause():
    report = chain_traces([_make_trace(), _make_trace("RuntimeError", "bad")])
    assert report.links[1].cause is not None


def test_chain_traces_empty_list():
    report = chain_traces([])
    assert report.count == 0
    assert report.is_chained is False


def test_summary_line_no_chain():
    report = chain_traces([_make_trace()])
    assert "No exception chain" in report.summary_line()


def test_summary_line_with_chain():
    report = chain_traces([_make_trace(), _make_trace("RuntimeError", "x")])
    line = report.summary_line()
    assert "2 links" in line


# ---------------------------------------------------------------------------
# format_chain
# ---------------------------------------------------------------------------

def test_format_chain_returns_string():
    report = chain_traces([_make_trace()])
    assert isinstance(format_chain(report), str)


def test_format_chain_contains_exception_type():
    report = chain_traces([_make_trace("TypeError", "bad type")])
    assert "TypeError" in format_chain(report)


def test_format_chain_contains_frame_count():
    report = chain_traces([_make_trace(n_frames=3)])
    assert "3 frame" in format_chain(report)


# ---------------------------------------------------------------------------
# chainer_cmd
# ---------------------------------------------------------------------------

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "no_color": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


RAW_TRACE = (
    "Traceback (most recent call last):\n"
    '  File "app.py", line 5, in run\n'
    "    raise ValueError('oops')\n"
    "ValueError: oops\n"
)


def test_build_subparser_registers_chain():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    ns = parser.parse_args(["chain"])
    assert hasattr(ns, "files")


def test_chainer_command_returns_zero_on_valid_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(RAW_TRACE)):
        rc = chainer_command(_args(), out=out, err=err)
    assert rc == 0


def test_chainer_command_returns_one_on_empty_stdin():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO("")):
        rc = chainer_command(_args(), out=out, err=err)
    assert rc == 1


def test_chainer_command_returns_one_on_missing_file():
    out, err = io.StringIO(), io.StringIO()
    rc = chainer_command(_args(files=["/no/such/file.json"]), out=out, err=err)
    assert rc == 1
    assert "not found" in err.getvalue()


def test_chainer_command_output_contains_summary():
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdin", io.StringIO(RAW_TRACE)):
        chainer_command(_args(), out=out, err=err)
    assert "exception" in out.getvalue().lower()
