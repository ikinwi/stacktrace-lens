"""Tests for stacktrace_lens.scorer4."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer4 import (
    ScoreReport4,
    ScoredFrame4,
    score_frames4,
    _exception_weight,
    _position_score,
)


def _frame(filename="app.py", lineno=10, function="do_thing"):
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(frames=None, exc_type="ValueError", exc_msg="bad value"):
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=frames or [_frame()],
    )


def test_score_frames_returns_report():
    report = score_frames4(_trace())
    assert isinstance(report, ScoreReport4)


def test_report_frames_are_scored_frames():
    report = score_frames4(_trace())
    for sf in report.frames:
        assert isinstance(sf, ScoredFrame4)


def test_frame_count_matches_trace():
    t = _trace(frames=[_frame(), _frame(filename="b.py")])
    report = score_frames4(t)
    assert report.count == 2


def test_exception_weight_stored():
    report = score_frames4(_trace(exc_type="RuntimeError"))
    assert report.exception_weight == pytest.approx(1.5)


def test_unknown_exception_weight_defaults_to_one():
    report = score_frames4(_trace(exc_type="WeirdError"))
    assert report.exception_weight == pytest.approx(1.0)


def test_scores_are_positive():
    t = _trace(frames=[_frame(lineno=5), _frame(lineno=100)])
    report = score_frames4(t)
    for sf in report.frames:
        assert sf.score > 0


def test_top_returns_highest_scored():
    t = _trace(frames=[_frame(lineno=1), _frame(lineno=500)])
    report = score_frames4(t)
    top = report.top()
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_ranked_is_descending():
    t = _trace(frames=[_frame(lineno=i) for i in range(1, 6)])
    report = score_frames4(t)
    ranked = report.ranked()
    scores = [sf.score for sf in ranked]
    assert scores == sorted(scores, reverse=True)


def test_top_returns_none_for_empty_trace():
    t = StackTrace(exception_type="E", exception_message="", frames=[])
    report = score_frames4(t)
    assert report.top() is None


def test_scored_frame_str_contains_function():
    sf = ScoredFrame4(frame=_frame(function="my_func"), score=0.75)
    assert "my_func" in str(sf)


def test_exception_weight_import_error():
    assert _exception_weight("ImportError") == pytest.approx(0.9)


def test_position_score_single_frame():
    assert _position_score(0, 1) == pytest.approx(1.0)


def test_position_score_last_frame_lower():
    assert _position_score(4, 5) < _position_score(0, 5)
