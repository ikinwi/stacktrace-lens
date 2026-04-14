"""Tests for stacktrace_lens.squasher."""
from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.squasher import (
    SquashReport,
    SquashedFrame,
    format_squash,
    squash_trace,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, context=None)


def _trace(*frames: Frame) -> StackTrace:
    return StackTrace(
        exception_type="ValueError",
        exception_message="bad value",
        frames=list(frames),
    )


# ---------------------------------------------------------------------------
# SquashReport
# ---------------------------------------------------------------------------

def test_squash_returns_squash_report():
    report = squash_trace(_trace(_frame()))
    assert isinstance(report, SquashReport)


def test_original_count_matches_input():
    t = _trace(_frame(), _frame(lineno=20), _frame(lineno=30))
    report = squash_trace(t)
    assert report.original_count == 3


def test_no_duplicates_preserves_all_frames():
    t = _trace(_frame(lineno=1), _frame(lineno=2), _frame(lineno=3))
    report = squash_trace(t)
    assert report.squashed_count == 3
    assert report.removed_count == 0


def test_consecutive_duplicates_merged():
    dup = _frame(lineno=5)
    t = _trace(dup, dup, dup)
    report = squash_trace(t)
    assert report.squashed_count == 1
    assert report.removed_count == 2


def test_repeat_count_reflects_duplicates():
    dup = _frame(lineno=7)
    t = _trace(dup, dup, dup, dup)
    report = squash_trace(t)
    assert report.frames[0].repeat_count == 4


def test_non_consecutive_duplicates_not_merged():
    a = _frame(lineno=1)
    b = _frame(lineno=2)
    t = _trace(a, b, a)  # a appears twice but not consecutively
    report = squash_trace(t)
    assert report.squashed_count == 3


def test_mixed_sequence():
    a = _frame(lineno=1)
    b = _frame(lineno=2)
    t = _trace(a, a, b, b, b, a)
    report = squash_trace(t)
    assert report.squashed_count == 3
    assert report.frames[0].repeat_count == 2
    assert report.frames[1].repeat_count == 3
    assert report.frames[2].repeat_count == 1


def test_empty_trace_produces_empty_report():
    t = StackTrace(exception_type="E", exception_message="m", frames=[])
    report = squash_trace(t)
    assert report.squashed_count == 0
    assert report.original_count == 0


def test_frames_are_squashed_frame_instances():
    t = _trace(_frame())
    report = squash_trace(t)
    assert all(isinstance(f, SquashedFrame) for f in report.frames)


def test_summary_line_is_string():
    report = squash_trace(_trace(_frame(), _frame()))
    assert isinstance(report.summary_line(), str)


def test_format_squash_returns_string():
    report = squash_trace(_trace(_frame()))
    assert isinstance(format_squash(report), str)


def test_format_squash_contains_summary():
    report = squash_trace(_trace(_frame()))
    result = format_squash(report)
    assert report.summary_line() in result
