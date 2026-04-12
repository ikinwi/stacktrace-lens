"""Tests for stacktrace_lens.scoper."""
from __future__ import annotations

import argparse
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scoper import (
    Scope,
    ScopeReport,
    ScopedFrame,
    _classify,
    format_scope_report,
    scope_trace,
)
from stacktrace_lens.scoper_cmd import _build_subparser, scoper_command


def _frame(filename: str, func: str = "fn", lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=func, context=None)


def _trace(*filenames: str) -> StackTrace:
    frames = [_frame(f) for f in filenames]
    return StackTrace(exception_type="ValueError", message="oops", frames=frames)


# --- _classify ---

def test_classify_user_code():
    assert _classify("/home/user/project/app.py") == Scope.USER


def test_classify_test_file_by_prefix():
    assert _classify("/home/user/project/test_main.py") == Scope.TEST


def test_classify_test_file_by_directory():
    assert _classify("/home/user/project/tests/test_foo.py") == Scope.TEST


def test_classify_stdlib():
    assert _classify("/usr/lib/python3.11/os.py") == Scope.STDLIB


def test_classify_frozen():
    assert _classify("<frozen importlib._bootstrap>") == Scope.STDLIB


def test_classify_third_party():
    assert _classify("/usr/local/lib/python3.11/site-packages/requests/api.py") == Scope.THIRD_PARTY


def test_classify_none_returns_unknown():
    assert _classify(None) == Scope.UNKNOWN


# --- scope_trace ---

def test_scope_trace_returns_scope_report():
    trace = _trace("app.py")
    result = scope_trace(trace)
    assert isinstance(result, ScopeReport)


def test_scope_trace_frame_count_matches():
    trace = _trace("a.py", "b.py", "c.py")
    result = scope_trace(trace)
    assert len(result.frames) == 3


def test_scope_trace_user_frames():
    trace = _trace("/home/dev/project/main.py", "/usr/lib/python3.11/os.py")
    result = scope_trace(trace)
    assert len(result.user_frames) == 1
    assert len(result.stdlib_frames) == 1


def test_scope_trace_test_frames():
    trace = _trace("tests/test_foo.py", "app.py")
    result = scope_trace(trace)
    assert len(result.test_frames) == 1


def test_summary_line_contains_counts():
    trace = _trace("app.py", "/usr/lib/python3.11/os.py")
    report = scope_trace(trace)
    summary = report.summary_line()
    assert "user=" in summary
    assert "stdlib=" in summary


def test_format_scope_report_returns_string():
    trace = _trace("app.py")
    report = scope_trace(trace)
    output = format_scope_report(report)
    assert isinstance(output, str)
    assert len(output) > 0


def test_scoped_frame_str_contains_scope():
    frame = _frame("app.py")
    sf = ScopedFrame(frame=frame, scope=Scope.USER)
    assert "user" in str(sf)


# --- scoper_command ---

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "no_colour": True, "user_only": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


_SAMPLE = """Traceback (most recent call last):
  File "app.py", line 10, in main
    run()
ValueError: bad value
"""


def test_scoper_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin", StringIO(_SAMPLE)):
        assert scoper_command(_args()) == 0


def test_scoper_command_returns_one_on_empty_stdin():
    with patch("sys.stdin", StringIO("")):
        assert scoper_command(_args()) == 1


def test_scoper_command_returns_one_on_missing_file():
    assert scoper_command(_args(file="/nonexistent/path.txt")) == 1


def test_build_subparser_registers_scope():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    parsed = root.parse_args(["scope"])
    assert parsed is not None
