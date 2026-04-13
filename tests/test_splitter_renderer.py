"""Tests for SplitterRenderer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.splitter import SplitReport
from stacktrace_lens.splitter_renderer import SplitterRenderer


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "main", code: str = "pass") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, code=code)


def _trace(exc_type: str = "ValueError", exc_msg: str = "bad value", frames=None) -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=frames or [_frame()],
    )


def _report(traces=None, is_chained: bool = False) -> SplitReport:
    return SplitReport(
        traces=traces or [_trace()],
        is_chained=is_chained,
    )


@pytest.fixture
def renderer() -> SplitterRenderer:
    return SplitterRenderer(colour=False)


def test_render_returns_string(renderer):
    result = renderer.render(_report())
    assert isinstance(result, str)


def test_render_contains_trace_count(renderer):
    result = renderer.render(_report(traces=[_trace(), _trace()]))
    assert "2 trace(s)" in result


def test_render_single_exception_label(renderer):
    result = renderer.render(_report(is_chained=False))
    assert "[single exception]" in result


def test_render_chained_label(renderer):
    result = renderer.render(_report(is_chained=True))
    assert "[chained exception]" in result


def test_render_contains_exception_type(renderer):
    result = renderer.render(_report(traces=[_trace(exc_type="TypeError")]))
    assert "TypeError" in result


def test_render_contains_exception_message(renderer):
    result = renderer.render(_report(traces=[_trace(exc_msg="something went wrong")]))
    assert "something went wrong" in result


def test_render_contains_filename(renderer):
    result = renderer.render(_report(traces=[_trace(frames=[_frame(filename="mymodule.py")])]))
    assert "mymodule.py" in result


def test_render_contains_function_name(renderer):
    result = renderer.render(_report(traces=[_trace(frames=[_frame(function="do_work")])]))
    assert "do_work" in result


def test_render_contains_lineno(renderer):
    result = renderer.render(_report(traces=[_trace(frames=[_frame(lineno=42)])]))
    assert "42" in result


def test_render_contains_code_snippet(renderer):
    result = renderer.render(_report(traces=[_trace(frames=[_frame(code="x = 1 / 0")])]))
    assert "x = 1 / 0" in result


def test_render_multiple_traces_numbered(renderer):
    result = renderer.render(_report(traces=[_trace(), _trace()], is_chained=True))
    assert "Trace 1" in result
    assert "Trace 2" in result


def test_render_with_colour_does_not_crash():
    r = SplitterRenderer(colour=True)
    result = r.render(_report())
    assert isinstance(result, str)
    assert len(result) > 0
