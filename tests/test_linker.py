"""Tests for stacktrace_lens/linker.py"""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.linker import (
    LinkOptions,
    LinkedFrame,
    LinkReport,
    _build_url,
    link_frames,
    format_links,
)


def _frame(filename: str = "/app/main.py", lineno: int = 10, func: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=func, source_line="pass")


def _trace(*frames: Frame) -> StackTrace:
    if not frames:
        frames = (_frame(),)  # type: ignore[assignment]
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# --- LinkReport ---

def test_link_frames_returns_report():
    report = link_frames(_trace())
    assert isinstance(report, LinkReport)


def test_total_matches_frame_count():
    t = _trace(_frame(), _frame("/app/utils.py", 5))
    report = link_frames(t)
    assert report.total == 2


def test_linked_count_excludes_unknown_files():
    t = _trace(_frame("<unknown>"), _frame("/app/main.py"))
    report = link_frames(t)
    assert report.linked_count == 1


def test_file_scheme_url_format():
    f = _frame("/app/main.py", 42)
    url = _build_url(f, LinkOptions(scheme="file"))
    assert url == "file:///app/main.py#42"


def test_vscode_scheme_url_format():
    f = _frame("/app/main.py", 7)
    url = _build_url(f, LinkOptions(scheme="vscode"))
    assert url == "vscode://file//app/main.py:7"


def test_pycharm_scheme_url_format():
    f = _frame("/app/main.py", 3)
    url = _build_url(f, LinkOptions(scheme="pycharm"))
    assert url == "idea://open?file=/app/main.py&line=3"


def test_idea_scheme_same_as_pycharm():
    f = _frame("/app/main.py", 3)
    assert _build_url(f, LinkOptions(scheme="idea")) == _build_url(f, LinkOptions(scheme="pycharm"))


def test_unknown_scheme_returns_none():
    f = _frame("/app/main.py", 1)
    assert _build_url(f, LinkOptions(scheme="sublime")) is None  # type: ignore[arg-type]


def test_base_path_stripped_from_url():
    f = _frame("/home/user/project/src/main.py", 5)
    url = _build_url(f, LinkOptions(scheme="file", base_path="/home/user/project"))
    assert "src/main.py" in url
    assert "/home/user/project" not in url


def test_none_filename_returns_none():
    f = Frame(filename=None, lineno=1, function="f", source_line="")
    assert _build_url(f, LinkOptions()) is None


def test_linked_frame_str_with_url():
    f = _frame("/app/main.py", 10)
    lf = LinkedFrame(frame=f, url="file:///app/main.py#10")
    assert "->" in str(lf)


def test_linked_frame_str_without_url():
    f = _frame("<unknown>", 0)
    lf = LinkedFrame(frame=f, url=None)
    assert "->" not in str(lf)


def test_summary_line_contains_scheme():
    report = link_frames(_trace())
    assert "file" in report.summary_line()


def test_format_links_returns_string():
    report = link_frames(_trace())
    result = format_links(report)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_links_contains_summary():
    report = link_frames(_trace())
    result = format_links(report)
    assert report.summary_line() in result
