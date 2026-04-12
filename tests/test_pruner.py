"""Tests for stacktrace_lens.pruner."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.pruner import (
    PruneOptions,
    PruneReport,
    prune_trace,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# --- basic return type ---

def test_prune_returns_report():
    t = _trace(_frame())
    assert isinstance(prune_trace(t), PruneReport)


def test_report_trace_is_stack_trace():
    t = _trace(_frame())
    report = prune_trace(t)
    assert isinstance(report.trace, StackTrace)


def test_original_count_matches_input():
    t = _trace(_frame(), _frame(), _frame())
    report = prune_trace(t)
    assert report.original_count == 3


def test_no_options_keeps_all_frames():
    t = _trace(_frame(), _frame(), _frame())
    report = prune_trace(t)
    assert report.pruned_count == 3
    assert report.removed_count == 0


# --- max_frames ---

def test_max_frames_limits_output():
    t = _trace(_frame(), _frame(), _frame(), _frame())
    report = prune_trace(t, PruneOptions(max_frames=2))
    assert report.pruned_count == 2
    assert report.removed_count == 2


def test_max_frames_larger_than_total_keeps_all():
    t = _trace(_frame(), _frame())
    report = prune_trace(t, PruneOptions(max_frames=10))
    assert report.pruned_count == 2


# --- drop_patterns ---

def test_drop_pattern_removes_matching_frames():
    frames = [
        _frame(filename="app.py"),
        _frame(filename="/usr/lib/python3/site.py"),
        _frame(filename="app.py"),
    ]
    t = _trace(*frames)
    report = prune_trace(t, PruneOptions(drop_patterns=[r"site\.py"]))
    assert report.pruned_count == 2
    assert all("site" not in f.filename for f in report.trace.frames)


def test_drop_pattern_matches_function():
    frames = [
        _frame(function="bootstrap"),
        _frame(function="main"),
    ]
    t = _trace(*frames)
    report = prune_trace(t, PruneOptions(drop_patterns=["bootstrap"]))
    assert report.pruned_count == 1
    assert report.trace.frames[0].function == "main"


# --- keep_first / keep_last ---

def test_keep_first_preserves_head():
    frames = [_frame(filename=f"{i}.py") for i in range(5)]
    t = _trace(*frames)
    report = prune_trace(t, PruneOptions(keep_first=2, max_frames=2))
    assert report.trace.frames[0].filename == "0.py"
    assert report.trace.frames[1].filename == "1.py"


def test_keep_last_preserves_tail():
    frames = [_frame(filename=f"{i}.py") for i in range(5)]
    t = _trace(*frames)
    report = prune_trace(t, PruneOptions(keep_last=2, max_frames=2))
    assert report.trace.frames[-1].filename == "4.py"
    assert report.trace.frames[-2].filename == "3.py"


# --- summary_line ---

def test_summary_line_format():
    t = _trace(_frame(), _frame(), _frame())
    report = prune_trace(t, PruneOptions(max_frames=1))
    line = report.summary_line()
    assert "3" in line
    assert "1" in line
