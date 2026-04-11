"""Tests for stacktrace_lens.heatmap."""
from __future__ import annotations

import pytest

from stacktrace_lens.heatmap import (
    HeatmapEntry,
    HeatmapReport,
    build_heatmap,
    format_heatmap,
)
from stacktrace_lens.parser import Frame, StackTrace


def _frame(filename: str, function: str, lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line=None)


def _trace(*frames: Frame, exc: str = "ValueError", msg: str = "oops") -> StackTrace:
    return StackTrace(exception_type=exc, message=msg, frames=list(frames))


# ── build_heatmap ────────────────────────────────────────────────────────────

def test_build_heatmap_returns_report():
    t = _trace(_frame("a.py", "foo"))
    report = build_heatmap([t])
    assert isinstance(report, HeatmapReport)


def test_total_frames_single_trace():
    t = _trace(_frame("a.py", "foo"), _frame("b.py", "bar"))
    assert build_heatmap([t]).total_frames == 2


def test_total_frames_multiple_traces():
    t1 = _trace(_frame("a.py", "foo"))
    t2 = _trace(_frame("b.py", "bar"), _frame("c.py", "baz"))
    assert build_heatmap([t1, t2]).total_frames == 3


def test_empty_traces_gives_zero_total():
    assert build_heatmap([]).total_frames == 0


def test_by_file_sorted_by_count():
    t = _trace(
        _frame("a.py", "f"),
        _frame("a.py", "g"),
        _frame("b.py", "h"),
    )
    report = build_heatmap([t])
    assert report.by_file[0].label == "a.py"
    assert report.by_file[0].count == 2


def test_by_function_sorted_by_count():
    t = _trace(
        _frame("a.py", "foo"),
        _frame("b.py", "foo"),
        _frame("c.py", "bar"),
    )
    report = build_heatmap([t])
    assert report.by_function[0].label == "foo"
    assert report.by_function[0].count == 2


def test_percentage_sums_to_100_for_unique_files():
    t = _trace(_frame("a.py", "f"), _frame("b.py", "g"))
    report = build_heatmap([t])
    total_pct = sum(e.percentage for e in report.by_file)
    assert abs(total_pct - 100.0) < 0.01


def test_entry_percentage_zero_when_no_frames():
    # edge: empty trace list
    report = build_heatmap([])
    assert report.by_file == []
    assert report.by_function == []


# ── format_heatmap ───────────────────────────────────────────────────────────

def test_format_heatmap_returns_string():
    t = _trace(_frame("a.py", "foo"))
    out = format_heatmap(build_heatmap([t]))
    assert isinstance(out, str)


def test_format_heatmap_contains_file_label():
    t = _trace(_frame("mymodule.py", "run"))
    out = format_heatmap(build_heatmap([t]))
    assert "mymodule.py" in out


def test_format_heatmap_contains_function_label():
    t = _trace(_frame("x.py", "my_function"))
    out = format_heatmap(build_heatmap([t]))
    assert "my_function" in out


def test_format_heatmap_top_n_limits_output():
    frames = [_frame(f"file{i}.py", f"fn{i}") for i in range(20)]
    t = _trace(*frames)
    out = format_heatmap(build_heatmap([t]), top_n=3)
    # Only 3 file entries should appear
    file_lines = [l for l in out.splitlines() if ".py" in l and "──" not in l]
    assert len(file_lines) == 3


def test_format_heatmap_no_data_message_on_empty():
    out = format_heatmap(build_heatmap([]))
    assert "(no data)" in out
