"""Tests for stacktrace_lens.grouper."""

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.grouper import FrameGroup, group_frames, summarise_groups


def _frame(filename: str, fn: str = "f") -> Frame:
    return Frame(filename=filename, lineno=1, function=fn, source_line="pass")


def _trace(*filenames: str) -> StackTrace:
    return StackTrace(
        frames=[_frame(fn) for fn in filenames],
        exception_type="RuntimeError",
        exception_message="oops",
    )


def test_group_frames_returns_list():
    trace = _trace("/app/main.py")
    result = group_frames(trace)
    assert isinstance(result, list)


def test_single_frame_produces_one_group():
    trace = _trace("/app/main.py")
    groups = group_frames(trace)
    assert len(groups) == 1


def test_consecutive_same_package_merged():
    trace = _trace("/app/a.py", "/app/b.py", "/app/c.py")
    groups = group_frames(trace)
    assert len(groups) == 1
    assert groups[0].count == 3


def test_different_packages_separate_groups():
    trace = _trace("/app/main.py", "/vendor/lib.py", "/app/utils.py")
    groups = group_frames(trace)
    assert len(groups) == 3


def test_group_label_from_parent_dir():
    trace = _trace("/myproject/core/runner.py")
    groups = group_frames(trace)
    assert groups[0].label == "core"


def test_site_packages_uses_package_name():
    trace = _trace("/usr/lib/python3.11/site-packages/requests/models.py")
    groups = group_frames(trace)
    assert groups[0].label == "requests"


def test_group_frames_preserves_frame_order():
    trace = _trace("/a/x.py", "/a/y.py", "/b/z.py")
    groups = group_frames(trace)
    assert groups[0].frames[0].filename == "/a/x.py"
    assert groups[0].frames[1].filename == "/a/y.py"
    assert groups[1].frames[0].filename == "/b/z.py"


def test_summarise_groups_returns_tuples():
    trace = _trace("/app/a.py", "/app/b.py", "/other/c.py")
    groups = group_frames(trace)
    summary = summarise_groups(groups)
    assert isinstance(summary, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in summary)


def test_summarise_groups_counts():
    trace = _trace("/app/a.py", "/app/b.py", "/other/c.py")
    groups = group_frames(trace)
    summary = summarise_groups(groups)
    assert summary[0][1] == 2
    assert summary[1][1] == 1


def test_empty_trace_produces_no_groups():
    trace = StackTrace(frames=[], exception_type="E", exception_message="m")
    groups = group_frames(trace)
    assert groups == []
