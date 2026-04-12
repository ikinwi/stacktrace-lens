"""Tests for stacktrace_lens.tokenizer."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.tokenizer import (
    Token,
    TokenKind,
    TokenReport,
    tokenize_trace,
    _package_of,
)
from stacktrace_lens.tokenizer_cmd import _build_subparser, _render, tokenizer_command


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _frame(filename: str = "myapp/views.py", lineno: int = 10, function: str = "handle") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(exc_type: str = "ValueError", exc_msg: str = "bad value", frames=None) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# ---------------------------------------------------------------------------
# tokenize_trace
# ---------------------------------------------------------------------------

def test_tokenize_returns_token_report():
    assert isinstance(tokenize_trace(_trace()), TokenReport)


def test_token_report_has_exception_type_token():
    report = tokenize_trace(_trace(exc_type="RuntimeError"))
    types = [t.value for t in report.by_kind(TokenKind.EXCEPTION_TYPE)]
    assert "RuntimeError" in types


def test_token_report_has_exception_message_token():
    report = tokenize_trace(_trace(exc_msg="oops"))
    msgs = [t.value for t in report.by_kind(TokenKind.EXCEPTION_MESSAGE)]
    assert "oops" in msgs


def test_token_report_filename_token_per_frame():
    frames = [_frame("a/b.py"), _frame("c/d.py")]
    report = tokenize_trace(_trace(frames=frames))
    filenames = [t.value for t in report.by_kind(TokenKind.FILENAME)]
    assert "a/b.py" in filenames
    assert "c/d.py" in filenames


def test_token_report_lineno_token_per_frame():
    frames = [_frame(lineno=42)]
    report = tokenize_trace(_trace(frames=frames))
    linenos = [t.value for t in report.by_kind(TokenKind.LINE_NUMBER)]
    assert "42" in linenos


def test_token_report_function_token_per_frame():
    frames = [_frame(function="do_thing")]
    report = tokenize_trace(_trace(frames=frames))
    fns = [t.value for t in report.by_kind(TokenKind.FUNCTION_NAME)]
    assert "do_thing" in fns


def test_token_report_package_token_per_frame():
    frames = [_frame(filename="myapp/views.py")]
    report = tokenize_trace(_trace(frames=frames))
    pkgs = [t.value for t in report.by_kind(TokenKind.PACKAGE)]
    assert "myapp" in pkgs


def test_for_frame_returns_only_that_frames_tokens():
    frames = [_frame("a.py", lineno=1), _frame("b.py", lineno=2)]
    report = tokenize_trace(_trace(frames=frames))
    frame0_tokens = report.for_frame(0)
    assert all(t.frame_index == 0 for t in frame0_tokens)


def test_count_matches_total_tokens():
    frames = [_frame(), _frame()]
    report = tokenize_trace(_trace(frames=frames))
    assert report.count == len(report.tokens)


# ---------------------------------------------------------------------------
# _package_of
# ---------------------------------------------------------------------------

def test_package_of_simple_path():
    assert _package_of("myapp/utils.py") == "myapp"


def test_package_of_site_packages_skips_prefix():
    result = _package_of("/usr/lib/python3/site-packages/requests/models.py")
    assert result == "requests"


def test_package_of_empty_returns_unknown():
    assert _package_of("") == "<unknown>"


# ---------------------------------------------------------------------------
# tokenizer_cmd
# ---------------------------------------------------------------------------

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": None, "no_color": True, "kind": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


SAMPLE = """Traceback (most recent call last):
  File \"app.py\", line 5, in run
    result = 1 / 0
ZeroDivisionError: division by zero
"""


def test_build_subparser_registers_tokenize():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    _build_subparser(sub)
    ns = p.parse_args(["tokenize"])
    assert ns is not None


def test_tokenizer_command_returns_zero_on_valid_stdin():
    with patch("sys.stdin.read", return_value=SAMPLE):
        assert tokenizer_command(_args()) == 0


def test_tokenizer_command_returns_one_on_empty_stdin():
    with patch("sys.stdin.read", return_value=""):
        assert tokenizer_command(_args()) == 1


def test_tokenizer_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(SAMPLE)
    assert tokenizer_command(_args(file=str(f))) == 0


def test_tokenizer_command_returns_one_on_missing_file():
    assert tokenizer_command(_args(file="/no/such/file.txt")) == 1


def test_render_kind_filter_limits_output():
    report = tokenize_trace(_trace())
    output = _render(report, no_color=True, kind_filter="filename")
    assert "FILENAME" in output
    assert "FUNCTION_NAME" not in output
