"""Tests for stacktrace_lens.patcher."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.patcher import (
    PatchRule,
    PatchedFrame,
    PatchReport,
    patch_trace,
)


def _frame(filename="app/main.py", lineno=10, function_name="run", source_line="") -> Frame:
    return Frame(filename=filename, lineno=lineno, function_name=function_name, source_line=source_line)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# ── basic return types ────────────────────────────────────────────────────────

def test_patch_trace_returns_report():
    report = patch_trace(_trace(_frame()), [])
    assert isinstance(report, PatchReport)


def test_patch_report_frames_are_patched_frames():
    report = patch_trace(_trace(_frame()), [])
    assert all(isinstance(f, PatchedFrame) for f in report.patched_frames)


def test_frame_count_matches_trace():
    trace = _trace(_frame(), _frame(), _frame())
    report = patch_trace(trace, [])
    assert report.count == 3


# ── no rules keeps frames unchanged ──────────────────────────────────────────

def test_no_rules_nothing_patched():
    report = patch_trace(_trace(_frame()), [])
    assert report.patched_count == 0


def test_no_rules_was_patched_false():
    report = patch_trace(_trace(_frame()), [])
    assert report.patched_frames[0].was_patched is False


# ── filename_contains matching ────────────────────────────────────────────────

def test_filename_match_patches_frame():
    rule = PatchRule(filename_contains="main", replace_filename="src/main.py")
    report = patch_trace(_trace(_frame(filename="app/main.py")), [rule])
    assert report.patched_frames[0].was_patched is True
    assert report.patched_frames[0].patched.filename == "src/main.py"


def test_filename_no_match_skips_frame():
    rule = PatchRule(filename_contains="other", replace_filename="src/other.py")
    report = patch_trace(_trace(_frame(filename="app/main.py")), [rule])
    assert report.patched_frames[0].was_patched is False


# ── function_name matching ────────────────────────────────────────────────────

def test_function_name_match_patches_frame():
    rule = PatchRule(function_name="run", replace_function="start")
    report = patch_trace(_trace(_frame(function_name="run")), [rule])
    assert report.patched_frames[0].patched.function_name == "start"


def test_function_name_no_match_skips_frame():
    rule = PatchRule(function_name="other", replace_function="start")
    report = patch_trace(_trace(_frame(function_name="run")), [rule])
    assert report.patched_frames[0].was_patched is False


# ── line_offset ───────────────────────────────────────────────────────────────

def test_line_offset_applied():
    rule = PatchRule(filename_contains="main", line_offset=5)
    report = patch_trace(_trace(_frame(lineno=10)), [rule])
    assert report.patched_frames[0].patched.lineno == 15


def test_line_offset_negative():
    rule = PatchRule(filename_contains="main", line_offset=-3)
    report = patch_trace(_trace(_frame(lineno=10)), [rule])
    assert report.patched_frames[0].patched.lineno == 7


# ── patched_count ─────────────────────────────────────────────────────────────

def test_patched_count_reflects_matches():
    rule = PatchRule(filename_contains="main", replace_filename="x.py")
    frames = [_frame("app/main.py"), _frame("lib/util.py"), _frame("app/main.py")]
    report = patch_trace(_trace(*frames), [rule])
    assert report.patched_count == 2


# ── as_trace ──────────────────────────────────────────────────────────────────

def test_as_trace_returns_stack_trace():
    from stacktrace_lens.parser import StackTrace as ST
    report = patch_trace(_trace(_frame()), [])
    result = report.as_trace()
    assert isinstance(result, ST)


def test_as_trace_preserves_exception_type():
    report = patch_trace(_trace(_frame()), [])
    assert report.as_trace().exception_type == "ValueError"


# ── summary_line ──────────────────────────────────────────────────────────────

def test_summary_line_is_string():
    report = patch_trace(_trace(_frame()), [])
    assert isinstance(report.summary_line(), str)


def test_summary_line_contains_exception_type():
    report = patch_trace(_trace(_frame()), [])
    assert "ValueError" in report.summary_line()


# ── __str__ on PatchedFrame ───────────────────────────────────────────────────

def test_patched_frame_str_contains_patched_label():
    rule = PatchRule(filename_contains="main", replace_filename="new.py")
    report = patch_trace(_trace(_frame()), [rule])
    assert "[patched]" in str(report.patched_frames[0])


def test_unpatched_frame_str_no_patched_label():
    report = patch_trace(_trace(_frame(filename="lib/other.py")), [
        PatchRule(filename_contains="main", replace_filename="new.py")
    ])
    assert "[patched]" not in str(report.patched_frames[0])
