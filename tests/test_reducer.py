"""Tests for stacktrace_lens.reducer."""
from __future__ import annotations

import argparse
from io import StringIO
from typing import List

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.reducer import (
    ReduceOptions,
    ReduceReport,
    ReducedFrame,
    reduce_trace,
)
from stacktrace_lens.reducer_cmd import _build_subparser, reducer_command


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn", code: str = "pass") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, code=code)


def _trace(frames: List[Frame], exc: str = "ValueError", msg: str = "bad") -> StackTrace:
    return StackTrace(exception_type=exc, exception_message=msg, frames=frames)


# --- reduce_trace ---

def test_reduce_returns_report():
    trace = _trace([_frame()])
    report = reduce_trace(trace)
    assert isinstance(report, ReduceReport)


def test_reduce_report_items_are_reduced_frames():
    trace = _trace([_frame(), _frame("other.py")])
    report = reduce_trace(trace)
    assert all(isinstance(rf, ReducedFrame) for rf in report.reduced_frames)


def test_original_count_matches_input_frames():
    frames = [_frame(f"f{i}.py") for i in range(5)]
    report = reduce_trace(_trace(frames))
    assert report.original_count == 5


def test_no_duplicates_preserves_all_frames():
    frames = [_frame(f"f{i}.py", lineno=i) for i in range(4)]
    report = reduce_trace(_trace(frames))
    assert report.reduced_count == 4


def test_consecutive_duplicates_collapsed():
    frame = _frame("app.py", lineno=5)
    trace = _trace([frame, frame, frame])
    report = reduce_trace(trace, ReduceOptions(collapse_duplicates=True))
    assert report.reduced_count == 1
    assert report.reduced_frames[0].repeat_count == 3


def test_no_collapse_keeps_duplicates():
    frame = _frame("app.py", lineno=5)
    trace = _trace([frame, frame])
    report = reduce_trace(trace, ReduceOptions(collapse_duplicates=False))
    assert report.reduced_count == 2


def test_keep_top_limits_frames():
    frames = [_frame(f"f{i}.py", lineno=i) for i in range(10)]
    report = reduce_trace(_trace(frames), ReduceOptions(keep_top=3))
    assert report.original_count == 3


def test_removed_count_property():
    frames = [_frame(f"f{i}.py", lineno=i) for i in range(5)]
    frame_dup = _frame("app.py", lineno=99)
    trace = _trace(frames + [frame_dup, frame_dup])
    report = reduce_trace(trace, ReduceOptions(collapse_duplicates=True))
    assert report.removed_count == report.original_count - report.reduced_count


def test_reduced_frame_str_includes_filename():
    rf = ReducedFrame(frame=_frame("myfile.py", lineno=42, function="do_thing"))
    assert "myfile.py" in str(rf)


def test_reduced_frame_str_includes_repeat_when_gt_1():
    rf = ReducedFrame(frame=_frame(), repeat_count=4, collapsed=True)
    assert "x4" in str(rf)


# --- reducer_command ---

def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(file=None, max_stdlib=3, no_collapse=False, keep_top=None, no_color=True)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


SAMPLE = """Traceback (most recent call last):
  File \"app.py\", line 10, in main
    run()
ValueError: something went wrong
"""


def test_reducer_command_returns_zero_on_valid_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", StringIO(SAMPLE))
    out = StringIO()
    rc = reducer_command(_args(), out=out)
    assert rc == 0


def test_reducer_command_returns_one_on_empty_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", StringIO(""))
    rc = reducer_command(_args(), out=StringIO(), err=StringIO())
    assert rc == 1


def test_reducer_command_reads_from_file(tmp_path):
    f = tmp_path / "trace.txt"
    f.write_text(SAMPLE)
    out = StringIO()
    rc = reducer_command(_args(file=str(f)), out=out)
    assert rc == 0
    assert "ValueError" in out.getvalue()


def test_reducer_command_returns_one_on_missing_file():
    rc = reducer_command(_args(file="/no/such/file.txt"), out=StringIO(), err=StringIO())
    assert rc == 1


def test_build_subparser_registers_reduce():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    _build_subparser(subs)
    parsed = root.parse_args(["reduce", "--max-stdlib", "5"])
    assert parsed.max_stdlib == 5
