"""Tests for stacktrace_lens.scorer6."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer6 import (
    ScoreReport6,
    ScoredFrame6,
    _depth_score,
    _exception_weight,
    _origin_bonus,
    score_frames6,
)


def _frame(filename: str = "app/main.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(*frames: Frame, exc_type: str = "ValueError") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message="something went wrong",
        frames=list(frames),
    )


def test_score_frames_returns_report():
    t = _trace(_frame())
    assert isinstance(score_frames6(t), ScoreReport6)


def test_report_frames_are_scored_frames():
    t = _trace(_frame(), _frame())
    report = score_frames6(t)
    assert all(isinstance(f, ScoredFrame6) for f in report.frames)


def test_frame_count_matches_trace():
    frames = [_frame() for _ in range(5)]
    t = _trace(*frames)
    assert score_frames6(t).count == 5


def test_exception_weight_known():
    assert _exception_weight("ImportError") == pytest.approx(1.4)


def test_exception_weight_unknown_defaults_to_one():
    assert _exception_weight("CustomError") == pytest.approx(1.0)


def test_exception_weight_substring_match():
    assert _exception_weight("ModuleNotFoundError") == pytest.approx(1.4)


def test_origin_bonus_user_code():
    assert _origin_bonus("app/main.py") == pytest.approx(1.0)


def test_origin_bonus_site_packages():
    assert _origin_bonus("/usr/local/lib/python3.11/site-packages/requests/api.py") == pytest.approx(0.6)


def test_origin_bonus_stdlib():
    assert _origin_bonus("/usr/lib/python3.11/os.py") == pytest.approx(0.4)


def test_origin_bonus_empty():
    assert _origin_bonus("") == pytest.approx(0.5)


def test_depth_score_single_frame():
    assert _depth_score(0, 1) == pytest.approx(1.0)


def test_depth_score_last_frame_highest():
    assert _depth_score(4, 5) > _depth_score(0, 5)


def test_top_returns_highest_scored():
    t = _trace(_frame("app/a.py"), _frame("app/b.py"), _frame("app/c.py"))
    report = score_frames6(t)
    top = report.top
    assert top is not None
    assert top.score == max(f.score for f in report.frames)


def test_ranked_descending():
    t = _trace(_frame(), _frame(), _frame())
    ranked = score_frames6(t).ranked()
    scores = [f.score for f in ranked]
    assert scores == sorted(scores, reverse=True)


def test_top_none_on_empty_trace():
    t = StackTrace(exception_type="ValueError", exception_message="", frames=[])
    assert score_frames6(t).top is None


def test_str_contains_function_name():
    t = _trace(_frame(function="my_func"))
    sf = score_frames6(t).frames[0]
    assert "my_func" in str(sf)


def test_exception_type_stored():
    t = _trace(_frame(), exc_type="RecursionError")
    assert score_frames6(t).exception_type == "RecursionError"
