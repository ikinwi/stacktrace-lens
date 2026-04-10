"""Tests for stacktrace_lens.profiler."""

from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.profiler import (
    Hotspot,
    ProfileReport,
    format_profile,
    profile_traces,
)


def _frame(filename: str, function: str, lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        frames=list(frames),
        exception_type="ValueError",
        message="oops",
    )


# ---------------------------------------------------------------------------
# profile_traces
# ---------------------------------------------------------------------------

def test_profile_traces_returns_profile_report():
    report = profile_traces([])
    assert isinstance(report, ProfileReport)


def test_total_traces_count():
    t1 = _trace(_frame("a.py", "foo"))
    t2 = _trace(_frame("b.py", "bar"))
    report = profile_traces([t1, t2])
    assert report.total_traces == 2


def test_total_frames_count():
    t = _trace(_frame("a.py", "foo"), _frame("b.py", "bar"))
    report = profile_traces([t])
    assert report.total_frames == 2


def test_hotspots_are_sorted_by_hit_count():
    t1 = _trace(_frame("a.py", "foo"), _frame("a.py", "foo"))
    t2 = _trace(_frame("b.py", "bar"))
    report = profile_traces([t1, t2])
    assert report.hotspots[0].hit_count >= report.hotspots[-1].hit_count


def test_most_common_frame_is_first_hotspot():
    t = _trace(_frame("hot.py", "run"), _frame("hot.py", "run"), _frame("cold.py", "idle"))
    report = profile_traces([t])
    assert report.hotspots[0].filename == "hot.py"
    assert report.hotspots[0].function == "run"
    assert report.hotspots[0].hit_count == 2


def test_top_n_limits_hotspots():
    frames = [_frame(f"f{i}.py", f"fn{i}") for i in range(20)]
    report = profile_traces([_trace(*frames)], top_n=5)
    assert len(report.hotspots) <= 5


def test_empty_traces_produces_empty_hotspots():
    report = profile_traces([])
    assert report.hotspots == []
    assert report.total_frames == 0


def test_hotspot_str_contains_filename_and_function():
    hs = Hotspot(filename="app.py", function="main", hit_count=3)
    s = str(hs)
    assert "app.py" in s
    assert "main" in s
    assert "3" in s


# ---------------------------------------------------------------------------
# format_profile
# ---------------------------------------------------------------------------

def test_format_profile_returns_string():
    report = profile_traces([_trace(_frame("a.py", "go"))])
    out = format_profile(report)
    assert isinstance(out, str)


def test_format_profile_contains_filename():
    t = _trace(_frame("mymodule.py", "process"))
    report = profile_traces([t])
    out = format_profile(report, colour=False)
    assert "mymodule.py" in out


def test_format_profile_no_colour_has_no_ansi():
    t = _trace(_frame("x.py", "y"))
    report = profile_traces([t])
    out = format_profile(report, colour=False)
    assert "\033[" not in out
