"""Tests for stacktrace_lens.trendline."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.timeline import TimestampedTrace
from stacktrace_lens.trendline import (
    TrendPoint,
    TrendReport,
    build_trendline,
    format_trendline,
)


def _make_trace(exc_type: str = "ValueError") -> StackTrace:
    frame = Frame(filename="app.py", lineno=10, function="run", source_line="x()")
    return StackTrace(
        exception_type=exc_type,
        exception_message="oops",
        frames=[frame],
        raw="",
    )


def _entry(ts_epoch: float, exc_type: str = "ValueError") -> TimestampedTrace:
    ts = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
    return TimestampedTrace(trace=_make_trace(exc_type), timestamp=ts)


def test_build_trendline_returns_report():
    entries = [_entry(0.0), _entry(10.0)]
    report = build_trendline(entries)
    assert isinstance(report, TrendReport)


def test_empty_entries_returns_empty_report():
    report = build_trendline([])
    assert report.total_traces == 0
    assert report.count == 0
    assert report.most_frequent_exception is None


def test_total_traces_count():
    entries = [_entry(0.0), _entry(60.0), _entry(120.0)]
    report = build_trendline(entries, bucket_size=60)
    assert report.total_traces == 3


def test_points_bucketed_correctly():
    entries = [_entry(0.0), _entry(30.0), _entry(60.0)]
    report = build_trendline(entries, bucket_size=60)
    assert report.count == 2  # bucket 0 and bucket 60


def test_same_bucket_merged():
    entries = [_entry(0.0), _entry(10.0), _entry(20.0)]
    report = build_trendline(entries, bucket_size=60)
    assert report.count == 1
    assert report.points[0].count == 3


def test_most_frequent_exception():
    entries = [
        _entry(0.0, "ValueError"),
        _entry(10.0, "ValueError"),
        _entry(20.0, "KeyError"),
    ]
    report = build_trendline(entries)
    assert report.most_frequent_exception == "ValueError"


def test_rising_trend_detected():
    # second half has more entries
    entries = [_entry(0.0)] + [_entry(float(120 + i * 5)) for i in range(5)]
    report = build_trendline(entries, bucket_size=60)
    assert report.rising is True


def test_falling_trend_not_rising():
    entries = [_entry(float(i * 5)) for i in range(5)] + [_entry(300.0)]
    report = build_trendline(entries, bucket_size=60)
    assert report.rising is False


def test_trend_point_str():
    tp = TrendPoint(label="0", count=3)
    assert "0" in str(tp)
    assert "3" in str(tp)


def test_summary_line_contains_total():
    entries = [_entry(0.0)]
    report = build_trendline(entries)
    assert "1" in report.summary_line()


def test_format_trendline_returns_string():
    entries = [_entry(0.0), _entry(60.0)]
    report = build_trendline(entries, bucket_size=60)
    result = format_trendline(report)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_trendline_contains_bucket_labels():
    entries = [_entry(0.0)]
    report = build_trendline(entries, bucket_size=60)
    result = format_trendline(report)
    assert "0" in result
