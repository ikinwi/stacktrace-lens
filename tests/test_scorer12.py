"""Tests for stacktrace_lens.scorer12."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer12 import (
    ScoreReport12,
    ScoredFrame12,
    _exception_weight,
    _stdlib_penalty,
    score_frames12,
)


def _frame(filename="app/main.py", function="run", lineno=10):
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(exc_type="ValueError", exc_msg="bad value", frames=None):
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


def test_score_frames_returns_report():
    report = score_frames12(_trace())
    assert isinstance(report, ScoreReport12)


def test_report_frames_are_scored_frames():
    report = score_frames12(_trace())
    for sf in report.frames:
        assert isinstance(sf, ScoredFrame12)


def test_frame_count_matches_trace():
    t = _trace(frames=[_frame(), _frame(filename="app/utils.py")])
    report = score_frames12(t)
    assert len(report.frames) == 2


def test_exception_type_stored():
    report = score_frames12(_trace(exc_type="ImportError"))
    assert report.exception_type == "ImportError"


def test_exception_message_stored():
    report = score_frames12(_trace(exc_msg="no module"))
    assert report.exception_message == "no module"


def test_exception_weight_known():
    assert _exception_weight("ZeroDivisionError") == pytest.approx(1.2)


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("CustomError") == pytest.approx(1.0)


def test_exception_weight_substring_match():
    assert _exception_weight("ModuleNotFoundError") == pytest.approx(1.3)


def test_stdlib_penalty_applied():
    f = _frame(filename="/usr/lib/python3.11/os.py")
    assert _stdlib_penalty(f) == pytest.approx(0.5)


def test_stdlib_penalty_not_applied_for_user_code():
    f = _frame(filename="app/main.py")
    assert _stdlib_penalty(f) == pytest.approx(1.0)


def test_scores_are_positive():
    t = _trace(frames=[_frame(), _frame(filename="app/b.py", lineno=20)])
    report = score_frames12(t)
    for sf in report.frames:
        assert sf.score > 0


def test_top_frame_has_highest_score():
    t = _trace(frames=[_frame(lineno=1), _frame(filename="app/b.py", lineno=50)])
    report = score_frames12(t)
    top = report.top_frame
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_ranked_descending():
    t = _trace(frames=[_frame(), _frame(filename="app/b.py"), _frame(filename="app/c.py")])
    report = score_frames12(t)
    scores = [sf.score for sf in report.ranked()]
    assert scores == sorted(scores, reverse=True)


def test_top_frame_none_for_empty_trace():
    t = StackTrace(exception_type="Error", exception_message="", frames=[])
    report = score_frames12(t)
    assert report.top_frame is None


def test_scored_frame_str_contains_function():
    sf = ScoredFrame12(frame=_frame(function="my_func"), score=0.75)
    assert "my_func" in str(sf)


def test_scored_frame_str_contains_score():
    sf = ScoredFrame12(frame=_frame(), score=0.75)
    assert "0.750" in str(sf)
