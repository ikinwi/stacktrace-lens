"""Snapshot module: capture and restore StackTrace instances to/from dicts."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class Snapshot:
    trace: StackTrace
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: Optional[str] = None

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        ref = now or datetime.now(timezone.utc)
        return (ref - self.captured_at).total_seconds()


def _frame_to_dict(f: Frame) -> Dict[str, Any]:
    return {
        "filename": f.filename,
        "lineno": f.lineno,
        "function": f.function,
        "source": f.source,
    }


def _frame_from_dict(d: Dict[str, Any]) -> Frame:
    return Frame(
        filename=d["filename"],
        lineno=d["lineno"],
        function=d["function"],
        source=d.get("source"),
    )


def snapshot_to_dict(snap: Snapshot) -> Dict[str, Any]:
    return {
        "captured_at": snap.captured_at.isoformat(),
        "label": snap.label,
        "exception_type": snap.trace.exception_type,
        "exception_message": snap.trace.exception_message,
        "frames": [_frame_to_dict(f) for f in snap.trace.frames],
    }


def snapshot_from_dict(d: Dict[str, Any]) -> Snapshot:
    frames = [_frame_from_dict(fd) for fd in d.get("frames", [])]
    trace = StackTrace(
        exception_type=d["exception_type"],
        exception_message=d["exception_message"],
        frames=frames,
    )
    captured_at = datetime.fromisoformat(d["captured_at"])
    return Snapshot(trace=trace, captured_at=captured_at, label=d.get("label"))


def dump_snapshot(snap: Snapshot) -> str:
    return json.dumps(snapshot_to_dict(snap), indent=2)


def load_snapshot(raw: str) -> Snapshot:
    return snapshot_from_dict(json.loads(raw))


def dump_snapshots(snaps: List[Snapshot]) -> str:
    return json.dumps([snapshot_to_dict(s) for s in snaps], indent=2)


def load_snapshots(raw: str) -> List[Snapshot]:
    return [snapshot_from_dict(d) for d in json.loads(raw)]
