"""Tests for stacktrace_lens.scorer7."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer7 import (
    ScoreReport7,
    ScoredFrame7,
    _depth_penalty,
    _exception_weight,
    _origin_bonus,
    score_frames7,
)


def _frame(filename="app/main.py", function="run", lineno=10):
    return Frame(filename=filename, function=function, lineno=lineno, context=None)


def _trace(exc="ValueError", frames=None):
    frames = frames or [_frame()]
    return StackTrace(exception_type=exc, exception_message="oops", frames=frames)


# --- unit helpers ---

def test_exception_weight_known():
    assert _exception_weight("ZeroDivisionError") == pytest.approx(1.4)


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("MyCustomError") == pytest.approx(1.0)


def test_exception_weight_substring_match():
    assert _exception_weight("SomeImportError") == pytest.approx(1.1)


def test_depth_penalty_single_frame():
    assert _depth_penalty(0, 1) == pytest.approx(1.0)


def test_depth_penalty_last_frame_is_highest():
    assert _depth_penalty(4, 5) > _depth_penalty(0, 5)


def test_origin_bonus_user_code():
    assert _origin_bonus("app/main.py") == pytest.approx(1.0)


def test_origin_bonus_stdlib():
    assert _origin_bonus("/usr/lib/python3.11/foo.py") == pytest.approx(0.6)


def test_origin_bonus_site_packages():
    assert _origin_bonus("/home/user/.venv/lib/site-packages/pkg/mod.py") == pytest.approx(0.7)


def test_origin_bonus_none_filename():
    assert _origin_bonus(None) == pytest.approx(0.8)


# --- ScoreReport7 ---

def test_score_frames_returns_report():
    assert isinstance(score_frames7(_trace()), ScoreReport7)


def test_report_frames_are_scored_frames():
    report = score_frames7(_trace())
    assert all(isinstance(sf, ScoredFrame7) for sf in report.frames)


def test_frame_count_matches_trace():
    t = _trace(frames=[_frame(), _frame(function="helper"), _frame(function="inner")])
    assert score_frames7(t).count == 3


def test_scores_are_positive():
    report = score_frames7(_trace(frames=[_frame(), _frame(function="f2")]))
    assert all(sf.score > 0 for sf in report.frames)


def test_top_returns_highest_score():
    t = _trace(frames=[_frame(), _frame(function="inner")])
    report = score_frames7(t)
    top = report.top()
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_top_returns_none_for_empty_trace():
    empty = StackTrace(exception_type="E", exception_message="m", frames=[])
    report = score_frames7(empty)
    assert report.top() is None


def test_ranked_descending():
    t = _trace(frames=[_frame(), _frame(function="f2"), _frame(function="f3")])
    ranked = score_frames7(t).ranked()
    scores = [sf.score for sf in ranked]
    assert scores == sorted(scores, reverse=True)


def test_scored_frame_str_contains_function():
    sf = ScoredFrame7(frame=_frame(function="my_func"), score=0.95)
    assert "my_func" in str(sf)


def test_exception_type_stored_in_report():
    report = score_frames7(_trace(exc="KeyError"))
    assert report.exception_type == "KeyError"


def test_stdlib_frame_scores_lower_than_user_frame():
    user_f = _frame(filename="app/views.py", function="handle")
    stdlib_f = _frame(filename="/usr/lib/python3.11/threading.py", function="run")
    t = StackTrace(
        exception_type="RuntimeError",
        exception_message="bad",
        frames=[stdlib_f, user_f],
    )
    report = score_frames7(t)
    user_score = next(sf.score for sf in report.frames if sf.frame.function == "handle")
    stdlib_score = next(sf.score for sf in report.frames if sf.frame.function == "run")
    assert user_score > stdlib_score
