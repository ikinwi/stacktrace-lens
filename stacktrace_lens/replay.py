"""replay.py — Record and replay stack traces for regression testing.

Provides utilities to save a parsed StackTrace to a JSON file and
reload it later, enabling deterministic replay of error scenarios
without needing the original process to crash again.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import List, Optional

from .parser import Frame, StackTrace


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _frame_to_dict(frame: Frame) -> dict:
    """Convert a Frame dataclass to a plain dict."""
    return {
        "filename": frame.filename,
        "lineno": frame.lineno,
        "function": frame.function,
        "source": frame.source,
    }


def _frame_from_dict(data: dict) -> Frame:
    """Reconstruct a Frame from a plain dict."""
    return Frame(
        filename=data["filename"],
        lineno=int(data["lineno"]),
        function=data["function"],
        source=data.get("source"),
    )


def _trace_to_dict(trace: StackTrace) -> dict:
    """Serialise a StackTrace to a JSON-compatible dict."""
    return {
        "exception_type": trace.exception_type,
        "exception_message": trace.exception_message,
        "frames": [_frame_to_dict(f) for f in trace.frames],
    }


def _trace_from_dict(data: dict) -> StackTrace:
    """Deserialise a StackTrace from a plain dict."""
    return StackTrace(
        exception_type=data["exception_type"],
        exception_message=data["exception_message"],
        frames=[_frame_from_dict(f) for f in data.get("frames", [])],
    )


# ---------------------------------------------------------------------------
# Replay record
# ---------------------------------------------------------------------------

@dataclass
class ReplayRecord:
    """A single saved trace with metadata."""

    trace: StackTrace
    label: Optional[str] = None
    recorded_at: Optional[str] = None  # ISO-8601 string

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "recorded_at": self.recorded_at,
            "trace": _trace_to_dict(self.trace),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReplayRecord":
        return cls(
            trace=_trace_from_dict(data["trace"]),
            label=data.get("label"),
            recorded_at=data.get("recorded_at"),
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_replay(trace: StackTrace, path: str, label: Optional[str] = None) -> ReplayRecord:
    """Serialise *trace* to *path* as a JSON replay file.

    Parameters
    ----------
    trace:  The parsed stack trace to persist.
    path:   Destination file path (will be created or overwritten).
    label:  Optional human-readable name for this replay.

    Returns
    -------
    The :class:`ReplayRecord` that was written.
    """
    record = ReplayRecord(
        trace=trace,
        label=label,
        recorded_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record.to_dict(), fh, indent=2)
    return record


def load_replay(path: str) -> ReplayRecord:
    """Load a replay file previously created by :func:`save_replay`.

    Raises
    ------
    FileNotFoundError  if *path* does not exist.
    ValueError         if the file cannot be parsed.
    """
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid replay file '{path}': {exc}") from exc
    return ReplayRecord.from_dict(data)


def list_replays(directory: str) -> List[ReplayRecord]:
    """Return all replay records found in *directory* (non-recursive).

    Files that cannot be parsed are silently skipped.
    """
    records: List[ReplayRecord] = []
    if not os.path.isdir(directory):
        return records
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        try:
            records.append(load_replay(os.path.join(directory, name)))
        except (ValueError, KeyError):
            pass
    return records
