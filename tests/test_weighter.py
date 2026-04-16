"""Tests for stacktrace_lens.weighter."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.weighter import (
    WeightedFrame, WeightReport, weight_frames,
    _is_noise, _exception_multiplier, _position_weight,
)


def _frame(filename="app/main.py", function="run", lineno=10) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(frames=None, exc_type="ValueError", exc_msg="bad") -> StackTrace:
    return StackTrace(
        frames=frames or [_frame()],
        exception_type=exc_type,
        exception_message=exc_msg,
    )


def test_weight_frames_returns_report():
    report = weight_frames(_trace())
    assert isinstance(report, WeightReport)


def test_report_frames_are_weighted_frames():
    report = weight_frames(_trace(frames=[_frame(), _frame()]))
    for wf in report.frames:
        assert isinstance(wf, WeightedFrame)


def test_frame_count_matches_trace():
    frames = [_frame(), _frame(), _frame()]
    report = weight_frames(_trace(frames=frames))
    assert report.count == 3


def test_exception_type_stored():
    report = weight_frames(_trace(exc_type="KeyError"))
    assert report.exception_type == "KeyError"


def test_top_frame_is_highest_weight():
    frames = [_frame(lineno=1), _frame(lineno=2), _frame(lineno=3)]
    report = weight_frames(_trace(frames=frames))
    assert report.top_frame is not None
    assert report.top_frame.weight == max(wf.weight for wf in report.frames)


def test_innermost_frame_has_highest_position_weight():
    frames = [_frame(lineno=i) for i in range(5)]
    report = weight_frames(_trace(frames=frames))
    weights = [wf.weight for wf in report.frames]
    assert weights[-1] >= weights[0]


def test_noise_frame_gets_low_weight():
    noise = _frame(filename="/usr/lib/python3.11/site.py")
    user = _frame(filename="app/main.py")
    report = weight_frames(_trace(frames=[noise, user]))
    noise_w = report.frames[0].weight
    user_w = report.frames[1].weight
    assert noise_w < user_w


def test_known_exception_multiplier_above_one():
    assert _exception_multiplier("ValueError") > 1.0


def test_unknown_exception_multiplier_is_one():
    assert _exception_multiplier("FooBarError") == 1.0


def test_is_noise_true_for_stdlib():
    assert _is_noise(_frame(filename="/usr/lib/python3/dist.py"))


def test_is_noise_false_for_user_code():
    assert not _is_noise(_frame(filename="myapp/views.py"))


def test_position_weight_single_frame():
    assert _position_weight(0, 1) == 1.0


def test_weighted_frame_str_contains_filename():
    wf = WeightedFrame(frame=_frame(filename="app/main.py"), weight=0.75)
    assert "app/main.py" in str(wf)


def test_summary_line_no_frames():
    report = WeightReport(frames=[], exception_type="", top_frame=None)
    assert "No frames" in report.summary_line()


def test_summary_line_with_frames():
    report = weight_frames(_trace())
    line = report.summary_line()
    assert "Top frame" in line
