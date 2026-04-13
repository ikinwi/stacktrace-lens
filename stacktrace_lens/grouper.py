"""Group consecutive frames by package or directory for summarised output."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import List, Tuple

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class FrameGroup:
    """A contiguous sequence of frames sharing the same top-level package."""

    label: str
    frames: List[Frame]

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def is_stdlib(self) -> bool:
        """Return True if this group originates from the Python standard library."""
        return self.label in ("python", "lib", "stdlib") or any(
            "lib/python" in f.filename or "Lib" in f.filename.split("/")
            for f in self.frames
        )


def _package_label(filename: str) -> str:
    """Return a short label representing the origin of *filename*.

    Resolution order:
    1. If the path contains a ``site-packages`` segment, return the
       immediately following segment (i.e. the third-party package name).
    2. Otherwise return the parent directory name.
    3. Fall back to the bare filename when no parent is available.
    """
    p = PurePosixPath(filename)
    parts = p.parts
    if "site-packages" in parts:
        idx = parts.index("site-packages")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    if len(parts) >= 2:
        return parts[-2]  # parent directory name
    return filename


def group_frames(trace: StackTrace) -> List[FrameGroup]:
    """Group frames in *trace* by package label.

    Consecutive frames with the same label are merged into one group.
    """
    groups: List[FrameGroup] = []
    for frame in trace.frames:
        label = _package_label(frame.filename)
        if groups and groups[-1].label == label:
            groups[-1].frames.append(frame)
        else:
            groups.append(FrameGroup(label=label, frames=[frame]))
    return groups


def summarise_groups(groups: List[FrameGroup]) -> List[Tuple[str, int]]:
    """Return a compact (label, count) list for display purposes."""
    return [(g.label, g.count) for g in groups]
