import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer14 import (
    ScoreReport14,
    ScoredFrame14,
    score_frames14,
    _exception_weight,
    _centrality_score,
    _noise_penalty,
)


def _frame(filename="app/main.py", function="run", lineno=10):
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(exc_type="ValueError", exc_msg="bad value", n=3):
    frames = [_frame(lineno=i + 1) for i in range(n)]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


def test_score_frames_returns_report():
    assert isinstance(score_frames14(_trace()), ScoreReport14)


def test_report_frames_are_scored_frames():
    report = score_frames14(_trace())
    assert all(isinstance(f, ScoredFrame14) for f in report.frames)


def test_frame_count_matches_trace():
    t = _trace(n=5)
    report = score_frames14(t)
    assert report.count == 5


def test_exception_type_stored():
    report = score_frames14(_trace(exc_type="ImportError"))
    assert report.exception_type == "ImportError"


def test_exception_message_stored():
    report = score_frames14(_trace(exc_msg="oops"))
    assert report.exception_message == "oops"


def test_scores_are_positive():
    report = score_frames14(_trace(n=4))
    assert all(sf.score > 0 for sf in report.frames)


def test_top_returns_highest_score():
    report = score_frames14(_trace(n=5))
    top = report.top()
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_top_returns_none_for_empty_trace():
    t = StackTrace(exception_type="E", exception_message="", frames=[])
    report = score_frames14(t)
    assert report.top() is None


def test_ranked_descending():
    report = score_frames14(_trace(n=6))
    scores = [sf.score for sf in report.ranked()]
    assert scores == sorted(scores, reverse=True)


def test_exception_weight_known():
    assert _exception_weight("RecursionError") == 1.5


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("WeirdError") == 1.0


def test_exception_weight_none_defaults_to_one():
    assert _exception_weight(None) == 1.0


def test_centrality_score_single_frame():
    assert _centrality_score(0, 1) == 1.0


def test_centrality_score_middle_highest():
    scores = [_centrality_score(i, 5) for i in range(5)]
    assert scores[2] == max(scores)


def test_noise_penalty_for_frozen():
    f = _frame(filename="frozen importlib")
    assert _noise_penalty(f) == 0.5


def test_noise_penalty_normal_frame():
    f = _frame(filename="app/utils.py")
    assert _noise_penalty(f) == 1.0


def test_str_representation():
    report = score_frames14(_trace(n=1))
    s = str(report.frames[0])
    assert "app/main.py" in s
    assert "run" in s
