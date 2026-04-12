"""Tests for stacktrace_lens.mutator."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.mutator import (
    MutateOptions,
    MutatedFrame,
    MutateReport,
    mutate_trace,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "main") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context="pass")


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames) or [_frame()],
    )


def test_mutate_returns_report():
    report = mutate_trace(_trace())
    assert isinstance(report, MutateReport)


def test_report_frames_are_mutated_frames():
    report = mutate_trace(_trace(_frame(), _frame()))
    assert all(isinstance(f, MutatedFrame) for f in report.frames)


def test_frame_count_matches_trace():
    t = _trace(_frame(), _frame(), _frame())
    report = mutate_trace(t)
    assert report.count == 3


def test_no_options_no_changes():
    report = mutate_trace(_trace(_frame()))
    assert report.changed_count == 0


def test_strip_line_numbers_sets_zero():
    opts = MutateOptions(strip_line_numbers=True)
    report = mutate_trace(_trace(_frame(lineno=42)), opts)
    assert report.frames[0].result.lineno == 0


def test_strip_line_numbers_marks_changed():
    opts = MutateOptions(strip_line_numbers=True)
    report = mutate_trace(_trace(_frame(lineno=5)), opts)
    assert report.frames[0].changed is True


def test_uppercase_filenames():
    opts = MutateOptions(uppercase_filenames=True)
    report = mutate_trace(_trace(_frame(filename="app.py")), opts)
    assert report.frames[0].result.filename == "APP.PY"


def test_uppercase_marks_changed():
    opts = MutateOptions(uppercase_filenames=True)
    report = mutate_trace(_trace(_frame(filename="app.py")), opts)
    assert report.frames[0].changed is True


def test_custom_transform_applied():
    def replace_fn(f: Frame) -> Frame:
        return Frame(filename=f.filename, lineno=f.lineno, function="replaced", context=f.context)

    opts = MutateOptions(custom_transforms=[replace_fn])
    report = mutate_trace(_trace(_frame(function="original")), opts)
    assert report.frames[0].result.function == "replaced"


def test_custom_transform_marks_changed():
    def noop(f: Frame) -> Frame:
        return Frame(filename="new.py", lineno=f.lineno, function=f.function, context=f.context)

    opts = MutateOptions(custom_transforms=[noop])
    report = mutate_trace(_trace(_frame(filename="old.py")), opts)
    assert report.frames[0].changed is True


def test_report_trace_is_stack_trace():
    from stacktrace_lens.parser import StackTrace
    report = mutate_trace(_trace())
    assert isinstance(report.trace, StackTrace)


def test_summary_line_contains_exception_type():
    report = mutate_trace(_trace())
    assert "ValueError" in report.summary_line()


def test_changed_count_in_summary():
    opts = MutateOptions(strip_line_numbers=True)
    report = mutate_trace(_trace(_frame(lineno=1), _frame(lineno=2)), opts)
    assert report.changed_count == 2
    assert "2/2" in report.summary_line()
