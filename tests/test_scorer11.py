"""Tests for stacktrace_lens.scorer11."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer11 import (
    ScoreReport11,
    ScoredFrame11,
    _exception_weight,
    _line_proximity,
    score_frames11,
)


def _frame(filename="app/main.py", function="run", lineno=10):
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(exc_type="ValueError", exc_msg="bad value", frames=None):
    if frames is None:
        frames = [_frame(), _frame("app/helper.py", "helper", 20)]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


def test_score_frames_returns_report():
    assert isinstance(score_frames11(_trace()), ScoreReport11)


def test_report_frames_are_scored_frames():
    report = score_frames11(_trace())
    assert all(isinstance(f, ScoredFrame11) for f in report.frames)


def test_frame_count_matches_trace():
    t = _trace()
    report = score_frames11(t)
    assert len(report.frames) == len(t.frames)


def test_exception_type_stored():
    report = score_frames11(_trace(exc_type="RuntimeError"))
    assert report.exception_type == "RuntimeError"


def test_exception_message_stored():
    report = score_frames11(_trace(exc_msg="oops"))
    assert report.exception_message == "oops"


def test_scores_are_positive():
    report = score_frames11(_trace())
    assert all(sf.score > 0 for sf in report.frames)


def test_top_returns_highest_score():
    report = score_frames11(_trace())
    top = report.top
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_ranked_descending():
    report = score_frames11(_trace())
    scores = [sf.score for sf in report.ranked()]
    assert scores == sorted(scores, reverse=True)


def test_exception_weight_known():
    assert _exception_weight("ZeroDivisionError") == pytest.approx(1.4)


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("ObscureError") == pytest.approx(1.0)


def test_exception_weight_substring_match():
    assert _exception_weight("MyImportError") == pytest.approx(1.1)


def test_line_proximity_zero_when_no_line():
    assert _line_proximity(None, 100) == pytest.approx(0.0)


def test_line_proximity_zero_when_max_zero():
    assert _line_proximity(50, 0) == pytest.approx(0.0)


def test_line_proximity_full_at_max():
    assert _line_proximity(100, 100) == pytest.approx(1.0)


def test_scored_frame_str_contains_filename():
    sf = ScoredFrame11(frame=_frame(filename="myfile.py"), score=0.75)
    assert "myfile.py" in str(sf)


def test_scored_frame_str_contains_score():
    sf = ScoredFrame11(frame=_frame(), score=0.123)
    assert "0.123" in str(sf)


def test_empty_frames_returns_empty_report():
    t = _trace(frames=[])
    report = score_frames11(t)
    assert report.frames == []
    assert report.top is None


def test_single_frame_report():
    t = _trace(frames=[_frame()])
    report = score_frames11(t)
    assert len(report.frames) == 1
