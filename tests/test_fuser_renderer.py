"""Tests for stacktrace_lens.fuser_renderer."""
import pytest
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.fuser import fuse_traces
from stacktrace_lens.fuser_renderer import FuserRenderer


def _frame(filename="app.py", lineno=10, function="main") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(*frames, exc="ValueError", msg="oops") -> StackTrace:
    return StackTrace(exception_type=exc, exception_message=msg, frames=list(frames))


def test_render_returns_string():
    t = _trace(_frame())
    report = fuse_traces(t, t)
    renderer = FuserRenderer(color=False)
    assert isinstance(renderer.render(report), str)


def test_render_contains_summary():
    t = _trace(_frame())
    report = fuse_traces(t, t)
    renderer = FuserRenderer(color=False)
    out = renderer.render(report)
    assert "shared" in out


def test_render_contains_exception_types():
    left = _trace(_frame(), exc="TypeError")
    right = _trace(_frame(), exc="ValueError")
    report = fuse_traces(left, right)
    renderer = FuserRenderer(color=False)
    out = renderer.render(report)
    assert "TypeError" in out
    assert "ValueError" in out


def test_render_contains_filename():
    t = _trace(_frame("myapp.py"))
    report = fuse_traces(t, t)
    renderer = FuserRenderer(color=False)
    out = renderer.render(report)
    assert "myapp.py" in out


def test_render_no_color_has_no_escape_codes():
    t = _trace(_frame())
    report = fuse_traces(t, t)
    renderer = FuserRenderer(color=False)
    out = renderer.render(report)
    assert "\033[" not in out


def test_render_color_has_escape_codes():
    t = _trace(_frame())
    report = fuse_traces(t, t)
    renderer = FuserRenderer(color=True)
    out = renderer.render(report)
    assert "\033[" in out


def test_render_left_only_label():
    left = _trace(_frame("left.py", 1, "lf"))
    right = _trace(_frame("right.py", 2, "rf"))
    report = fuse_traces(left, right)
    renderer = FuserRenderer(color=False)
    out = renderer.render(report)
    assert "left-only" in out
    assert "right-only" in out
