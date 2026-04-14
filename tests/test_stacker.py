"""Tests for stacktrace_lens.stacker."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.stacker import (
    DepthBucket,
    StackProfile,
    build_stack_profile,
    format_profile,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*depths: int, exc: str = "ValueError") -> StackTrace:
    """Build a StackTrace whose frame list has *depth* entries."""
    frames = [_frame(f"f{i}.py", i + 1) for i in range(depths[0])]
    return StackTrace(exception_type=exc, exception_message="oops", frames=frames)


def _traces(*depths: int, exc: str = "ValueError") -> list:
    return [_trace(d, exc=exc) for d in depths]


# ---------------------------------------------------------------------------
# build_stack_profile
# ---------------------------------------------------------------------------

def test_build_profile_returns_stack_profile():
    result = build_stack_profile(_traces(3))
    assert isinstance(result, StackProfile)


def test_empty_traces_returns_zero_total():
    result = build_stack_profile([])
    assert result.total_traces == 0
    assert result.buckets == []
    assert result.min_depth is None
    assert result.max_depth is None
    assert result.avg_depth == 0.0


def test_total_traces_count():
    result = build_stack_profile(_traces(2, 3, 4))
    assert result.total_traces == 3


def test_min_depth():
    result = build_stack_profile(_traces(1, 3, 5))
    assert result.min_depth == 1


def test_max_depth():
    result = build_stack_profile(_traces(1, 3, 5))
    assert result.max_depth == 5


def test_avg_depth():
    result = build_stack_profile(_traces(2, 4))
    assert result.avg_depth == pytest.approx(3.0)


def test_buckets_are_sorted_by_depth():
    result = build_stack_profile(_traces(5, 2, 3))
    depths = [b.depth for b in result.buckets]
    assert depths == sorted(depths)


def test_identical_depths_merged_into_one_bucket():
    result = build_stack_profile(_traces(3, 3, 3))
    assert len(result.buckets) == 1
    assert result.buckets[0].count == 3


def test_distinct_depths_produce_separate_buckets():
    result = build_stack_profile(_traces(1, 2, 3))
    assert len(result.buckets) == 3


def test_bucket_stores_exception_types():
    traces = [
        _trace(2, exc="ValueError"),
        _trace(2, exc="TypeError"),
    ]
    result = build_stack_profile(traces)
    assert len(result.buckets) == 1
    assert "ValueError" in result.buckets[0].exception_types
    assert "TypeError" in result.buckets[0].exception_types


def test_deepest_bucket_returns_max_depth():
    result = build_stack_profile(_traces(1, 4, 2))
    assert result.deepest_bucket().depth == 4


def test_most_common_bucket_returns_highest_count():
    result = build_stack_profile(_traces(3, 3, 3, 1))
    assert result.most_common_bucket().depth == 3


def test_summary_line_no_traces():
    result = build_stack_profile([])
    assert "No traces" in result.summary_line()


def test_summary_line_contains_counts():
    result = build_stack_profile(_traces(2, 4))
    line = result.summary_line()
    assert "2" in line  # total traces


# ---------------------------------------------------------------------------
# format_profile
# ---------------------------------------------------------------------------

def test_format_profile_returns_string():
    result = build_stack_profile(_traces(2))
    assert isinstance(format_profile(result), str)


def test_format_profile_contains_depth():
    result = build_stack_profile(_traces(3))
    output = format_profile(result)
    assert "3" in output


def test_format_profile_colour_flag_does_not_crash():
    result = build_stack_profile(_traces(2, 4))
    output = format_profile(result, colour=True)
    assert isinstance(output, str)
