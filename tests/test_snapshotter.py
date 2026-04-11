"""Tests for stacktrace_lens.snapshotter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.snapshotter import (
    Snapshot,
    dump_snapshot,
    dump_snapshots,
    load_snapshot,
    load_snapshots,
    snapshot_from_dict,
    snapshot_to_dict,
)


def _make_trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    n_frames: int = 2,
) -> StackTrace:
    frames = [
        Frame(filename=f"mod{i}.py", lineno=i * 10, function=f"fn{i}", source=f"x = {i}")
        for i in range(n_frames)
    ]
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=frames)


def test_snapshot_stores_trace():
    trace = _make_trace()
    snap = Snapshot(trace=trace)
    assert snap.trace is trace


def test_snapshot_default_label_is_none():
    snap = Snapshot(trace=_make_trace())
    assert snap.label is None


def test_snapshot_age_seconds_positive():
    snap = Snapshot(trace=_make_trace())
    assert snap.age_seconds() >= 0.0


def test_snapshot_to_dict_has_required_keys():
    snap = Snapshot(trace=_make_trace(), label="my-snap")
    d = snapshot_to_dict(snap)
    for key in ("captured_at", "label", "exception_type", "exception_message", "frames"):
        assert key in d


def test_snapshot_to_dict_exception_type():
    snap = Snapshot(trace=_make_trace(exc_type="KeyError"))
    assert snapshot_to_dict(snap)["exception_type"] == "KeyError"


def test_snapshot_to_dict_frame_count():
    snap = Snapshot(trace=_make_trace(n_frames=3))
    assert len(snapshot_to_dict(snap)["frames"]) == 3


def test_snapshot_roundtrip_via_dict():
    original = Snapshot(trace=_make_trace(), label="roundtrip")
    restored = snapshot_from_dict(snapshot_to_dict(original))
    assert restored.trace.exception_type == original.trace.exception_type
    assert restored.trace.exception_message == original.trace.exception_message
    assert len(restored.trace.frames) == len(original.trace.frames)
    assert restored.label == original.label


def test_dump_and_load_snapshot():
    snap = Snapshot(trace=_make_trace())
    raw = dump_snapshot(snap)
    loaded = load_snapshot(raw)
    assert loaded.trace.exception_type == snap.trace.exception_type


def test_dump_snapshot_is_valid_json():
    snap = Snapshot(trace=_make_trace())
    raw = dump_snapshot(snap)
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_dump_and_load_snapshots_list():
    snaps = [Snapshot(trace=_make_trace(exc_type=f"Err{i}")) for i in range(3)]
    raw = dump_snapshots(snaps)
    loaded = load_snapshots(raw)
    assert len(loaded) == 3
    assert loaded[1].trace.exception_type == "Err1"


def test_load_snapshot_restores_captured_at():
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    snap = Snapshot(trace=_make_trace(), captured_at=ts)
    loaded = load_snapshot(dump_snapshot(snap))
    assert loaded.captured_at == ts
