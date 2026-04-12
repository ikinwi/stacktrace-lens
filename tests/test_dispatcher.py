"""Tests for stacktrace_lens.dispatcher and dispatcher_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.dispatcher import (
    DispatchResult,
    DispatchRule,
    Dispatcher,
    build_default_dispatcher,
)
from stacktrace_lens.dispatcher_cmd import _build_subparser, dispatcher_command


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_trace(exc_type: str = "ValueError", message: str = "bad value") -> StackTrace:
    frame = Frame(filename="app.py", lineno=10, function="main", source_line="x = 1/0")
    return StackTrace(exception_type=exc_type, exception_message=message, frames=[frame])


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "show_rule": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# DispatchRule / Dispatcher
# ---------------------------------------------------------------------------

def test_dispatch_result_matched_flag():
    r = DispatchResult(rule_name="test", output="hello", matched=True)
    assert r.matched is True


def test_dispatcher_returns_dispatch_result():
    d = Dispatcher()
    rule = DispatchRule("always", lambda _: True, lambda t: "matched", priority=1)
    d.register(rule)
    result = d.dispatch(_make_trace())
    assert isinstance(result, DispatchResult)


def test_dispatcher_matched_rule_name():
    d = Dispatcher()
    rule = DispatchRule("my_rule", lambda _: True, lambda t: "ok")
    d.register(rule)
    result = d.dispatch(_make_trace())
    assert result.rule_name == "my_rule"


def test_dispatcher_no_match_uses_fallback():
    d = Dispatcher(fallback=lambda t: "fallback_output")
    result = d.dispatch(_make_trace())
    assert result.output == "fallback_output"
    assert result.matched is False


def test_dispatcher_no_match_no_fallback_returns_empty():
    d = Dispatcher()
    result = d.dispatch(_make_trace())
    assert result.output == ""
    assert result.rule_name == "none"


def test_dispatcher_higher_priority_wins():
    d = Dispatcher()
    d.register(DispatchRule("low", lambda _: True, lambda t: "low", priority=1))
    d.register(DispatchRule("high", lambda _: True, lambda t: "high", priority=10))
    result = d.dispatch(_make_trace())
    assert result.rule_name == "high"


def test_dispatcher_skips_non_matching_rule():
    d = Dispatcher(fallback=lambda t: "fb")
    d.register(DispatchRule("never", lambda _: False, lambda t: "nope", priority=5))
    result = d.dispatch(_make_trace())
    assert result.rule_name == "fallback"


# ---------------------------------------------------------------------------
# build_default_dispatcher
# ---------------------------------------------------------------------------

def test_build_default_dispatcher_returns_dispatcher():
    d = build_default_dispatcher()
    assert isinstance(d, Dispatcher)


def test_default_dispatcher_handles_zero_division():
    trace = _make_trace(exc_type="ZeroDivisionError", message="division by zero")
    d = build_default_dispatcher()
    result = d.dispatch(trace)
    assert isinstance(result.output, str)
    assert len(result.output) > 0


def test_default_dispatcher_fallback_for_unknown():
    trace = _make_trace(exc_type="ObscureError", message="something weird")
    d = build_default_dispatcher()
    result = d.dispatch(trace)
    assert "ObscureError" in result.output


# ---------------------------------------------------------------------------
# dispatcher_cmd
# ---------------------------------------------------------------------------

def test_build_subparser_registers_dispatch():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    ns = root.parse_args(["dispatch"])
    assert ns is not None


RAW_TRACE = (
    "Traceback (most recent call last):\n"
    '  File "app.py", line 5, in run\n'
    "    result = 1 / 0\n"
    "ZeroDivisionError: division by zero\n"
)


def test_dispatcher_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin.read", return_value=RAW_TRACE):
        assert dispatcher_command(_args()) == 0


def test_dispatcher_command_returns_one_on_empty_stdin():
    with patch("sys.stdin.read", return_value="   "):
        assert dispatcher_command(_args()) == 1


def test_dispatcher_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(RAW_TRACE)
    assert dispatcher_command(_args(file=str(f))) == 0


def test_dispatcher_command_returns_one_on_missing_file():
    assert dispatcher_command(_args(file="/no/such/file.txt")) == 1


def test_dispatcher_command_show_rule_flag(capsys):
    with patch("sys.stdin.read", return_value=RAW_TRACE):
        rc = dispatcher_command(_args(show_rule=True))
    assert rc == 0
    captured = capsys.readouterr()
    assert "rule:" in captured.out
