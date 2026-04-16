"""Tests for stacktrace_lens.scorer10."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer10 import (
    _exception_weight,
    _entropy_bonus,
    _depth_score,
    score_frames,
    ScoreReport10,
    ScoredFrame10,
)


def _frame(filename="app.py", lineno=10, function="main"):
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(frames=None, exc="ValueError", msg="bad value"):
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=frames or [_frame()],
    )


def test_exception_weight_known():
    assert _exception_weight("ValueError") == 1.2


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("CustomError") == 1.0


def test_exception_weight_substring_match():
    assert _exception_weight("MyImportError") == 1.4


def test_depth_score_single_frame():
    assert _depth_score(0, 1) == 1.0


def test_depth_score_first_of_many():
    assert _depth_score(0, 5) == 0.0


def test_depth_score_last_of_many():
    assert _depth_score(4, 5) == 1.0


def test_entropy_bonus_unique_file():
    frames = [_frame("a.py"), _frame("b.py"), _frame("c.py")]
    bonus = _entropy_bonus(frames[0], frames)
    assert bonus == pytest.approx(1 - 1 / 3, rel=1e-3)


def test_entropy_bonus_repeated_file():
    frames = [_frame("a.py"), _frame("a.py")]
    bonus = _entropy_bonus(frames[0], frames)
    assert bonus == 0.0


def test_entropy_bonus_empty_frames():
    assert _entropy_bonus(_frame(), []) == 0.0


def test_score_frames_returns_report():
    report = score_frames(_trace())
    assert isinstance(report, ScoreReport10)


def test_report_frames_are_scored_frames():
    report = score_frames(_trace(frames=[_frame(), _frame("b.py")]))
    assert all(isinstance(f, ScoredFrame10) for f in report.frames)


def test_frame_count_matches_trace():
    frames = [_frame(), _frame("b.py"), _frame("c.py")]
    report = score_frames(_trace(frames=frames))
    assert report.count == 3


def test_exception_type_stored():
    report = score_frames(_trace(exc="RuntimeError"))
    assert report.exception_type == "RuntimeError"


def test_top_returns_highest_score():
    frames = [_frame("a.py"), _frame("b.py"), _frame("c.py")]
    report = score_frames(_trace(frames=frames))
    top = report.top()
    assert top is not None
    assert top.score == max(f.score for f in report.frames)


def test_top_returns_none_for_empty():
    report = ScoreReport10(exception_type="E", frames=[])
    assert report.top() is None


def test_ranked_descending():
    frames = [_frame("a.py"), _frame("b.py"), _frame("c.py")]
    report = score_frames(_trace(frames=frames))
    scores = [f.score for f in report.ranked()]
    assert scores == sorted(scores, reverse=True)


def test_scored_frame_str_contains_filename():
    sf = ScoredFrame10(frame=_frame("myfile.py", 42, "run"), score=0.75)
    assert "myfile.py" in str(sf)
    assert "0.750" in str(sf)
