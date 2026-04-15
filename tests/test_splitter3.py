"""Tests for stacktrace_lens.splitter3."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.splitter3 import (
    Partition,
    PartitionReport,
    _package_of,
    partition_trace,
)


def _frame(filename: str, function: str = "fn", lineno: int = 1) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# -- _package_of -----------------------------------------------------------

def test_package_of_simple_path():
    assert _package_of("myapp/models.py") == "myapp"


def test_package_of_deep_path():
    assert _package_of("site-packages/requests/adapters.py") == "site-packages"


def test_package_of_empty_string():
    assert _package_of("") == "<unknown>"


def test_package_of_windows_path():
    assert _package_of("myapp\\views.py") == "myapp"


def test_package_of_bare_filename():
    assert _package_of("script.py") == "script.py"


# -- partition_trace -------------------------------------------------------

def test_partition_trace_returns_report():
    t = _trace(_frame("app/main.py"))
    report = partition_trace(t)
    assert isinstance(report, PartitionReport)


def test_single_frame_one_partition():
    t = _trace(_frame("app/main.py"))
    report = partition_trace(t)
    assert report.count == 1


def test_same_package_merged():
    t = _trace(_frame("app/a.py"), _frame("app/b.py"))
    report = partition_trace(t)
    assert report.count == 1
    assert report.partitions[0].count == 2


def test_different_packages_split():
    t = _trace(_frame("app/a.py"), _frame("lib/x.py"))
    report = partition_trace(t)
    assert report.count == 2


def test_partition_packages_correct():
    t = _trace(_frame("app/a.py"), _frame("lib/x.py"), _frame("app/b.py"))
    report = partition_trace(t)
    assert [p.package for p in report.partitions] == ["app", "lib", "app"]


def test_empty_trace_produces_no_partitions():
    t = _trace()
    report = partition_trace(t)
    assert report.count == 0


def test_summary_line_contains_exception_type():
    t = _trace(_frame("app/a.py"))
    report = partition_trace(t)
    assert "ValueError" in report.summary_line


def test_summary_line_contains_partition_count():
    t = _trace(_frame("app/a.py"), _frame("lib/x.py"))
    report = partition_trace(t)
    assert "2" in report.summary_line


def test_partition_str_contains_package():
    p = Partition(package="myapp", frames=[_frame("myapp/x.py")])
    assert "myapp" in str(p)
