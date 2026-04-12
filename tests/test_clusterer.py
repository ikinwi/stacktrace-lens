"""Tests for stacktrace_lens.clusterer."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.clusterer import (
    ClusterEntry,
    ClusterReport,
    cluster_traces,
    format_cluster_report,
)


def _frame(filename: str = "app.py", lineno: int = 10, name: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, line="pass")


def _trace(exc: str = "ValueError", msg: str = "bad value", frames=None) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc, exception_message=msg, frames=frames)


# ---------------------------------------------------------------------------
# cluster_traces
# ---------------------------------------------------------------------------

def test_cluster_traces_returns_report():
    report = cluster_traces([_trace()])
    assert isinstance(report, ClusterReport)


def test_single_trace_produces_one_cluster():
    report = cluster_traces([_trace()])
    assert report.total_clusters == 1
    assert report.total_traces == 1


def test_identical_traces_merged_into_one_cluster():
    t = _trace()
    report = cluster_traces([t, t])
    assert report.total_clusters == 1
    assert report.total_traces == 2


def test_different_exceptions_produce_separate_clusters():
    t1 = _trace(exc="ValueError")
    t2 = _trace(exc="KeyError")
    report = cluster_traces([t1, t2])
    assert report.total_clusters == 2


def test_empty_input_produces_empty_report():
    report = cluster_traces([])
    assert report.total_clusters == 0
    assert report.total_traces == 0


def test_largest_returns_most_common_cluster():
    t = _trace(exc="ValueError")
    t2 = _trace(exc="KeyError")
    report = cluster_traces([t, t, t2])
    largest = report.largest()
    assert largest is not None
    assert largest.count == 2


def test_largest_returns_none_for_empty_report():
    report = cluster_traces([])
    assert report.largest() is None


def test_ranked_orders_by_count_descending():
    t1 = _trace(exc="ValueError")
    t2 = _trace(exc="KeyError")
    report = cluster_traces([t1, t1, t1, t2, t2])
    ranked = report.ranked()
    assert ranked[0].count >= ranked[1].count


def test_representative_is_first_trace():
    t = _trace(exc="RuntimeError")
    report = cluster_traces([t])
    entry = report.clusters[0]
    assert entry.representative is t


# ---------------------------------------------------------------------------
# format_cluster_report
# ---------------------------------------------------------------------------

def test_format_returns_string():
    report = cluster_traces([_trace()])
    out = format_cluster_report(report)
    assert isinstance(out, str)


def test_format_contains_exception_type():
    report = cluster_traces([_trace(exc="TypeError")])
    out = format_cluster_report(report, colour=False)
    assert "TypeError" in out


def test_format_no_colour_has_no_escape_codes():
    report = cluster_traces([_trace()])
    out = format_cluster_report(report, colour=False)
    assert "\033[" not in out


def test_format_contains_total_traces():
    report = cluster_traces([_trace(), _trace()])
    out = format_cluster_report(report, colour=False)
    assert "2" in out
