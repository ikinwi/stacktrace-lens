"""Tests for stacktrace_lens.sampler."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.sampler import (
    SampleOptions,
    SampleReport,
    format_sample,
    sample_traces,
)


def _frame(filename: str = "app.py", lineno: int = 1, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, line="pass")


def _trace(exc: str = "ValueError", msg: str = "bad", n: int = 2) -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=[_frame(f"f{i}.py", i) for i in range(n)],
    )


def test_sample_returns_sample_report():
    report = sample_traces([_trace()])
    assert isinstance(report, SampleReport)


def test_empty_traces_returns_zero_total():
    report = sample_traces([])
    assert report.original_count == 0
    assert report.count == 0


def test_no_options_keeps_all_traces():
    traces = [_trace() for _ in range(5)]
    report = sample_traces(traces)
    assert report.count == 5


def test_n_limits_count():
    traces = [_trace() for _ in range(10)]
    report = sample_traces(traces, SampleOptions(n=3, seed=0))
    assert report.count == 3


def test_n_larger_than_pool_returns_all():
    traces = [_trace() for _ in range(4)]
    report = sample_traces(traces, SampleOptions(n=100, seed=0))
    assert report.count == 4


def test_fraction_returns_approximate_count():
    traces = [_trace() for _ in range(10)]
    report = sample_traces(traces, SampleOptions(fraction=0.5, seed=42))
    assert 1 <= report.count <= 10


def test_fraction_clamped_to_one():
    traces = [_trace() for _ in range(5)]
    report = sample_traces(traces, SampleOptions(fraction=2.0, seed=0))
    assert report.count == 5


def test_fraction_clamped_to_zero_returns_at_least_one():
    traces = [_trace() for _ in range(5)]
    report = sample_traces(traces, SampleOptions(fraction=0.0, seed=0))
    assert report.count >= 1


def test_every_nth_keeps_correct_indices():
    traces = [_trace(exc=f"E{i}") for i in range(6)]
    report = sample_traces(traces, SampleOptions(every_nth=2))
    # 1-based: indices 2, 4, 6 → traces[1], traces[3], traces[5]
    assert report.count == 3
    assert report.sampled[0].exception_type == "E1"


def test_every_nth_one_keeps_all():
    traces = [_trace() for _ in range(4)]
    report = sample_traces(traces, SampleOptions(every_nth=1))
    assert report.count == 4


def test_seed_produces_deterministic_results():
    traces = [_trace(exc=f"E{i}") for i in range(20)]
    r1 = sample_traces(traces, SampleOptions(n=5, seed=7))
    r2 = sample_traces(traces, SampleOptions(n=5, seed=7))
    assert [t.exception_type for t in r1.sampled] == [t.exception_type for t in r2.sampled]


def test_original_count_always_reflects_input():
    traces = [_trace() for _ in range(8)]
    report = sample_traces(traces, SampleOptions(n=3, seed=0))
    assert report.original_count == 8


def test_summary_line_contains_counts():
    traces = [_trace() for _ in range(10)]
    report = sample_traces(traces, SampleOptions(n=4, seed=0))
    line = report.summary_line()
    assert "4" in line
    assert "10" in line


def test_format_sample_returns_string():
    traces = [_trace()]
    report = sample_traces(traces)
    out = format_sample(report)
    assert isinstance(out, str)
    assert "ValueError" in out
