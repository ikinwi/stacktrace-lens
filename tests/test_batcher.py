"""Tests for stacktrace_lens.batcher."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.batcher import (
    BatchOptions,
    BatchEntry,
    BatchReport,
    batch_traces,
    format_batch,
)


def _frame(filename: str = "app.py", lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(exc_type: str = "ValueError", msg: str = "oops") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=msg,
        frames=[_frame()],
    )


# --- batch_traces ---

def test_batch_traces_returns_batch_report():
    report = batch_traces([_trace()])
    assert isinstance(report, BatchReport)


def test_batch_traces_count_matches_input():
    traces = [_trace(), _trace()]
    report = batch_traces(traces)
    assert report.count == 2


def test_batch_traces_respects_max_batch_size():
    traces = [_trace() for _ in range(10)]
    opts = BatchOptions(max_batch_size=3)
    report = batch_traces(traces, opts)
    assert report.count == 3


def test_batch_traces_default_group_key_is_default():
    report = batch_traces([_trace()])
    assert report.groups == ["default"]


def test_batch_traces_group_by_exception():
    traces = [_trace("ValueError"), _trace("KeyError"), _trace("ValueError")]
    opts = BatchOptions(group_by_exception=True)
    report = batch_traces(traces, opts)
    assert set(report.groups) == {"ValueError", "KeyError"}


def test_batch_traces_by_group_filters_correctly():
    traces = [_trace("ValueError"), _trace("KeyError")]
    opts = BatchOptions(group_by_exception=True)
    report = batch_traces(traces, opts)
    ve_entries = report.by_group("ValueError")
    assert len(ve_entries) == 1
    assert ve_entries[0].trace.exception_type == "ValueError"


def test_batch_entry_str_contains_exception_type():
    t = _trace("RuntimeError")
    entry = BatchEntry(index=0, trace=t, group_key="RuntimeError")
    assert "RuntimeError" in str(entry)


def test_batch_report_label_stored():
    opts = BatchOptions(label="my-batch")
    report = batch_traces([_trace()], opts)
    assert report.label == "my-batch"


def test_batch_report_summary_line_contains_label():
    opts = BatchOptions(label="release-1")
    report = batch_traces([_trace()], opts)
    assert "release-1" in report.summary_line()


def test_batch_report_summary_line_contains_counts():
    report = batch_traces([_trace(), _trace()])
    line = report.summary_line()
    assert "2" in line


# --- format_batch ---

def test_format_batch_returns_string():
    report = batch_traces([_trace()])
    assert isinstance(format_batch(report), str)


def test_format_batch_contains_group_key():
    opts = BatchOptions(group_by_exception=True)
    report = batch_traces([_trace("TypeError")], opts)
    output = format_batch(report)
    assert "TypeError" in output
