"""Tests for stacktrace_lens.mapper."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.mapper import (
    MappedFrame,
    MapReport,
    map_trace,
    format_map,
    _module_from_path,
    _package_from_path,
)


def _frame(filename: str = "myapp/utils.py", lineno: int = 10,
           function: str = "helper") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context="x = 1")


def _trace(*frames: Frame, exc: str = "ValueError",
           msg: str = "bad value") -> StackTrace:
    return StackTrace(
        exception_type=exc,
        exception_message=msg,
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# map_trace return type
# ---------------------------------------------------------------------------

def test_map_trace_returns_map_report():
    report = map_trace(_trace(_frame()))
    assert isinstance(report, MapReport)


def test_map_report_frames_are_mapped_frames():
    report = map_trace(_trace(_frame()))
    assert all(isinstance(f, MappedFrame) for f in report.frames)


def test_frame_count_matches_trace():
    report = map_trace(_trace(_frame(), _frame("other/mod.py")))
    assert report.count == 2


# ---------------------------------------------------------------------------
# exception metadata preserved
# ---------------------------------------------------------------------------

def test_exception_type_preserved():
    report = map_trace(_trace(_frame(), exc="KeyError"))
    assert report.exception_type == "KeyError"


def test_exception_message_preserved():
    report = map_trace(_trace(_frame(), msg="missing key"))
    assert report.exception_message == "missing key"


# ---------------------------------------------------------------------------
# module / package derivation
# ---------------------------------------------------------------------------

def test_module_from_py_path():
    assert _module_from_path("myapp/utils.py") == "myapp.utils"


def test_module_strips_py_extension():
    result = _module_from_path("pkg/sub/mod.py")
    assert not result.endswith(".py")


def test_package_from_nested_path():
    assert _package_from_path("myapp/utils.py") == "myapp"


def test_package_from_flat_path():
    assert _package_from_path("utils.py") == "utils"


# ---------------------------------------------------------------------------
# packages() helper
# ---------------------------------------------------------------------------

def test_packages_returns_unique_list():
    frames = [
        _frame("myapp/a.py"),
        _frame("myapp/b.py"),
        _frame("other/c.py"),
    ]
    report = map_trace(_trace(*frames))
    pkgs = report.packages()
    assert len(pkgs) == 2
    assert "myapp" in pkgs
    assert "other" in pkgs


# ---------------------------------------------------------------------------
# summary_line
# ---------------------------------------------------------------------------

def test_summary_line_contains_exception_type():
    report = map_trace(_trace(_frame(), exc="RuntimeError"))
    assert "RuntimeError" in report.summary_line()


def test_summary_line_contains_frame_count():
    report = map_trace(_trace(_frame(), _frame("x/y.py")))
    assert "2" in report.summary_line()


# ---------------------------------------------------------------------------
# format_map
# ---------------------------------------------------------------------------

def test_format_map_returns_string():
    report = map_trace(_trace(_frame()))
    assert isinstance(format_map(report), str)


def test_format_map_contains_filename():
    report = map_trace(_trace(_frame("myapp/utils.py")))
    output = format_map(report)
    assert "myapp/utils.py" in output or "myapp" in output
