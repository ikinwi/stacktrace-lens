"""Tests for stacktrace_lens.transformer"""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.transformer import (
    TransformRule,
    TransformedFrame,
    TransformReport,
    transform_trace,
)


def _frame(filename: str = "/app/module.py", lineno: int = 10,
           function: str = "do_thing") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# --- TransformReport --------------------------------------------------------

def test_transform_returns_report():
    report = transform_trace(_trace(_frame()))
    assert isinstance(report, TransformReport)


def test_report_frames_are_transformed_frames():
    report = transform_trace(_trace(_frame()))
    assert all(isinstance(f, TransformedFrame) for f in report.frames)


def test_frame_count_matches_trace():
    trace = _trace(_frame(), _frame(), _frame())
    report = transform_trace(trace)
    assert report.count == 3


def test_no_rules_zero_modified():
    report = transform_trace(_trace(_frame(), _frame()))
    assert report.modified_count == 0


def test_rule_modifies_filename():
    rule = TransformRule(
        name="strip-app",
        apply=lambda f: Frame(
            filename=f.filename.replace("/app/", ""),
            lineno=f.lineno,
            function=f.function,
            context=f.context,
        ),
    )
    report = transform_trace(_trace(_frame("/app/module.py")), [rule])
    assert report.frames[0].result.filename == "module.py"


def test_rule_records_applied_name():
    rule = TransformRule(
        name="my-rule",
        apply=lambda f: Frame(
            filename="changed.py", lineno=f.lineno,
            function=f.function, context=f.context,
        ),
    )
    report = transform_trace(_trace(_frame()), [rule])
    assert "my-rule" in report.frames[0].rules_applied


def test_unchanged_frame_has_empty_rules_applied():
    rule = TransformRule(name="noop", apply=lambda f: f)
    report = transform_trace(_trace(_frame()), [rule])
    assert report.frames[0].rules_applied == []


def test_multiple_rules_all_applied():
    r1 = TransformRule(
        name="r1",
        apply=lambda f: Frame("/new.py", f.lineno, f.function, f.context),
    )
    r2 = TransformRule(
        name="r2",
        apply=lambda f: Frame(f.filename, f.lineno, "renamed", f.context),
    )
    report = transform_trace(_trace(_frame()), [r1, r2])
    tf = report.frames[0]
    assert tf.result.filename == "/new.py"
    assert tf.result.function == "renamed"
    assert set(tf.rules_applied) == {"r1", "r2"}


def test_modified_count_correct():
    rule = TransformRule(
        name="r",
        apply=lambda f: Frame("x.py", f.lineno, f.function, f.context) if f.filename == "/app/module.py" else f,
    )
    trace = _trace(_frame("/app/module.py"), _frame("/other.py"))
    report = transform_trace(trace, [rule])
    assert report.modified_count == 1


def test_to_trace_returns_stack_trace():
    report = transform_trace(_trace(_frame()))
    result = report.to_trace()
    assert isinstance(result, StackTrace)


def test_to_trace_preserves_exception_info():
    trace = _trace(_frame())
    report = transform_trace(trace)
    result = report.to_trace()
    assert result.exception_type == "ValueError"
    assert result.exception_message == "bad value"


def test_summary_line_returns_string():
    report = transform_trace(_trace(_frame()))
    assert isinstance(report.summary_line(), str)


def test_summary_line_contains_counts():
    rule = TransformRule(
        name="r",
        apply=lambda f: Frame("x.py", f.lineno, f.function, f.context),
    )
    report = transform_trace(_trace(_frame(), _frame()), [rule])
    line = report.summary_line()
    assert "2" in line
