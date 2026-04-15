"""Tests for stacktrace_lens.splitter4."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.splitter4 import DepthLayer, LayerReport, split_by_depth


def _frame(filename: str = "app.py", lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(n: int = 6, exc: str = "ValueError", msg: str = "bad") -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=[_frame(f"f{i}.py", i + 1, f"func{i}") for i in range(n)],
    )


def test_split_returns_layer_report():
    report = split_by_depth(_trace())
    assert isinstance(report, LayerReport)


def test_split_stores_exception_type():
    report = split_by_depth(_trace(exc="TypeError"))
    assert report.exception_type == "TypeError"


def test_split_stores_exception_message():
    report = split_by_depth(_trace(msg="oops"))
    assert report.exception_message == "oops"


def test_split_empty_trace_returns_no_layers():
    t = StackTrace(exception_type="E", exception_message="m", frames=[])
    report = split_by_depth(t)
    assert report.count == 0
    assert report.total_frames == 0


def test_split_default_bucket_size_is_five():
    report = split_by_depth(_trace(n=10))
    assert report.bucket_size == 5


def test_split_single_bucket_for_fewer_frames_than_bucket_size():
    report = split_by_depth(_trace(n=3), bucket_size=5)
    assert report.count == 1
    assert report.layers[0].bucket == "0-4"


def test_split_two_buckets_for_six_frames_with_bucket_size_five():
    report = split_by_depth(_trace(n=6), bucket_size=5)
    assert report.count == 2


def test_total_frames_matches_input():
    n = 11
    report = split_by_depth(_trace(n=n), bucket_size=4)
    assert report.total_frames == n


def test_bucket_labels_are_correct():
    report = split_by_depth(_trace(n=10), bucket_size=5)
    labels = [lay.bucket for lay in report.layers]
    assert labels == ["0-4", "5-9"]


def test_custom_bucket_size_respected():
    report = split_by_depth(_trace(n=9), bucket_size=3)
    assert report.count == 3
    for lay in report.layers:
        assert lay.count == 3


def test_depth_layer_count_property():
    layer = DepthLayer(bucket="0-4", frames=[_frame(), _frame()])
    assert layer.count == 2


def test_depth_layer_str_contains_bucket():
    layer = DepthLayer(bucket="5-9", frames=[_frame()])
    assert "5-9" in str(layer)


def test_summary_line_contains_exception_type():
    report = split_by_depth(_trace(exc="KeyError"))
    assert "KeyError" in report.summary_line()


def test_invalid_bucket_size_raises():
    with pytest.raises(ValueError):
        split_by_depth(_trace(), bucket_size=0)
