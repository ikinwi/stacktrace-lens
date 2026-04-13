"""Tests for stacktrace_lens.scorer3."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.scorer3 import (
    ScoreReport3,
    ScoredFrame3,
    score_frames3,
)


def _frame(filename: str = "app.py", function: str = "fn", lineno: int = 1) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad",
        frames=list(frames),
    )


def test_score_frames_returns_report():
    t = _trace(_frame())
    assert isinstance(score_frames3(t), ScoreReport3)


def test_report_frames_are_scored_frames():
    t = _trace(_frame(), _frame())
    report = score_frames3(t)
    assert all(isinstance(sf, ScoredFrame3) for sf in report.frames)


def test_frame_count_matches_trace():
    t = _trace(_frame(), _frame(), _frame())
    report = score_frames3(t)
    assert report.count == 3


def test_last_frame_has_highest_score():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    report = score_frames3(t)
    scores = [sf.score for sf in report.frames]
    assert scores[-1] == max(scores)


def test_first_frame_has_lowest_score():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    report = score_frames3(t)
    scores = [sf.score for sf in report.frames]
    assert scores[0] == min(scores)


def test_single_frame_scores_one():
    t = _trace(_frame())
    report = score_frames3(t)
    assert report.frames[0].score == pytest.approx(1.0)


def test_score_capped_at_one():
    t = _trace(_frame(), _frame())
    report = score_frames3(t)
    assert all(sf.score <= 1.0 for sf in report.frames)


def test_top_returns_highest_scored_frame():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    report = score_frames3(t)
    top = report.top()
    assert top is not None
    assert top.frame.filename == "c.py"


def test_top_returns_none_when_empty():
    t = _trace()
    report = score_frames3(t)
    assert report.top() is None


def test_ranked_is_descending():
    t = _trace(_frame("a.py"), _frame("b.py"), _frame("c.py"))
    ranked = score_frames3(t).ranked()
    scores = [sf.score for sf in ranked]
    assert scores == sorted(scores, reverse=True)


def test_str_contains_filename():
    f = _frame(filename="myfile.py", function="run", lineno=42)
    sf = ScoredFrame3(frame=f, score=0.75)
    assert "myfile.py" in str(sf)


def test_str_contains_score():
    f = _frame()
    sf = ScoredFrame3(frame=f, score=0.5)
    assert "0.5000" in str(sf)


def test_summary_line_no_frames():
    report = ScoreReport3(frames=[])
    assert "No frames" in report.summary_line()


def test_summary_line_with_frames():
    t = _trace(_frame())
    report = score_frames3(t)
    line = report.summary_line()
    assert "1" in line
