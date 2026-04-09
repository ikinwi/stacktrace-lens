"""Tests for stacktrace_lens.filters."""

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.filters import FilterOptions, filter_frames


def _make_trace(*filenames: str) -> StackTrace:
    frames = [
        Frame(filename=fn, lineno=i + 1, function=f"fn_{i}", source_line="pass")
        for i, fn in enumerate(filenames)
    ]
    return StackTrace(
        frames=frames,
        exception_type="ValueError",
        exception_message="bad value",
    )


def test_filter_returns_stacktrace():
    trace = _make_trace("/app/main.py")
    result = filter_frames(trace, FilterOptions())
    assert isinstance(result, StackTrace)


def test_no_options_keeps_all_frames():
    trace = _make_trace("/app/a.py", "/app/b.py", "/app/c.py")
    result = filter_frames(trace, FilterOptions())
    assert len(result.frames) == 3


def test_exclude_pattern_removes_matching_frames():
    trace = _make_trace("/app/main.py", "/app/utils.py", "/vendor/lib.py")
    opts = FilterOptions(exclude_patterns=["/vendor/*"])
    result = filter_frames(trace, opts)
    assert len(result.frames) == 2
    assert all("/vendor/" not in f.filename for f in result.frames)


def test_include_only_pattern_keeps_only_matching():
    trace = _make_trace("/app/main.py", "/app/utils.py", "/vendor/lib.py")
    opts = FilterOptions(include_only_patterns=["/app/*"])
    result = filter_frames(trace, opts)
    assert len(result.frames) == 2
    assert all(f.filename.startswith("/app/") for f in result.frames)


def test_exclude_stdlib_removes_stdlib_frames():
    trace = _make_trace(
        "/app/main.py",
        "/usr/lib/python3.11/traceback.py",
        "/usr/lib/python3.11/site-packages/requests/api.py",
    )
    opts = FilterOptions(exclude_stdlib=True)
    result = filter_frames(trace, opts)
    assert len(result.frames) == 1
    assert result.frames[0].filename == "/app/main.py"


def test_max_frames_limits_output():
    trace = _make_trace("/a.py", "/b.py", "/c.py", "/d.py", "/e.py")
    opts = FilterOptions(max_frames=3)
    result = filter_frames(trace, opts)
    assert len(result.frames) == 3


def test_max_frames_keeps_last_frames():
    trace = _make_trace("/a.py", "/b.py", "/c.py")
    opts = FilterOptions(max_frames=2)
    result = filter_frames(trace, opts)
    assert result.frames[0].filename == "/b.py"
    assert result.frames[1].filename == "/c.py"


def test_exception_metadata_preserved():
    trace = _make_trace("/app/main.py")
    opts = FilterOptions(exclude_patterns=["/app/*"])
    result = filter_frames(trace, opts)
    assert result.exception_type == "ValueError"
    assert result.exception_message == "bad value"


def test_combined_options():
    trace = _make_trace(
        "/app/a.py",
        "/vendor/v.py",
        "/app/b.py",
        "/app/c.py",
    )
    opts = FilterOptions(
        exclude_patterns=["/vendor/*"],
        max_frames=2,
    )
    result = filter_frames(trace, opts)
    assert len(result.frames) == 2
    assert all("/vendor/" not in f.filename for f in result.frames)
