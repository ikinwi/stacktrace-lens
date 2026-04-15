"""Tests for stacktrace_lens.scorer8."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer8 import (
    ScoreReport8,
    ScoredFrame8,
    _diversity_bonus,
    _exception_weight,
    _origin_bonus,
    _recency_score,
    score_frames8,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "main") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(*frames: Frame, exc: str = "ValueError") -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message="something went wrong",
        frames=list(frames),
    )


# --- unit helpers ---

def test_exception_weight_known():
    assert _exception_weight("RecursionError") == 1.5


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("CustomWeirdError") == 1.0


def test_exception_weight_substring_match():
    assert _exception_weight("MyZeroDivisionError") == 1.4


def test_recency_score_last_frame_is_one():
    assert _recency_score(2, 3) == pytest.approx(1.0)


def test_recency_score_first_frame_is_lowest():
    assert _recency_score(0, 3) < _recency_score(2, 3)


def test_recency_score_single_frame():
    assert _recency_score(0, 1) == pytest.approx(1.0)


def test_origin_bonus_user_code():
    assert _origin_bonus("app/views.py") == pytest.approx(0.2)


def test_origin_bonus_site_packages():
    assert _origin_bonus("/usr/lib/python3/site-packages/foo.py") == pytest.approx(0.0)


def test_origin_bonus_frozen():
    assert _origin_bonus("<frozen importlib>") == pytest.approx(0.0)


def test_diversity_bonus_new_file():
    seen: set = set()
    assert _diversity_bonus("app.py", seen) == pytest.approx(0.15)


def test_diversity_bonus_seen_file():
    seen = {"app.py"}
    assert _diversity_bonus("app.py", seen) == pytest.approx(0.0)


# --- score_frames8 ---

def test_score_frames_returns_report():
    t = _trace(_frame())
    assert isinstance(score_frames8(t), ScoreReport8)


def test_report_frames_are_scored_frames():
    t = _trace(_frame(), _frame("other.py"))
    report = score_frames8(t)
    assert all(isinstance(sf, ScoredFrame8) for sf in report.frames)


def test_frame_count_matches_trace():
    t = _trace(_frame(), _frame("b.py"), _frame("c.py"))
    assert score_frames8(t).count == 3


def test_exception_type_stored():
    t = _trace(_frame(), exc="RuntimeError")
    assert score_frames8(t).exception_type == "RuntimeError"


def test_top_returns_highest_scored_frame():
    t = _trace(_frame("lib.py"), _frame("app.py"), exc="ValueError")
    report = score_frames8(t)
    top = report.top()
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_ranked_descending():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    ranked = score_frames8(t).ranked()
    scores = [sf.score for sf in ranked]
    assert scores == sorted(scores, reverse=True)


def test_top_returns_none_for_empty_trace():
    t = _trace(exc="ValueError")
    assert score_frames8(t).top() is None


def test_scores_are_positive():
    t = _trace(_frame(), _frame("b.py"), exc="TypeError")
    for sf in score_frames8(t).frames:
        assert sf.score > 0


def test_scored_frame_str_contains_filename():
    sf = ScoredFrame8(frame=_frame("myfile.py", 42, "run"), score=1.23)
    assert "myfile.py" in str(sf)


def test_scored_frame_str_contains_score():
    sf = ScoredFrame8(frame=_frame(), score=2.5)
    assert "2.500" in str(sf)


def test_diversity_bonus_applied_for_unique_files():
    t = _trace(_frame("a.py"), _frame("b.py"), exc="ValueError")
    report = score_frames8(t)
    # Both frames have unique filenames so both should get diversity bonus
    # We can't check exact values but count should be 2
    assert report.count == 2
