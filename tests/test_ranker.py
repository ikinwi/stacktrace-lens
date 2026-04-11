"""Tests for stacktrace_lens.ranker."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.ranker import (
    RankReport,
    RankedTrace,
    format_rank,
    rank_traces,
)


def _make_trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    n_frames: int = 3,
) -> StackTrace:
    frames = [
        Frame(filename=f"app/mod{i}.py", lineno=i * 10, function=f"func{i}")
        for i in range(n_frames)
    ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


def test_rank_traces_returns_report():
    report = rank_traces([_make_trace()])
    assert isinstance(report, RankReport)


def test_rank_traces_single_entry():
    report = rank_traces([_make_trace()])
    assert len(report.entries) == 1


def test_rank_traces_multiple_entries():
    traces = [_make_trace("ValueError"), _make_trace("ImportError")]
    report = rank_traces(traces)
    assert len(report.entries) == 2


def test_entries_are_ranked_traces():
    report = rank_traces([_make_trace()])
    assert isinstance(report.entries[0], RankedTrace)


def test_composite_is_between_zero_and_one():
    report = rank_traces([_make_trace()])
    for entry in report.entries:
        assert 0.0 <= entry.composite <= 1.0


def test_ranked_sorted_descending():
    traces = [
        _make_trace("ValueError", n_frames=2),
        _make_trace("RecursionError", n_frames=20),
    ]
    report = rank_traces(traces)
    ranked = report.ranked()
    assert ranked[0].composite >= ranked[1].composite


def test_top_returns_first_entry():
    traces = [_make_trace("ValueError"), _make_trace("ImportError")]
    report = rank_traces(traces)
    assert report.top is report.entries[0]


def test_top_returns_none_for_empty_report():
    assert RankReport().top is None


def test_recurrence_affects_score():
    t1 = _make_trace("ValueError")
    t2 = _make_trace("ValueError")
    rec = {"ValueError": 5}
    report = rank_traces([t1, t2], recurrence_counts=rec)
    for e in report.entries:
        assert e.recurrence_score == 1.0


def test_labels_assigned():
    traces = [_make_trace()]
    report = rank_traces(traces, labels=["my_label"])
    assert report.entries[0].label == "my_label"


def test_str_includes_exception_type():
    report = rank_traces([_make_trace("KeyError")])
    assert "KeyError" in str(report.entries[0])


def test_format_rank_returns_string():
    report = rank_traces([_make_trace()])
    out = format_rank(report)
    assert isinstance(out, str)


def test_format_rank_empty_report():
    assert "No traces" in format_rank(RankReport())


def test_format_rank_contains_exception_type():
    report = rank_traces([_make_trace("MemoryError")])
    assert "MemoryError" in format_rank(report)
