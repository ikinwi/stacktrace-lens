"""Tests for scorer13."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer13 import (
    score_frames,
    ScoreReport13,
    ScoredFrame13,
    _exception_weight,
    _stdlib_penalty,
)


def _frame(filename="app/main.py", function="run", lineno=10):
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(exc="ValueError", msg="bad value", frames=None):
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc, exception_message=msg, frames=frames)


def test_score_frames_returns_report():
    assert isinstance(score_frames(_trace()), ScoreReport13)


def test_report_frames_are_scored_frames():
    report = score_frames(_trace())
    assert all(isinstance(f, ScoredFrame13) for f in report.frames)


def test_frame_count_matches_trace():
    t = _trace(frames=[_frame(), _frame(function="helper")])
    assert len(score_frames(t).frames) == 2


def test_exception_type_stored():
    assert score_frames(_trace(exc="TypeError")).exception_type == "TypeError"


def test_exception_weight_known():
    assert _exception_weight("ValueError") == 1.2


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("WeirdError") == 1.0


def test_exception_weight_substring_match():
    assert _exception_weight("MyImportError") == 1.4


def test_stdlib_penalty_stdlib_frame():
    f = _frame(filename="/usr/lib/python3.11/os.py")
    assert _stdlib_penalty(f) == 0.5


def test_stdlib_penalty_user_frame():
    f = _frame(filename="app/main.py")
    assert _stdlib_penalty(f) == 1.0


def test_stdlib_penalty_frozen_frame():
    f = _frame(filename="<frozen importlib._bootstrap>")
    assert _stdlib_penalty(f) == 0.5


def test_top_frame_returns_highest_score():
    frames = [
        _frame(filename="app/a.py", lineno=1),
        _frame(filename="app/b.py", lineno=100),
    ]
    report = score_frames(_trace(frames=frames))
    top = report.top_frame
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_ranked_descending():
    frames = [_frame(lineno=i * 10) for i in range(1, 5)]
    report = score_frames(_trace(frames=frames))
    scores = [sf.score for sf in report.ranked()]
    assert scores == sorted(scores, reverse=True)


def test_empty_frames_top_is_none():
    t = StackTrace(exception_type="ValueError", exception_message="x", frames=[])
    report = score_frames(t)
    assert report.top_frame is None


def test_scored_frame_str_contains_function():
    sf = ScoredFrame13(frame=_frame(function="my_func"), score=1.5)
    assert "my_func" in str(sf)


def test_scored_frame_str_contains_score():
    sf = ScoredFrame13(frame=_frame(), score=0.75)
    assert "0.750" in str(sf)
