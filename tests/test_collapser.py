"""Tests for stacktrace_lens.collapser."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.collapser import (
    CollapseOptions,
    CollapseReport,
    CollapsedFrame,
    collapse_frames,
)


def _frame(filename: str, lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="oops",
        frames=list(frames),
    )


_USER = "/home/user/project/app.py"
_STDLIB = "/usr/lib/python3.11/threading.py"
_STDLIB2 = "/usr/lib/python3.11/queue.py"
_THIRD = "/home/user/.venv/lib/python3.11/site-packages/requests/adapters.py"
_THIRD2 = "/home/user/.venv/lib/python3.11/site-packages/urllib3/pool.py"


def test_collapse_returns_collapse_report():
    trace = _trace(_frame(_USER))
    result = collapse_frames(trace)
    assert isinstance(result, CollapseReport)


def test_original_count_matches_trace():
    trace = _trace(_frame(_USER), _frame(_STDLIB))
    report = collapse_frames(trace)
    assert report.original_count == 2


def test_no_stdlib_frames_kept_as_is():
    trace = _trace(_frame(_USER), _frame(_USER))
    report = collapse_frames(trace)
    assert report.collapsed_count == 0
    assert all(not cf.is_collapsed for cf in report.frames)


def test_single_stdlib_frame_not_collapsed_below_min_run():
    trace = _trace(_frame(_USER), _frame(_STDLIB), _frame(_USER))
    opts = CollapseOptions(collapse_stdlib=True, min_run=2)
    report = collapse_frames(trace, opts)
    # Only 1 stdlib frame – below min_run=2, should NOT be collapsed
    assert report.collapsed_count == 0


def test_two_consecutive_stdlib_frames_collapsed():
    trace = _trace(_frame(_USER), _frame(_STDLIB), _frame(_STDLIB2), _frame(_USER))
    opts = CollapseOptions(collapse_stdlib=True, min_run=2)
    report = collapse_frames(trace, opts)
    assert report.collapsed_count == 2


def test_collapsed_frame_is_collapsed_true():
    trace = _trace(_frame(_STDLIB), _frame(_STDLIB2))
    report = collapse_frames(trace)
    collapsed = [cf for cf in report.frames if cf.is_collapsed]
    assert len(collapsed) == 1
    assert collapsed[0].collapsed_count == 2


def test_collapsed_frame_label_stdlib():
    trace = _trace(_frame(_STDLIB), _frame(_STDLIB2))
    report = collapse_frames(trace)
    collapsed = [cf for cf in report.frames if cf.is_collapsed]
    assert collapsed[0].label == "stdlib"


def test_third_party_not_collapsed_by_default():
    trace = _trace(_frame(_THIRD), _frame(_THIRD2))
    opts = CollapseOptions(collapse_stdlib=True, collapse_third_party=False)
    report = collapse_frames(trace, opts)
    assert report.collapsed_count == 0


def test_third_party_collapsed_when_enabled():
    trace = _trace(_frame(_THIRD), _frame(_THIRD2))
    opts = CollapseOptions(collapse_stdlib=False, collapse_third_party=True, min_run=2)
    report = collapse_frames(trace, opts)
    assert report.collapsed_count == 2


def test_kept_count_property():
    trace = _trace(_frame(_USER), _frame(_STDLIB), _frame(_STDLIB2))
    report = collapse_frames(trace)
    assert report.kept_count == report.original_count - report.collapsed_count


def test_summary_line_returns_string():
    trace = _trace(_frame(_USER), _frame(_STDLIB), _frame(_STDLIB2))
    report = collapse_frames(trace)
    assert isinstance(report.summary_line(), str)


def test_collapsed_frame_str_contains_count():
    cf = CollapsedFrame(frame=None, collapsed_count=3, label="stdlib")
    assert "3" in str(cf)
    assert "stdlib" in str(cf)


def test_user_frame_str_contains_filename():
    f = _frame(_USER, lineno=42, function="my_func")
    cf = CollapsedFrame(frame=f)
    assert "app.py" in str(cf)
    assert "42" in str(cf)
