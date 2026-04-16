"""Tests for stacktrace_lens.windower."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.windower import WindowReport, WindowStats, build_windows


def _make_trace(exc_type: str = "ValueError", n_frames: int = 2) -> StackTrace:
    frames = [
        Frame(filename=f"app/mod{i}.py", lineno=i + 1, function=f"fn{i}")
        for i in range(n_frames)
    ]
    return StackTrace(
        exception_type=exc_type,
        exception_message="msg",
        frames=frames,
    )


def test_build_windows_returns_report():
    traces = [_make_trace() for _ in range(6)]
    report = build_windows(traces, window_size=3, step=1)
    assert isinstance(report, WindowReport)


def test_window_count_default_step():
    traces = [_make_trace() for _ in range(5)]
    report = build_windows(traces, window_size=3, step=1)
    assert report.count == 3


def test_window_count_with_step_2():
    traces = [_make_trace() for _ in range(6)]
    report = build_windows(traces, window_size=3, step=2)
    assert report.count == 3


def test_empty_traces_returns_empty_report():
    report = build_windows([], window_size=3, step=1)
    assert report.count == 0


def test_window_size_stored_on_report():
    report = build_windows([_make_trace()], window_size=4, step=2)
    assert report.window_size == 4
    assert report.step == 2


def test_window_stats_count_matches_chunk():
    traces = [_make_trace() for _ in range(3)]
    report = build_windows(traces, window_size=2, step=2)
    assert report.windows[0].count == 2


def test_window_stats_start_end_index():
    traces = [_make_trace() for _ in range(4)]
    report = build_windows(traces, window_size=2, step=2)
    assert report.windows[0].start_index == 0
    assert report.windows[0].end_index == 1
    assert report.windows[1].start_index == 2
    assert report.windows[1].end_index == 3


def test_most_common_exception():
    traces = [
        _make_trace("ValueError"),
        _make_trace("ValueError"),
        _make_trace("TypeError"),
    ]
    report = build_windows(traces, window_size=3, step=3)
    ws = report.windows[0]
    assert ws.most_common_exception() == "ValueError"


def test_unique_exceptions_count():
    traces = [
        _make_trace("ValueError"),
        _make_trace("TypeError"),
        _make_trace("ValueError"),
    ]
    report = build_windows(traces, window_size=3, step=3)
    assert report.windows[0].unique_exceptions == 2


def test_most_common_exception_none_when_empty():
    ws = WindowStats(start_index=0, end_index=0, traces=[], exception_types=[])
    assert ws.most_common_exception() is None


def test_window_stats_str_contains_count():
    traces = [_make_trace() for _ in range(2)]
    report = build_windows(traces, window_size=2, step=2)
    s = str(report.windows[0])
    assert "traces=2" in s


def test_summary_line_contains_window_size():
    report = build_windows([_make_trace()], window_size=5, step=1)
    assert "size=5" in report.summary_line()


def test_invalid_window_size_raises():
    with pytest.raises(ValueError):
        build_windows([], window_size=0)


def test_invalid_step_raises():
    with pytest.raises(ValueError):
        build_windows([], window_size=3, step=0)
