"""Tests for stacktrace_lens.renamer."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.renamer import (
    RenameRule,
    RenameReport,
    RenamedFrame,
    rename_frames,
)


def _frame(filename: str = "/app/src/module.py", function: str = "my_func") -> Frame:
    return Frame(filename=filename, lineno=10, function=function, source="x = 1")


def _trace(*frames: Frame) -> StackTrace:
    if not frames:
        frames = (_frame(),)
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# --- rename_frames return type ---

def test_rename_returns_report():
    report = rename_frames(_trace())
    assert isinstance(report, RenameReport)


def test_report_frames_are_renamed_frames():
    report = rename_frames(_trace())
    assert all(isinstance(f, RenamedFrame) for f in report.frames)


def test_frame_count_matches_trace():
    t = _trace(_frame(), _frame(), _frame())
    report = rename_frames(t)
    assert report.count == 3


# --- no rules keeps frames unchanged ---

def test_no_rules_no_rename():
    report = rename_frames(_trace())
    assert report.renamed_count == 0


def test_no_rules_filename_unchanged():
    f = _frame(filename="/app/foo.py")
    report = rename_frames(_trace(f))
    assert report.frames[0].frame.filename == "/app/foo.py"


# --- filename rule ---

def test_filename_rule_replaces_text():
    rule = RenameRule(find="/app/src", replace="/project")
    report = rename_frames(_trace(_frame(filename="/app/src/module.py")), [rule])
    assert report.frames[0].frame.filename == "/project/module.py"


def test_filename_rule_marks_renamed():
    rule = RenameRule(find="/app/src", replace="/project")
    report = rename_frames(_trace(_frame(filename="/app/src/module.py")), [rule])
    assert report.frames[0].renamed is True


def test_filename_rule_no_match_not_renamed():
    rule = RenameRule(find="/other", replace="/project")
    report = rename_frames(_trace(_frame(filename="/app/src/module.py")), [rule])
    assert report.frames[0].renamed is False


# --- function rule ---

def test_function_rule_replaces_text():
    rule = RenameRule(find="my_func", replace="renamed_func", target="function")
    report = rename_frames(_trace(_frame(function="my_func")), [rule])
    assert report.frames[0].frame.function == "renamed_func"


def test_function_rule_does_not_touch_filename():
    rule = RenameRule(find="module", replace="replaced", target="function")
    report = rename_frames(_trace(_frame(filename="/app/module.py", function="module_fn")), [rule])
    assert "/app/module.py" == report.frames[0].frame.filename


# --- 'both' target ---

def test_both_target_renames_filename_and_function():
    rule = RenameRule(find="app", replace="svc", target="both")
    f = _frame(filename="/app/main.py", function="app_start")
    report = rename_frames(_trace(f), [rule])
    rf = report.frames[0]
    assert rf.frame.filename == "/svc/main.py"
    assert rf.frame.function == "svc_start"


# --- summary ---

def test_summary_line_contains_counts():
    rule = RenameRule(find="/app", replace="/svc")
    report = rename_frames(_trace(_frame(filename="/app/foo.py")), [rule])
    summary = report.summary_line()
    assert "1/1" in summary


def test_rules_applied_count():
    rules = [RenameRule(find="a", replace="b"), RenameRule(find="c", replace="d")]
    report = rename_frames(_trace(), rules)
    assert report.rules_applied == 2


# --- str representation ---

def test_renamed_frame_str_contains_filename():
    rule = RenameRule(find="/app", replace="/svc")
    report = rename_frames(_trace(_frame(filename="/app/foo.py")), [rule])
    assert "/svc/foo.py" in str(report.frames[0])


def test_renamed_frame_str_contains_renamed_tag():
    rule = RenameRule(find="/app", replace="/svc")
    report = rename_frames(_trace(_frame(filename="/app/foo.py")), [rule])
    assert "[renamed]" in str(report.frames[0])
