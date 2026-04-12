"""Tests for stacktrace_lens.resolver."""

from __future__ import annotations

import os
import tempfile

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.resolver import (
    ResolveOptions,
    ResolveReport,
    ResolvedFrame,
    format_resolve_report,
    resolve_frames,
)


def _frame(filename: str, lineno: int = 1, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*filenames: str) -> StackTrace:
    frames = [_frame(f) for f in filenames]
    return StackTrace(exception_type="ValueError", message="oops", frames=frames)


def test_resolve_frames_returns_report():
    trace = _trace("app.py")
    report = resolve_frames(trace)
    assert isinstance(report, ResolveReport)


def test_report_frames_are_resolved_frames():
    trace = _trace("app.py")
    report = resolve_frames(trace)
    assert all(isinstance(f, ResolvedFrame) for f in report.frames)


def test_frame_count_matches_trace():
    trace = _trace("a.py", "b.py", "c.py")
    report = resolve_frames(trace)
    assert len(report.frames) == 3


def test_absolute_existing_path_is_resolved(tmp_path):
    src = tmp_path / "module.py"
    src.write_text("x = 1\n")
    trace = _trace(str(src))
    report = resolve_frames(trace, ResolveOptions())
    assert report.frames[0].was_resolved is True
    assert report.resolved_count == 1


def test_absolute_missing_path_is_not_resolved():
    trace = _trace("/nonexistent/path/file.py")
    report = resolve_frames(trace)
    assert report.frames[0].was_resolved is False
    assert report.unresolved_count == 1


def test_relative_path_resolved_via_search_path(tmp_path):
    src = tmp_path / "utils.py"
    src.write_text("pass\n")
    trace = _trace("utils.py")
    options = ResolveOptions(search_paths=[str(tmp_path)])
    report = resolve_frames(trace, options)
    assert report.frames[0].was_resolved is True
    assert str(tmp_path) in report.frames[0].resolved_filename


def test_relative_path_not_found_stays_unresolved():
    trace = _trace("missing_module.py")
    options = ResolveOptions(search_paths=["/tmp"])
    report = resolve_frames(trace, options)
    assert report.frames[0].was_resolved is False
    assert report.frames[0].resolved_filename == "missing_module.py"


def test_resolved_count_and_unresolved_count_sum_to_total(tmp_path):
    existing = tmp_path / "real.py"
    existing.write_text("")
    trace = _trace(str(existing), "/ghost/file.py")
    report = resolve_frames(trace)
    assert report.resolved_count + report.unresolved_count == len(report.frames)


def test_resolved_frame_str_contains_filename(tmp_path):
    src = tmp_path / "main.py"
    src.write_text("")
    trace = _trace(str(src))
    report = resolve_frames(trace)
    result = str(report.frames[0])
    assert "main.py" in result


def test_format_resolve_report_returns_string():
    trace = _trace("app.py")
    report = resolve_frames(trace)
    output = format_resolve_report(report)
    assert isinstance(output, str)


def test_format_resolve_report_contains_counts():
    trace = _trace("app.py")
    report = resolve_frames(trace)
    output = format_resolve_report(report)
    assert "Resolved" in output
    assert "Unresolved" in output


def test_search_paths_stored_in_report(tmp_path):
    trace = _trace("x.py")
    options = ResolveOptions(search_paths=[str(tmp_path)])
    report = resolve_frames(trace, options)
    assert str(tmp_path) in report.search_paths
