"""Tests for stacktrace_lens.differ."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.comparator import compare_traces
from stacktrace_lens.differ import (
    DiffLine,
    DiffRenderOptions,
    render_diff,
    summary_line,
)


def _frame(filename="app.py", lineno=10, function="run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="pass")


def _trace(exc_type="ValueError", exc_msg="bad", frames=None) -> StackTrace:
    if frames is None:
        frames = [_frame()]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


# ---------------------------------------------------------------------------
# render_diff
# ---------------------------------------------------------------------------

def test_render_diff_returns_string():
    diff = compare_traces(_trace(), _trace())
    result = render_diff(diff)
    assert isinstance(result, str)


def test_render_diff_contains_exception_type():
    diff = compare_traces(_trace(exc_type="TypeError"), _trace(exc_type="TypeError"))
    result = render_diff(diff, DiffRenderOptions(colour=False))
    assert "TypeError" in result


def test_render_diff_shows_added_frame():
    left = _trace(frames=[_frame("a.py")])
    right = _trace(frames=[_frame("a.py"), _frame("b.py")])
    diff = compare_traces(left, right)
    result = render_diff(diff, DiffRenderOptions(colour=False))
    assert "b.py" in result
    assert "+" in result


def test_render_diff_shows_removed_frame():
    left = _trace(frames=[_frame("a.py"), _frame("b.py")])
    right = _trace(frames=[_frame("a.py")])
    diff = compare_traces(left, right)
    result = render_diff(diff, DiffRenderOptions(colour=False))
    assert "b.py" in result
    assert "-" in result


def test_render_diff_exception_type_change_shows_both():
    diff = compare_traces(_trace(exc_type="ValueError"), _trace(exc_type="TypeError"))
    result = render_diff(diff, DiffRenderOptions(colour=False))
    assert "ValueError" in result
    assert "TypeError" in result


def test_render_diff_hide_unchanged_omits_unchanged_frames():
    left = _trace(frames=[_frame("a.py"), _frame("b.py")])
    right = _trace(frames=[_frame("a.py"), _frame("b.py")])
    diff = compare_traces(left, right)
    opts = DiffRenderOptions(colour=False, show_unchanged=False)
    result = render_diff(diff, opts)
    # unchanged frames should not appear (no leading space for frame lines)
    for line in result.splitlines():
        if "a.py" in line or "b.py" in line:
            assert not line.startswith("  File"), f"Unexpected unchanged frame line: {line!r}"


def test_render_diff_no_colour_has_no_escape_codes():
    diff = compare_traces(_trace(), _trace())
    result = render_diff(diff, DiffRenderOptions(colour=False))
    assert "\033[" not in result


def test_render_diff_with_colour_has_escape_codes():
    left = _trace(frames=[_frame("a.py")])
    right = _trace(frames=[_frame("a.py"), _frame("b.py")])
    diff = compare_traces(left, right)
    result = render_diff(diff, DiffRenderOptions(colour=True))
    assert "\033[" in result


# ---------------------------------------------------------------------------
# summary_line
# ---------------------------------------------------------------------------

def test_summary_line_returns_string():
    diff = compare_traces(_trace(), _trace())
    assert isinstance(summary_line(diff), str)


def test_summary_line_contains_counts():
    left = _trace(frames=[_frame("a.py"), _frame("b.py")])
    right = _trace(frames=[_frame("a.py"), _frame("c.py")])
    diff = compare_traces(left, right)
    line = summary_line(diff)
    assert "+" in line
    assert "-" in line
