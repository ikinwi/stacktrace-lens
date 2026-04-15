"""Tests for stacktrace_lens.scaler."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scaler import ScaleReport, ScaledFrame, scale_traces


# ------------------------------------------------------------------ helpers

def _frame(filename: str = "app.py", lineno: int = 10,
           function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(*filenames: str) -> StackTrace:
    frames = [_frame(filename=f, lineno=i + 1) for i, f in enumerate(filenames)]
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=frames,
    )


# ------------------------------------------------------------------ tests

def test_scale_returns_scale_report():
    report = scale_traces([_trace("a.py", "b.py")])
    assert isinstance(report, ScaleReport)


def test_empty_traces_returns_zero_max_depth():
    report = scale_traces([])
    assert report.max_depth == 0
    assert report.total_frames == 0
    assert report.trace_count == 0


def test_single_trace_single_frame_scaled_depth_is_zero():
    report = scale_traces([_trace("only.py")])
    assert report.scaled[0][0].scaled_depth == 0.0


def test_max_depth_equals_longest_trace():
    t1 = _trace("a.py", "b.py")
    t2 = _trace("x.py", "y.py", "z.py")
    report = scale_traces([t1, t2])
    assert report.max_depth == 3


def test_last_frame_of_deepest_trace_has_scaled_depth_one():
    t = _trace("a.py", "b.py", "c.py")
    report = scale_traces([t])
    assert report.scaled[0][-1].scaled_depth == pytest.approx(1.0)


def test_first_frame_scaled_depth_is_zero():
    t = _trace("a.py", "b.py", "c.py")
    report = scale_traces([t])
    assert report.scaled[0][0].scaled_depth == pytest.approx(0.0)


def test_middle_frame_scaled_depth_is_half():
    t = _trace("a.py", "b.py", "c.py")
    report = scale_traces([t])
    assert report.scaled[0][1].scaled_depth == pytest.approx(0.5)


def test_total_frames_counts_all():
    t1 = _trace("a.py", "b.py")
    t2 = _trace("x.py")
    report = scale_traces([t1, t2])
    assert report.total_frames == 3


def test_trace_count_matches_input():
    traces = [_trace("a.py"), _trace("b.py"), _trace("c.py")]
    report = scale_traces(traces)
    assert report.trace_count == 3


def test_flat_returns_all_scaled_frames():
    t1 = _trace("a.py", "b.py")
    t2 = _trace("x.py")
    report = scale_traces([t1, t2])
    flat = report.flat()
    assert len(flat) == 3
    assert all(isinstance(sf, ScaledFrame) for sf in flat)


def test_summary_line_contains_max_depth():
    report = scale_traces([_trace("a.py", "b.py")])
    assert "max_depth=2" in report.summary_line()


def test_shorter_trace_scaled_against_global_max():
    t_short = _trace("a.py")          # 1 frame
    t_long = _trace("x.py", "y.py", "z.py", "w.py")  # 4 frames
    report = scale_traces([t_short, t_long])
    # short trace: only frame is at index 0, max_depth=4 -> 0/(4-1) = 0.0
    assert report.scaled[0][0].scaled_depth == pytest.approx(0.0)
    # long trace: last frame index 3 -> 3/3 = 1.0
    assert report.scaled[1][-1].scaled_depth == pytest.approx(1.0)


def test_scaled_frame_stores_original_frame():
    t = _trace("app.py")
    report = scale_traces([t])
    sf = report.scaled[0][0]
    assert sf.frame is t.frames[0]
