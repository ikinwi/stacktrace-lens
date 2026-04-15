"""Tests for stacktrace_lens.splitter2_renderer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.splitter2 import segment_trace
from stacktrace_lens.splitter2_renderer import Splitter2Renderer


def _frame(filename: str = "app/main.py", function: str = "run", lineno: int = 5) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(*frames: Frame, exc_type: str = "ValueError") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message="bad value",
        frames=list(frames),
    )


@pytest.fixture()
def renderer() -> Splitter2Renderer:
    return Splitter2Renderer(use_color=False)


def test_render_returns_string(renderer: Splitter2Renderer) -> None:
    report = segment_trace(_trace(_frame()))
    result = renderer.render(report)
    assert isinstance(result, str)


def test_render_contains_exception_type(renderer: Splitter2Renderer) -> None:
    report = segment_trace(_trace(_frame(), exc_type="KeyError"))
    result = renderer.render(report)
    assert "KeyError" in result


def test_render_contains_segment_label(renderer: Splitter2Renderer) -> None:
    report = segment_trace(_trace(_frame(filename="django/db/models.py")))
    result = renderer.render(report)
    assert "django" in result


def test_render_contains_function_name(renderer: Splitter2Renderer) -> None:
    report = segment_trace(_trace(_frame(function="my_func")))
    result = renderer.render(report)
    assert "my_func" in result


def test_render_contains_lineno(renderer: Splitter2Renderer) -> None:
    report = segment_trace(_trace(_frame(lineno=42)))
    result = renderer.render(report)
    assert "42" in result


def test_render_multiple_segments(renderer: Splitter2Renderer) -> None:
    f1 = _frame(filename="app/a.py")
    f2 = _frame(filename="lib/x.py")
    report = segment_trace(_trace(f1, f2))
    result = renderer.render(report)
    assert "app" in result
    assert "lib" in result


def test_render_with_color_does_not_crash() -> None:
    r = Splitter2Renderer(use_color=True)
    report = segment_trace(_trace(_frame()))
    result = r.render(report)
    assert isinstance(result, str)


def test_render_empty_trace(renderer: Splitter2Renderer) -> None:
    report = segment_trace(_trace())
    result = renderer.render(report)
    assert isinstance(result, str)
