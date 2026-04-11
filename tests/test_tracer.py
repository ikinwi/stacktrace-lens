"""Tests for stacktrace_lens.tracer."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.tracer import Lineage, TraceNode


def _make_trace(exc_type: str = "ValueError") -> StackTrace:
    frame = Frame(filename="app.py", lineno=10, function="run", source_line="x()")
    return StackTrace(frames=[frame], exception_type=exc_type,
                      exception_message="oops", raw="")


# --- Lineage.add ---

def test_add_returns_trace_node():
    lineage = Lineage()
    node = lineage.add(_make_trace())
    assert isinstance(node, TraceNode)


def test_add_stores_node_in_lineage():
    lineage = Lineage()
    node = lineage.add(_make_trace())
    assert lineage.get(node.trace_id) is node


def test_root_node_has_no_parent():
    lineage = Lineage()
    node = lineage.add(_make_trace())
    assert node.parent_id is None
    assert node.is_root


def test_child_node_has_parent_id():
    lineage = Lineage()
    root = lineage.add(_make_trace())
    child = lineage.add(_make_trace("TypeError"), parent_id=root.trace_id)
    assert child.parent_id == root.trace_id
    assert not child.is_root


def test_parent_children_list_updated():
    lineage = Lineage()
    root = lineage.add(_make_trace())
    child = lineage.add(_make_trace(), parent_id=root.trace_id)
    assert child.trace_id in root.children


def test_label_stored_on_node():
    lineage = Lineage()
    node = lineage.add(_make_trace(), label="initial")
    assert node.label == "initial"


# --- Lineage.roots ---

def test_roots_returns_only_root_nodes():
    lineage = Lineage()
    r1 = lineage.add(_make_trace())
    r2 = lineage.add(_make_trace())
    lineage.add(_make_trace(), parent_id=r1.trace_id)
    roots = lineage.roots()
    assert r1 in roots and r2 in roots
    assert len(roots) == 2


# --- Lineage.ancestors ---

def test_ancestors_of_root_is_empty():
    lineage = Lineage()
    root = lineage.add(_make_trace())
    assert lineage.ancestors(root.trace_id) == []


def test_ancestors_returns_chain():
    lineage = Lineage()
    root = lineage.add(_make_trace())
    mid = lineage.add(_make_trace(), parent_id=root.trace_id)
    leaf = lineage.add(_make_trace(), parent_id=mid.trace_id)
    anc = lineage.ancestors(leaf.trace_id)
    assert [n.trace_id for n in anc] == [root.trace_id, mid.trace_id]


# --- Lineage.depth_of ---

def test_depth_of_root_is_zero():
    lineage = Lineage()
    root = lineage.add(_make_trace())
    assert lineage.depth_of(root.trace_id) == 0


def test_depth_of_child_is_one():
    lineage = Lineage()
    root = lineage.add(_make_trace())
    child = lineage.add(_make_trace(), parent_id=root.trace_id)
    assert lineage.depth_of(child.trace_id) == 1


# --- Lineage.size ---

def test_size_reflects_node_count():
    lineage = Lineage()
    assert lineage.size() == 0
    lineage.add(_make_trace())
    lineage.add(_make_trace())
    assert lineage.size() == 2
