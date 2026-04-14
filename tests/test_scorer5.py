"""Tests for stacktrace_lens.scorer5."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer5 import (
    ScoreReport5,
    ScoredFrame5,
    score_frames5,
    _exception_weight,
    _origin_bonus,
    _recency_score,
)


def _frame(filename="app/main.py", lineno=10, function="run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(frames=None, exc_type="ValueError") -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message="oops", frames=frames)


# --- unit helpers ---

def test_exception_weight_known():
    assert _exception_weight("MemoryError") == 2.0


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("SomeCrazyError") == 1.0


def test_exception_weight_substring_match():
    assert _exception_weight("MyValueError") == 1.1


def test_origin_bonus_user_code():
    assert _origin_bonus("app/main.py") == 1.0


def test_origin_bonus_stdlib():
    assert _origin_bonus("/usr/lib/python3.11/os.py") == 0.0


def test_origin_bonus_site_packages():
    assert _origin_bonus("/home/user/.venv/lib/site-packages/requests/api.py") == 0.3


def test_origin_bonus_empty_string():
    assert _origin_bonus("") == 0.0


def test_recency_score_single_frame():
    assert _recency_score(0, 1) == 1.0


def test_recency_score_last_frame_is_highest():
    assert _recency_score(4, 5) > _recency_score(0, 5)


def test_recency_score_proportional():
    assert _recency_score(1, 4) == pytest.approx(0.5)


# --- score_frames5 ---

def test_score_frames_returns_report():
    report = score_frames5(_trace())
    assert isinstance(report, ScoreReport5)


def test_report_frames_are_scored_frames():
    report = score_frames5(_trace())
    assert all(isinstance(f, ScoredFrame5) for f in report.frames)


def test_frame_count_matches_trace():
    frames = [_frame() for _ in range(4)]
    report = score_frames5(_trace(frames=frames))
    assert report.count == 4


def test_exception_type_stored():
    report = score_frames5(_trace(exc_type="RuntimeError"))
    assert report.exception_type == "RuntimeError"


def test_top_returns_first_frame_when_one():
    report = score_frames5(_trace())
    assert report.top() is not None
    assert isinstance(report.top(), ScoredFrame5)


def test_top_returns_none_for_empty():
    empty = StackTrace(exception_type="E", exception_message="m", frames=[])
    report = score_frames5(empty)
    assert report.top() is None


def test_ranked_sorted_descending():
    frames = [_frame(lineno=i) for i in range(5)]
    report = score_frames5(_trace(frames=frames))
    ranked = report.ranked()
    scores = [f.score for f in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_assigned_to_frames():
    frames = [_frame(lineno=i) for i in range(3)]
    report = score_frames5(_trace(frames=frames))
    ranks = {sf.rank for sf in report.frames}
    assert ranks == {1, 2, 3}


def test_scored_frame_str_contains_function():
    sf = ScoredFrame5(frame=_frame(function="my_func"), score=0.75, rank=1)
    assert "my_func" in str(sf)


def test_scored_frame_str_contains_score():
    sf = ScoredFrame5(frame=_frame(), score=0.75, rank=1)
    assert "0.750" in str(sf)


def test_high_exception_weight_inflates_score():
    f_mem = score_frames5(_trace(exc_type="MemoryError"))
    f_val = score_frames5(_trace(exc_type="ValueError"))
    assert f_mem.frames[0].score > f_val.frames[0].score
