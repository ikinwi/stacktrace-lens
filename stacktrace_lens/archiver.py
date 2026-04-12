"""Archive multiple stack traces to a JSON file and reload them."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class ArchiveEntry:
    trace: StackTrace
    label: Optional[str] = None
    archived_at: float = field(default_factory=time.time)


@dataclass
class Archive:
    entries: List[ArchiveEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)


def _frame_to_dict(f: Frame) -> dict:
    return {"filename": f.filename, "lineno": f.lineno, "function": f.function, "source": f.source}


def _frame_from_dict(d: dict) -> Frame:
    return Frame(filename=d["filename"], lineno=d["lineno"], function=d["function"], source=d.get("source", ""))


def _entry_to_dict(e: ArchiveEntry) -> dict:
    return {
        "label": e.label,
        "archived_at": e.archived_at,
        "exception_type": e.trace.exception_type,
        "exception_message": e.trace.exception_message,
        "frames": [_frame_to_dict(f) for f in e.trace.frames],
    }


def _entry_from_dict(d: dict) -> ArchiveEntry:
    frames = [_frame_from_dict(f) for f in d.get("frames", [])]
    trace = StackTrace(
        exception_type=d["exception_type"],
        exception_message=d["exception_message"],
        frames=frames,
    )
    return ArchiveEntry(trace=trace, label=d.get("label"), archived_at=d.get("archived_at", 0.0))


def save_archive(archive: Archive, path: Path) -> None:
    data = {"entries": [_entry_to_dict(e) for e in archive.entries]}
    path.write_text(json.dumps(data, indent=2))


def load_archive(path: Path) -> Archive:
    raw = json.loads(path.read_text())
    entries = [_entry_from_dict(d) for d in raw.get("entries", [])]
    return Archive(entries=entries)


def add_to_archive(archive: Archive, trace: StackTrace, label: Optional[str] = None) -> ArchiveEntry:
    entry = ArchiveEntry(trace=trace, label=label)
    archive.entries.append(entry)
    return entry
