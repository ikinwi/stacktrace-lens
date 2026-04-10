"""Tests for stacktrace_lens.watchdog."""

from __future__ import annotations

import textwrap
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.watchdog import (
    WatchAlert,
    WatchOptions,
    _iter_raw_traces,
    tail_file,
)

_RAW = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: something went wrong
""").strip()

_TWO_TRACES = _RAW + "\n\n" + _RAW


def test_iter_raw_traces_single():
    blocks = list(_iter_raw_traces(_RAW))
    assert len(blocks) == 1
    assert "Traceback" in blocks[0]


def test_iter_raw_traces_multiple():
    blocks = list(_iter_raw_traces(_TWO_TRACES))
    assert len(blocks) == 2


def test_iter_raw_traces_no_trace():
    blocks = list(_iter_raw_traces("Nothing to see here."))
    assert blocks == []


def test_watch_alert_fields():
    trace = parse_stacktrace(_RAW)
    from stacktrace_lens.severity import score_trace
    severity = score_trace(trace)
    alert = WatchAlert(trace=trace, severity=severity, byte_offset=0)
    assert alert.trace is trace
    assert alert.severity is severity
    assert alert.byte_offset == 0


def test_tail_file_raises_on_missing(tmp_path):
    opts = WatchOptions(max_alerts=0)
    with pytest.raises(FileNotFoundError):
        tail_file(tmp_path / "ghost.log", opts, lambda a: None)


def test_tail_file_emits_alert(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("")          # start empty so seen_bytes == 0

    collected: list[WatchAlert] = []
    opts = WatchOptions(poll_interval=0.05, max_alerts=1)

    # Append a trace *after* watchdog has noted the initial size
    import threading

    def _writer():
        time.sleep(0.08)
        with log.open("a") as fh:
            fh.write(_RAW + "\n\n")

    t = threading.Thread(target=_writer, daemon=True)
    t.start()
    tail_file(log, opts, collected.append)
    t.join(timeout=2)

    assert len(collected) == 1
    assert collected[0].trace.exception_type == "ValueError"


def test_tail_file_min_severity_filters(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("")

    collected: list[WatchAlert] = []
    # Use an impossibly high score so nothing passes
    opts = WatchOptions(poll_interval=0.05, max_alerts=1, min_severity_score=9999)

    import threading

    def _writer():
        time.sleep(0.08)
        with log.open("a") as fh:
            fh.write(_RAW + "\n\n")
        # Write a second trace to trigger max_alerts via a different path;
        # since none pass the filter, we just let the thread finish.

    t = threading.Thread(target=_writer, daemon=True)
    t.start()
    # Watchdog will never hit max_alerts; interrupt manually after short wait
    import signal

    def _stop(sig, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGALRM, _stop)
        signal.alarm(1)
        tail_file(log, opts, collected.append)
    except KeyboardInterrupt:
        pass
    finally:
        signal.alarm(0)
    t.join(timeout=2)

    assert collected == []
