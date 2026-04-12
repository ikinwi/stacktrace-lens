"""Tests for stacktrace_lens.denoiser."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.denoiser import (
    DenoiseOptions,
    DenoiseReport,
    denoise_trace,
)


def _frame(filename: str, function: str = "fn", lineno: int = 1) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="RuntimeError",
        exception_message="boom",
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# Basic return type
# ---------------------------------------------------------------------------

def test_denoise_returns_report():
    t = _trace(_frame("/app/main.py"))
    report = denoise_trace(t)
    assert isinstance(report, DenoiseReport)


def test_report_trace_is_stack_trace():
    t = _trace(_frame("/app/main.py"))
    report = denoise_trace(t)
    assert isinstance(report.trace, StackTrace)


# ---------------------------------------------------------------------------
# Clean traces are left untouched
# ---------------------------------------------------------------------------

def test_no_noise_keeps_all_frames():
    t = _trace(_frame("/app/main.py"), _frame("/app/utils.py"))
    report = denoise_trace(t)
    assert report.kept_count == 2
    assert report.removed_count == 0


def test_original_count_matches_input():
    frames = [_frame(f"/app/f{i}.py") for i in range(5)]
    t = _trace(*frames)
    report = denoise_trace(t)
    assert report.original_count == 5


# ---------------------------------------------------------------------------
# Built-in noise patterns
# ---------------------------------------------------------------------------

def test_frozen_importlib_frame_removed():
    t = _trace(
        _frame("/app/main.py"),
        _frame("<frozen importlib._bootstrap>"),
    )
    report = denoise_trace(t)
    assert report.removed_count == 1
    assert report.kept_count == 1


def test_pytest_frame_removed():
    t = _trace(
        _frame("/app/main.py"),
        _frame("/usr/lib/python3/dist-packages/_pytest/runner.py"),
    )
    report = denoise_trace(t)
    assert report.removed_count == 1


def test_unittest_frame_removed():
    t = _trace(
        _frame("/app/main.py"),
        _frame("/usr/lib/python3.11/unittest/case.py"),
    )
    report = denoise_trace(t)
    assert report.removed_count == 1


# ---------------------------------------------------------------------------
# Extra patterns
# ---------------------------------------------------------------------------

def test_extra_pattern_removes_matching_frame():
    opts = DenoiseOptions(extra_patterns=[r"celery"])
    t = _trace(
        _frame("/app/main.py"),
        _frame("/site-packages/celery/app/trace.py"),
    )
    report = denoise_trace(t, opts)
    assert report.removed_count == 1


# ---------------------------------------------------------------------------
# Fallback when everything is noise
# ---------------------------------------------------------------------------

def test_all_noise_with_fallback_keeps_all():
    t = _trace(_frame("<frozen importlib>"), _frame("<frozen abc>"))
    opts = DenoiseOptions(keep_if_only_noise=True)
    report = denoise_trace(t, opts)
    assert report.kept_count == 2
    assert report.removed_count == 0


def test_all_noise_without_fallback_removes_all():
    t = _trace(_frame("<frozen importlib>"), _frame("<frozen abc>"))
    opts = DenoiseOptions(keep_if_only_noise=False)
    report = denoise_trace(t, opts)
    assert report.kept_count == 0
    assert report.removed_count == 2


# ---------------------------------------------------------------------------
# Summary line
# ---------------------------------------------------------------------------

def test_summary_line_is_string():
    t = _trace(_frame("/app/main.py"))
    report = denoise_trace(t)
    assert isinstance(report.summary_line(), str)


def test_summary_line_contains_counts():
    t = _trace(
        _frame("/app/main.py"),
        _frame("<frozen importlib>"),
    )
    report = denoise_trace(t)
    line = report.summary_line()
    assert "2" in line  # original
    assert "1" in line  # kept or removed
