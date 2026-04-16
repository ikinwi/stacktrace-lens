"""Tests for stacktrace_lens.scorer9."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer9 import (
    ScoreReport9,
    ScoredFrame9,
    _exception_weight,
    _package_depth,
    _recency_score,
    _uniqueness_bonus,
    score_frames9,
)


def _frame(filename: str = "app/main.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno, context=None)


def _trace(
    frames=None,
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(frames=frames, exception_type=exc_type, exception_message=exc_msg)


# --- unit helpers ---

def test_exception_weight_known():
    assert _exception_weight("RuntimeError") == pytest.approx(1.5)


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("FooError") == pytest.approx(1.0)


def test_exception_weight_substring_match():
    assert _exception_weight("ModuleNotFoundError") == pytest.approx(1.4)


def test_package_depth_simple():
    assert _package_depth("app/main.py") == 2


def test_package_depth_deep():
    assert _package_depth("a/b/c/d/e.py") == 5


def test_package_depth_empty():
    assert _package_depth("") == 0


def test_recency_score_first_frame_highest():
    assert _recency_score(0, 5) > _recency_score(4, 5)


def test_recency_score_single_frame():
    assert _recency_score(0, 1) == pytest.approx(1.0)


def test_uniqueness_bonus_unique_function():
    frames = [_frame(function="run"), _frame(function="start")]
    assert _uniqueness_bonus(frames[0], frames) == pytest.approx(0.5)


def test_uniqueness_bonus_repeated_function():
    frames = [_frame(function="run"), _frame(function="run")]
    assert _uniqueness_bonus(frames[0], frames) == pytest.approx(0.0)


# --- score_frames9 ---

def test_score_frames_returns_report():
    report = score_frames9(_trace())
    assert isinstance(report, ScoreReport9)


def test_report_frames_are_scored_frames():
    report = score_frames9(_trace(frames=[_frame(), _frame(function="helper")]))
    assert all(isinstance(f, ScoredFrame9) for f in report.frames)


def test_frame_count_matches_trace():
    frames = [_frame(), _frame(function="a"), _frame(function="b")]
    report = score_frames9(_trace(frames=frames))
    assert len(report.frames) == 3


def test_scores_are_positive():
    report = score_frames9(_trace(frames=[_frame(), _frame(function="helper")]))
    assert all(f.score > 0 for f in report.frames)


def test_exception_type_stored():
    report = score_frames9(_trace(exc_type="RuntimeError"))
    assert report.exception_type == "RuntimeError"


def test_exception_message_stored():
    report = score_frames9(_trace(exc_msg="something broke"))
    assert report.exception_message == "something broke"


def test_top_returns_highest_scoring_frame():
    frames = [_frame(function="inner", lineno=1), _frame(function="outer", lineno=100)]
    report = score_frames9(_trace(frames=frames))
    assert report.top is not None
    assert report.top.score == max(f.score for f in report.frames)


def test_ranked_descending_order():
    frames = [_frame(function=f"fn{i}") for i in range(5)]
    report = score_frames9(_trace(frames=frames))
    scores = [f.score for f in report.ranked]
    assert scores == sorted(scores, reverse=True)


def test_top_none_when_no_frames():
    report = ScoreReport9(frames=[], exception_type="E", exception_message="m")
    assert report.top is None


def test_scored_frame_str_contains_function():
    sf = ScoredFrame9(frame=_frame(function="my_func"), score=1.23, index=0)
    assert "my_func" in str(sf)


def test_scored_frame_str_contains_score():
    sf = ScoredFrame9(frame=_frame(), score=2.456, index=0)
    assert "2.456" in str(sf)


def test_higher_exception_weight_yields_higher_scores():
    t_runtime = _trace(exc_type="RecursionError")   # weight 1.6
    t_zero = _trace(exc_type="ZeroDivisionError")   # weight 1.0
    r1 = score_frames9(t_runtime)
    r2 = score_frames9(t_zero)
    assert r1.frames[0].score > r2.frames[0].score
