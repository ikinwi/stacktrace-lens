"""Tests for stacktrace_lens.scorer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer import (
    ScoreReport,
    ScoredFrame,
    score_frames,
)


def _frame(filename: str, lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        frames=list(frames),
        exception_type="ValueError",
        exception_message="bad value",
    )


# ---------------------------------------------------------------------------
# score_frames return type
# ---------------------------------------------------------------------------

def test_score_frames_returns_report():
    t = _trace(_frame("app/main.py"))
    assert isinstance(score_frames(t), ScoreReport)


def test_report_frames_are_scored_frames():
    t = _trace(_frame("app/main.py"))
    report = score_frames(t)
    assert all(isinstance(sf, ScoredFrame) for sf in report.frames)


def test_frame_count_matches_trace():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    report = score_frames(t)
    assert len(report.frames) == 3


# ---------------------------------------------------------------------------
# scoring logic
# ---------------------------------------------------------------------------

def test_user_code_scores_higher_than_stdlib():
    user = _frame("myapp/views.py")
    stdlib = _frame("/usr/lib/python3.11/lib/python3.11/traceback.py")
    t = _trace(user, stdlib)
    report = score_frames(t)
    user_score = next(sf for sf in report.frames if sf.frame is user).score
    stdlib_score = next(sf for sf in report.frames if sf.frame is stdlib).score
    assert user_score > stdlib_score


def test_site_packages_penalised():
    noisy = _frame("/home/user/.venv/lib/python3.11/site-packages/django/core/handlers/base.py")
    t = _trace(noisy)
    report = score_frames(t)
    assert report.frames[0].score < 0.5


def test_innermost_frame_gets_depth_bonus():
    frames = [_frame(f"myapp/mod{i}.py") for i in range(5)]
    t = _trace(*frames)
    report = score_frames(t)
    scores = [sf.score for sf in report.frames]
    # Last frame should have a higher depth contribution than first
    assert scores[-1] >= scores[0]


# ---------------------------------------------------------------------------
# top_frame / ranked helpers
# ---------------------------------------------------------------------------

def test_top_frame_returns_highest_score():
    t = _trace(_frame("myapp/a.py"), _frame("/usr/lib/python3.11/lib/python3.11/os.py"))
    report = score_frames(t)
    top = report.top_frame
    assert top is not None
    assert top.score == max(sf.score for sf in report.frames)


def test_top_frame_none_on_empty_report():
    report = ScoreReport(frames=[])
    assert report.top_frame is None


def test_ranked_is_descending():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    report = score_frames(t)
    ranked = report.ranked
    scores = [sf.score for sf in ranked]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# reason field
# ---------------------------------------------------------------------------

def test_reason_non_empty():
    t = _trace(_frame("myapp/views.py"))
    report = score_frames(t)
    assert report.frames[0].reason != ""


def test_stdlib_reason_contains_label():
    stdlib = _frame("/usr/lib/python3.11/lib/python3.11/traceback.py")
    t = _trace(stdlib)
    report = score_frames(t)
    assert "stdlib" in report.frames[0].reason or "third-party" in report.frames[0].reason
