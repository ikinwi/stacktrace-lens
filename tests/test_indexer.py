"""Tests for stacktrace_lens.indexer."""
from __future__ import annotations

import argparse
from io import StringIO

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.indexer import (
    IndexEntry,
    IndexReport,
    index_traces,
    format_index,
)
from stacktrace_lens.indexer_cmd import indexer_command


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "bad") -> StackTrace:
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=list(frames))


# --- index_traces ---

def test_index_traces_returns_index_report():
    report = index_traces([_trace(_frame())])
    assert isinstance(report, IndexReport)


def test_index_traces_total_matches_frame_count():
    t = _trace(_frame("a.py"), _frame("b.py"))
    report = index_traces([t])
    assert report.total == 2


def test_index_traces_multiple_traces():
    t1 = _trace(_frame("a.py"))
    t2 = _trace(_frame("b.py"), _frame("c.py"))
    report = index_traces([t1, t2])
    assert report.total == 3


def test_index_entry_trace_index():
    t0 = _trace(_frame("x.py"))
    t1 = _trace(_frame("y.py"))
    report = index_traces([t0, t1])
    assert report.entries[0].trace_index == 0
    assert report.entries[1].trace_index == 1


def test_index_entry_frame_index():
    t = _trace(_frame("a.py"), _frame("b.py"))
    report = index_traces([t])
    assert report.entries[0].frame_index == 0
    assert report.entries[1].frame_index == 1


def test_by_file_returns_matching_entries():
    t = _trace(_frame("app.py"), _frame("utils.py"), _frame("app.py"))
    report = index_traces([t])
    hits = report.by_file("app.py")
    assert len(hits) == 2
    assert all(e.frame.filename == "app.py" for e in hits)


def test_by_file_unknown_returns_empty():
    report = index_traces([_trace(_frame("app.py"))])
    assert report.by_file("missing.py") == []


def test_by_function_returns_matching_entries():
    t = _trace(_frame(function="main"), _frame(function="helper"), _frame(function="main"))
    report = index_traces([t])
    assert len(report.by_function("main")) == 2


def test_files_returns_sorted_list():
    t = _trace(_frame("z.py"), _frame("a.py"))
    report = index_traces([t])
    assert report.files() == ["a.py", "z.py"]


def test_functions_returns_sorted_list():
    t = _trace(_frame(function="zebra"), _frame(function="alpha"))
    report = index_traces([t])
    assert report.functions() == ["alpha", "zebra"]


def test_index_entry_str_contains_filename():
    entry = IndexEntry(frame=_frame("app.py", 42, "run"), trace_index=0, frame_index=0)
    assert "app.py" in str(entry)
    assert "42" in str(entry)


# --- format_index ---

def test_format_index_returns_string():
    report = index_traces([_trace(_frame())])
    assert isinstance(format_index(report), str)


def test_format_index_contains_total():
    report = index_traces([_trace(_frame("a.py"), _frame("b.py"))])
    out = format_index(report)
    assert "2" in out


def test_format_index_query_file_filters():
    t = _trace(_frame("app.py"), _frame("lib.py"))
    report = index_traces([t])
    out = format_index(report, query_file="app.py")
    assert "app.py" in out


def test_format_index_query_fn_filters():
    t = _trace(_frame(function="my_func"), _frame(function="other"))
    report = index_traces([t])
    out = format_index(report, query_fn="my_func")
    assert "my_func" in out


# --- indexer_command ---

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "query_file": None, "query_fn": None, "as_json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


SAMPLE_TRACE = """Traceback (most recent call last):
  File \"app.py\", line 5, in run
    do_thing()
ValueError: bad value
"""


def test_indexer_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", StringIO(SAMPLE_TRACE))
    out = StringIO()
    assert indexer_command(_args(), out=out) == 0


def test_indexer_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", StringIO(""))
    err = StringIO()
    assert indexer_command(_args(), err=err) == 1


def test_indexer_command_json_output(monkeypatch):
    import json as _json
    monkeypatch.setattr("sys.stdin", StringIO(SAMPLE_TRACE))
    out = StringIO()
    rc = indexer_command(_args(as_json=True), out=out)
    assert rc == 0
    data = _json.loads(out.getvalue())
    assert isinstance(data, list)


def test_indexer_command_returns_one_on_missing_file():
    err = StringIO()
    rc = indexer_command(_args(files=["/no/such/file.txt"]), err=err)
    assert rc == 1
