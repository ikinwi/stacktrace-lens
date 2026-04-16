"""Tests for stacktrace_lens.fuser."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.fuser import (
    FusedFrame,
    FuseReport,
    fuse_traces,
    _frame_key,
)


def _frame(filename="app.py", lineno=10, function="main") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(*frames, exc="ValueError", msg="oops") -> StackTrace:
    return StackTrace(exception_type=exc, exception_message=msg, frames=list(frames))


def test_fuse_returns_fuse_report():
    t = _trace(_frame())
    report = fuse_traces(t, t)
    assert isinstance(report, FuseReport)


def test_fuse_identical_traces_all_shared():
    f = _frame()
    t = _trace(f)
    report = fuse_traces(t, t)
    assert report.shared_count == 1
    assert report.left_only_count == 0
    assert report.right_only_count == 0


def test_fuse_disjoint_traces():
    left = _trace(_frame("a.py", 1, "foo"))
    right = _trace(_frame("b.py", 2, "bar"))
    report = fuse_traces(left, right)
    assert report.left_only_count == 1
    assert report.right_only_count == 1
    assert report.shared_count == 0


def test_fuse_partial_overlap():
    shared = _frame("shared.py", 5, "common")
    left = _trace(shared, _frame("only_left.py", 1, "l"))
    right = _trace(shared, _frame("only_right.py", 2, "r"))
    report = fuse_traces(left, right)
    assert report.shared_count == 1
    assert report.left_only_count == 1
    assert report.right_only_count == 1


def test_fuse_count_equals_total_frames():
    left = _trace(_frame("a.py", 1, "x"), _frame("b.py", 2, "y"))
    right = _trace(_frame("b.py", 2, "y"), _frame("c.py", 3, "z"))
    report = fuse_traces(left, right)
    assert report.count == report.shared_count + report.left_only_count + report.right_only_count


def test_fuse_stores_exception_types():
    left = _trace(_frame(), exc="TypeError")
    right = _trace(_frame(), exc="ValueError")
    report = fuse_traces(left, right)
    assert report.left_exception == "TypeError"
    assert report.right_exception == "ValueError"


def test_fused_frame_str_shared():
    ff = FusedFrame(frame=_frame("app.py", 10, "main"), source="both")
    assert "[=]" in str(ff)
    assert "app.py" in str(ff)


def test_fused_frame_str_left():
    ff = FusedFrame(frame=_frame(), source="left")
    assert "[<]" in str(ff)


def test_fused_frame_str_right():
    ff = FusedFrame(frame=_frame(), source="right")
    assert "[>]" in str(ff)


def test_summary_line_contains_counts():
    left = _trace(_frame("a.py", 1, "f"))
    right = _trace(_frame("b.py", 2, "g"))
    report = fuse_traces(left, right)
    summary = report.summary_line()
    assert "shared" in summary
    assert "left-only" in summary
    assert "right-only" in summary


def test_frame_key_unique_per_location():
    f1 = _frame("x.py", 1, "a")
    f2 = _frame("x.py", 2, "a")
    assert _frame_key(f1) != _frame_key(f2)
