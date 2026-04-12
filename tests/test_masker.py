"""Tests for stacktrace_lens.masker."""
from __future__ import annotations

import argparse
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.masker import (
    MaskOptions,
    MaskedFrame,
    MaskReport,
    mask_trace,
)


def _frame(
    filename: str = "/app/views.py",
    lineno: int = 42,
    function: str = "handle_request",
    context: str | None = None,
) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=context)


def _trace(
    frames=None,
    exc_type: str = "ValueError",
    exc_msg: str = "bad input",
) -> StackTrace:
    return StackTrace(
        frames=frames or [_frame()],
        exception_type=exc_type,
        exception_message=exc_msg,
    )


# ---------------------------------------------------------------------------
# mask_trace return types
# ---------------------------------------------------------------------------

def test_mask_trace_returns_mask_report():
    report = mask_trace(_trace())
    assert isinstance(report, MaskReport)


def test_mask_report_frames_are_masked_frames():
    report = mask_trace(_trace())
    assert all(isinstance(f, MaskedFrame) for f in report.frames)


def test_mask_report_frame_count_matches_trace():
    t = _trace(frames=[_frame(), _frame(filename="/app/models.py")])
    report = mask_trace(t)
    assert report.count == 2


# ---------------------------------------------------------------------------
# No sensitive data – zero replacements
# ---------------------------------------------------------------------------

def test_no_sensitive_data_zero_replacements():
    report = mask_trace(_trace())
    assert report.total_replacements == 0


def test_no_sensitive_data_filename_unchanged():
    report = mask_trace(_trace())
    assert report.frames[0].masked_filename == "/app/views.py"


# ---------------------------------------------------------------------------
# Sensitive data in context
# ---------------------------------------------------------------------------

def test_password_in_context_is_masked():
    frame = _frame(context="    url = '/api/login?password=supersecret&next=/'")
    report = mask_trace(_trace(frames=[frame]))
    assert "supersecret" not in report.frames[0].masked_context
    assert "***" in report.frames[0].masked_context


def test_token_in_context_is_masked():
    frame = _frame(context="    headers = {'token=abc123'}")
    report = mask_trace(_trace(frames=[frame]))
    assert "abc123" not in report.frames[0].masked_context


def test_replacements_counted_correctly():
    frame = _frame(context="password=x token=y")
    report = mask_trace(_trace(frames=[frame]))
    assert report.total_replacements >= 2


# ---------------------------------------------------------------------------
# Custom placeholder
# ---------------------------------------------------------------------------

def test_custom_placeholder_used():
    frame = _frame(context="secret=myvalue")
    opts = MaskOptions(placeholder="<REDACTED>")
    report = mask_trace(_trace(frames=[frame]), opts)
    assert "<REDACTED>" in report.frames[0].masked_context


# ---------------------------------------------------------------------------
# mask_line_numbers option
# ---------------------------------------------------------------------------

def test_line_numbers_preserved_by_default():
    report = mask_trace(_trace())
    assert report.frames[0].masked_lineno == 42


def test_line_numbers_masked_when_option_set():
    opts = MaskOptions(mask_line_numbers=True)
    report = mask_trace(_trace(), opts)
    assert report.frames[0].masked_lineno is None


# ---------------------------------------------------------------------------
# Custom patterns
# ---------------------------------------------------------------------------

def test_custom_pattern_masks_value():
    frame = _frame(context="ssn=123-45-6789")
    opts = MaskOptions(patterns=[r'ssn=[\d-]+'])
    report = mask_trace(_trace(frames=[frame]), opts)
    assert "123-45-6789" not in report.frames[0].masked_context


def test_no_default_patterns_leaves_password_intact():
    frame = _frame(context="password=hunter2")
    opts = MaskOptions(patterns=[])  # empty patterns list
    report = mask_trace(_trace(frames=[frame]), opts)
    assert "hunter2" in report.frames[0].masked_context


# ---------------------------------------------------------------------------
# summary_line
# ---------------------------------------------------------------------------

def test_summary_line_contains_frame_count():
    report = mask_trace(_trace(frames=[_frame(), _frame()]))
    assert "2" in report.summary_line()


# ---------------------------------------------------------------------------
# masker_cmd integration
# ---------------------------------------------------------------------------

_SAMPLE_TRACE = """Traceback (most recent call last):
  File "/app/views.py", line 10, in handle
    do_stuff(token=abc)
ValueError: bad input
"""


def test_masker_command_returns_zero_on_valid_stdin():
    from stacktrace_lens.masker_cmd import masker_command

    ns = argparse.Namespace(
        file=None,
        placeholder="***",
        patterns=None,
        mask_line_numbers=False,
        no_default_patterns=False,
    )
    with patch("sys.stdin", StringIO(_SAMPLE_TRACE)):
        rc = masker_command(ns, out=StringIO(), err=StringIO())
    assert rc == 0


def test_masker_command_returns_one_on_empty_stdin():
    from stacktrace_lens.masker_cmd import masker_command

    ns = argparse.Namespace(
        file=None,
        placeholder="***",
        patterns=None,
        mask_line_numbers=False,
        no_default_patterns=False,
    )
    with patch("sys.stdin", StringIO("")):
        rc = masker_command(ns, out=StringIO(), err=StringIO())
    assert rc == 1


def test_masker_command_returns_one_on_missing_file():
    from stacktrace_lens.masker_cmd import masker_command

    ns = argparse.Namespace(
        file="/nonexistent/path/trace.txt",
        placeholder="***",
        patterns=None,
        mask_line_numbers=False,
        no_default_patterns=False,
    )
    rc = masker_command(ns, out=StringIO(), err=StringIO())
    assert rc == 1


def test_masker_command_output_contains_summary(tmp_path):
    from stacktrace_lens.masker_cmd import masker_command

    f = tmp_path / "trace.txt"
    f.write_text(_SAMPLE_TRACE)
    ns = argparse.Namespace(
        file=str(f),
        placeholder="***",
        patterns=None,
        mask_line_numbers=False,
        no_default_patterns=False,
    )
    out = StringIO()
    rc = masker_command(ns, out=out, err=StringIO())
    assert rc == 0
    assert "frame" in out.getvalue()
