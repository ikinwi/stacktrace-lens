"""Tests for stacktrace_lens.stats and stacktrace_lens.stats_cmd."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.stats import StackTraceStats, compute_stats, format_stats
from stacktrace_lens.stats_cmd import stats_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_TRACE = (
    "Traceback (most recent call last):\n"
    '  File "app/main.py", line 10, in run\n'
    "    do_thing()\n"
    '  File "app/utils.py", line 42, in do_thing\n'
    "    helper()\n"
    '  File "app/utils.py", line 55, in helper\n'
    "    raise ZeroDivisionError('oops')\n"
    "ZeroDivisionError: oops"
)


def _make_trace() -> StackTrace:
    frames = [
        Frame(filename="app/main.py", lineno=10, function="run", context="do_thing()"),
        Frame(filename="app/utils.py", lineno=42, function="do_thing", context="helper()"),
        Frame(filename="app/utils.py", lineno=55, function="helper", context="raise ZeroDivisionError('oops')"),
    ]
    return StackTrace(frames=frames, exception_type="ZeroDivisionError", message="oops")


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

def test_compute_stats_returns_instance():
    stats = compute_stats(_make_trace())
    assert isinstance(stats, StackTraceStats)


def test_total_frames():
    assert compute_stats(_make_trace()).total_frames == 3


def test_unique_files():
    assert compute_stats(_make_trace()).unique_files == 2


def test_unique_functions():
    assert compute_stats(_make_trace()).unique_functions == 3


def test_exception_type_preserved():
    assert compute_stats(_make_trace()).exception_type == "ZeroDivisionError"


def test_top_file_is_most_common():
    # app/utils.py appears twice
    assert compute_stats(_make_trace()).top_file == "app/utils.py"


def test_packages_counted():
    stats = compute_stats(_make_trace())
    assert "app" in stats.packages
    assert stats.packages["app"] == 3


# ---------------------------------------------------------------------------
# format_stats
# ---------------------------------------------------------------------------

def test_format_stats_returns_string():
    assert isinstance(format_stats(compute_stats(_make_trace())), str)


def test_format_stats_contains_exception_type():
    output = format_stats(compute_stats(_make_trace()))
    assert "ZeroDivisionError" in output


def test_format_stats_contains_frame_count():
    output = format_stats(compute_stats(_make_trace()))
    assert "3" in output


# ---------------------------------------------------------------------------
# stats_command
# ---------------------------------------------------------------------------

def test_stats_command_returns_zero_on_valid_input():
    assert stats_command(argv=[], stdin_text=SAMPLE_TRACE) == 0


def test_stats_command_returns_one_on_empty_input():
    assert stats_command(argv=[], stdin_text="") == 1


def test_stats_command_json_flag(capsys):
    rc = stats_command(argv=["--json"], stdin_text=SAMPLE_TRACE)
    assert rc == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["exception_type"] == "ZeroDivisionError"
    assert data["total_frames"] == 3


def test_stats_command_plain_output(capsys):
    rc = stats_command(argv=[], stdin_text=SAMPLE_TRACE)
    assert rc == 0
    out = capsys.readouterr().out
    assert "ZeroDivisionError" in out


def test_stats_command_missing_file_returns_one(tmp_path):
    rc = stats_command(argv=[str(tmp_path / "nonexistent.txt")], stdin_text=None)
    assert rc == 1
