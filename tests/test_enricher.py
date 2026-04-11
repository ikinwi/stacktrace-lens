"""Tests for stacktrace_lens.enricher."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.enricher import (
    EnrichedFrame,
    EnrichReport,
    enrich_trace,
    format_enrich_report,
    _is_stdlib,
    _is_third_party,
)


def _frame(
    filename: str = "app/main.py",
    lineno: int = 10,
    function: str = "run",
    context: str = "run()",
) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=context)


def _trace(*frames: Frame, exc: str = "RuntimeError", msg: str = "boom") -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# _is_stdlib / _is_third_party helpers
# ---------------------------------------------------------------------------

def test_is_stdlib_frozen():
    assert _is_stdlib("<frozen importlib._bootstrap>")


def test_is_stdlib_usr_lib():
    assert _is_stdlib("/usr/lib/python3.11/pathlib.py")


def test_is_stdlib_false_for_user_code():
    assert not _is_stdlib("app/main.py")


def test_is_third_party_site_packages():
    assert _is_third_party("/usr/local/lib/python3.11/site-packages/requests/api.py")


def test_is_third_party_false_for_user_code():
    assert not _is_third_party("app/models.py")


# ---------------------------------------------------------------------------
# enrich_trace return types
# ---------------------------------------------------------------------------

def test_enrich_trace_returns_enrich_report():
    report = enrich_trace(_trace(_frame()))
    assert isinstance(report, EnrichReport)


def test_enrich_frames_are_enriched_frame_instances():
    report = enrich_trace(_trace(_frame(), _frame()))
    for ef in report.frames:
        assert isinstance(ef, EnrichedFrame)


def test_frame_count_matches_trace():
    trace = _trace(_frame(), _frame(), _frame())
    report = enrich_trace(trace)
    assert len(report.frames) == 3


# ---------------------------------------------------------------------------
# depth assignment
# ---------------------------------------------------------------------------

def test_depth_starts_at_zero():
    report = enrich_trace(_trace(_frame()))
    assert report.frames[0].depth == 0


def test_depth_increments_per_frame():
    report = enrich_trace(_trace(_frame(), _frame(), _frame()))
    assert [ef.depth for ef in report.frames] == [0, 1, 2]


# ---------------------------------------------------------------------------
# call_chain_position
# ---------------------------------------------------------------------------

def test_single_frame_is_root():
    report = enrich_trace(_trace(_frame()))
    assert report.frames[0].call_chain_position == "root"


def test_first_frame_of_many_is_root():
    report = enrich_trace(_trace(_frame(), _frame(), _frame()))
    assert report.frames[0].call_chain_position == "root"


def test_last_frame_is_leaf():
    report = enrich_trace(_trace(_frame(), _frame(), _frame()))
    assert report.frames[-1].call_chain_position == "leaf"


def test_middle_frame_is_middle():
    report = enrich_trace(_trace(_frame(), _frame(), _frame()))
    assert report.frames[1].call_chain_position == "middle"


# ---------------------------------------------------------------------------
# stdlib / third-party classification
# ---------------------------------------------------------------------------

def test_stdlib_frame_flagged():
    f = _frame(filename="/usr/lib/python3.11/os.py")
    report = enrich_trace(_trace(f))
    assert report.frames[0].is_stdlib is True
    assert report.frames[0].is_third_party is False


def test_third_party_frame_flagged():
    f = _frame(filename="/env/lib/python3.11/site-packages/flask/app.py")
    report = enrich_trace(_trace(f))
    assert report.frames[0].is_third_party is True
    assert report.frames[0].is_stdlib is False


def test_user_frame_not_flagged():
    f = _frame(filename="app/views.py")
    report = enrich_trace(_trace(f))
    assert report.frames[0].is_stdlib is False
    assert report.frames[0].is_third_party is False


# ---------------------------------------------------------------------------
# user_frames / third_party_frames properties
# ---------------------------------------------------------------------------

def test_user_frames_excludes_third_party_and_stdlib():
    user = _frame(filename="app/views.py")
    third = _frame(filename="/env/lib/python3.11/site-packages/flask/app.py")
    stdlib = _frame(filename="/usr/lib/python3.11/os.py")
    report = enrich_trace(_trace(user, third, stdlib))
    assert len(report.user_frames) == 1
    assert report.user_frames[0].frame is user


def test_third_party_frames_property():
    user = _frame(filename="app/views.py")
    third = _frame(filename="/env/lib/python3.11/site-packages/flask/app.py")
    report = enrich_trace(_trace(user, third))
    assert len(report.third_party_frames) == 1


# ---------------------------------------------------------------------------
# tags
# ---------------------------------------------------------------------------

def test_stdlib_frame_has_stdlib_tag():
    f = _frame(filename="<frozen importlib._bootstrap>")
    report = enrich_trace(_trace(f))
    assert "stdlib" in report.frames[0].tags


def test_third_party_frame_has_third_party_tag():
    f = _frame(filename="/env/lib/python3.11/site-packages/requests/api.py")
    report = enrich_trace(_trace(f))
    assert "third-party" in report.frames[0].tags


def test_user_frame_has_no_tags():
    f = _frame(filename="app/models.py")
    report = enrich_trace(_trace(f))
    assert report.frames[0].tags == []


# ---------------------------------------------------------------------------
# format_enrich_report
# ---------------------------------------------------------------------------

def test_format_returns_string():
    report = enrich_trace(_trace(_frame()))
    result = format_enrich_report(report, colour=False)
    assert isinstance(result, str)


def test_format_contains_exception_type():
    report = enrich_trace(_trace(_frame(), exc="ValueError"))
    result = format_enrich_report(report, colour=False)
    assert "ValueError" in result


def test_format_contains_filename():
    f = _frame(filename="app/main.py")
    report = enrich_trace(_trace(f))
    result = format_enrich_report(report, colour=False)
    assert "app/main.py" in result


def test_format_no_colour_has_no_escape_codes():
    report = enrich_trace(_trace(_frame()))
    result = format_enrich_report(report, colour=False)
    assert "\033[" not in result
