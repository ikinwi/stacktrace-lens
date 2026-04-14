"""Tests for stacktrace_lens.grapher."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.grapher import (
    GraphNode,
    GraphReport,
    build_graph,
    format_graph,
    _node_label,
)


def _frame(filename: str, function: str, lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "oops") -> StackTrace:
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=list(frames))


# ---------------------------------------------------------------------------
# GraphNode
# ---------------------------------------------------------------------------

def test_graph_node_str_contains_label():
    node = GraphNode(label="app.py:main", call_count=3)
    assert "app.py:main" in str(node)


def test_graph_node_str_contains_count():
    node = GraphNode(label="app.py:main", call_count=7)
    assert "7" in str(node)


# ---------------------------------------------------------------------------
# _node_label helper
# ---------------------------------------------------------------------------

def test_node_label_uses_basename():
    label = _node_label("/home/user/project/app.py", "main")
    assert label == "app.py:main"


def test_node_label_none_function_becomes_module():
    label = _node_label("app.py", None)
    assert "<module>" in label


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------

def test_build_graph_returns_graph_report():
    trace = _trace(_frame("a.py", "foo"), _frame("b.py", "bar"))
    report = build_graph([trace])
    assert isinstance(report, GraphReport)


def test_build_graph_total_traces_count():
    t1 = _trace(_frame("a.py", "foo"))
    t2 = _trace(_frame("b.py", "baz"))
    report = build_graph([t1, t2])
    assert report.total_traces == 2


def test_build_graph_empty_list_zero_totals():
    report = build_graph([])
    assert report.total_traces == 0
    assert report.root_count == 0
    assert report.total_edges == 0


def test_build_graph_single_frame_creates_root():
    trace = _trace(_frame("app.py", "main"))
    report = build_graph([trace])
    assert report.root_count == 1


def test_build_graph_two_frames_creates_one_edge():
    trace = _trace(_frame("a.py", "caller"), _frame("b.py", "callee"))
    report = build_graph([trace])
    assert report.total_edges == 1


def test_build_graph_same_root_increments_call_count():
    t1 = _trace(_frame("a.py", "foo"), _frame("b.py", "bar"))
    t2 = _trace(_frame("a.py", "foo"), _frame("c.py", "baz"))
    report = build_graph([t1, t2])
    root = next(iter(report.roots.values()))
    assert root.call_count == 2


def test_build_graph_empty_trace_skipped():
    trace = StackTrace(exception_type="E", exception_message="m", frames=[])
    report = build_graph([trace])
    assert report.root_count == 0


# ---------------------------------------------------------------------------
# format_graph
# ---------------------------------------------------------------------------

def test_format_graph_returns_string():
    trace = _trace(_frame("a.py", "foo"), _frame("b.py", "bar"))
    report = build_graph([trace])
    result = format_graph(report)
    assert isinstance(result, str)


def test_format_graph_contains_summary():
    trace = _trace(_frame("a.py", "foo"))
    report = build_graph([trace])
    result = format_graph(report)
    assert "1 trace" in result


def test_format_graph_contains_root_label():
    trace = _trace(_frame("app.py", "main"))
    report = build_graph([trace])
    result = format_graph(report)
    assert "app.py:main" in result
