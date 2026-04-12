"""Tests for stacktrace_lens.recommender."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.recommender import (
    Recommendation,
    RecommendationReport,
    format_recommendations,
    recommend,
)


def _make_trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    n_frames: int = 3,
) -> StackTrace:
    frames = [
        Frame(filename=f"app/mod{i}.py", lineno=i * 10, function=f"func_{i}")
        for i in range(n_frames)
    ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# ---------------------------------------------------------------------------
# RecommendationReport
# ---------------------------------------------------------------------------

def test_report_count_reflects_recommendations():
    report = RecommendationReport(exception_type="TypeError")
    assert report.count == 0
    report.recommendations.append(Recommendation("t", "d", 1))
    assert report.count == 1


def test_report_top_returns_none_when_empty():
    report = RecommendationReport(exception_type="TypeError")
    assert report.top() is None


def test_report_top_returns_highest_priority():
    report = RecommendationReport(exception_type="TypeError")
    report.recommendations = [
        Recommendation("low", "d", 3),
        Recommendation("high", "d", 1),
        Recommendation("med", "d", 2),
    ]
    assert report.top().priority == 1


# ---------------------------------------------------------------------------
# recommend()
# ---------------------------------------------------------------------------

def test_recommend_returns_report_instance():
    trace = _make_trace()
    result = recommend(trace)
    assert isinstance(result, RecommendationReport)


def test_recommend_exception_type_stored():
    trace = _make_trace(exc_type="KeyError")
    result = recommend(trace)
    assert result.exception_type == "KeyError"


def test_recommend_known_exception_has_specific_advice():
    trace = _make_trace(exc_type="ZeroDivisionError")
    result = recommend(trace)
    titles = [r.title for r in result.recommendations]
    assert any("division" in t.lower() or "Guard" in t for t in titles)


def test_recommend_unknown_exception_has_generic_advice():
    trace = _make_trace(exc_type="MyCustomError")
    result = recommend(trace)
    assert result.count >= 1
    assert any("MyCustomError" in r.detail for r in result.recommendations)


def test_recommend_deep_trace_adds_depth_recommendation():
    trace = _make_trace(n_frames=25)
    result = recommend(trace)
    titles = [r.title for r in result.recommendations]
    assert any("deep" in t.lower() or "stack" in t.lower() for t in titles)


def test_recommend_shallow_trace_no_depth_recommendation():
    trace = _make_trace(n_frames=3)
    result = recommend(trace)
    titles = [r.title for r in result.recommendations]
    assert not any("deep" in t.lower() for t in titles)


def test_recommend_sorted_by_priority():
    trace = _make_trace(exc_type="ImportError", n_frames=25)
    result = recommend(trace)
    priorities = [r.priority for r in result.recommendations]
    assert priorities == sorted(priorities)


def test_recommend_import_error_high_priority():
    trace = _make_trace(exc_type="ImportError")
    result = recommend(trace)
    assert result.top() is not None
    assert result.top().priority == 1


# ---------------------------------------------------------------------------
# format_recommendations()
# ---------------------------------------------------------------------------

def test_format_recommendations_returns_string():
    trace = _make_trace()
    report = recommend(trace)
    output = format_recommendations(report)
    assert isinstance(output, str)


def test_format_recommendations_contains_exception_type():
    trace = _make_trace(exc_type="RuntimeError")
    report = recommend(trace)
    output = format_recommendations(report)
    assert "RuntimeError" in output


def test_format_recommendations_no_colour_has_no_escape_codes():
    trace = _make_trace()
    report = recommend(trace)
    output = format_recommendations(report, colour=False)
    assert "\033[" not in output


def test_format_recommendations_with_colour_contains_escape_codes():
    trace = _make_trace()
    report = recommend(trace)
    output = format_recommendations(report, colour=True)
    assert "\033[" in output


def test_recommendation_str_contains_badge():
    rec = Recommendation(title="Fix it", detail="Do something.", priority=1)
    assert "HIGH" in str(rec)
