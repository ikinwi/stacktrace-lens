"""Split a StackTrace into logical segments based on package boundaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class Segment:
    """A contiguous slice of frames sharing the same package label."""

    label: str
    frames: List[Frame] = field(default_factory=list)

    @property
    def count(self) -> int:  # noqa: D401
        return len(self.frames)

    def __str__(self) -> str:
        return f"Segment({self.label!r}, {self.count} frame(s))"


@dataclass
class SegmentReport:
    """Result returned by :func:`segment_trace`."""

    trace: StackTrace
    segments: List[Segment]

    @property
    def count(self) -> int:  # noqa: D401
        return len(self.segments)

    def summary_line(self) -> str:
        return (
            f"{self.trace.exception_type}: "
            f"{self.count} segment(s) across {len(self.trace.frames)} frame(s)"
        )


def _package_of(frame: Frame) -> str:
    """Return a coarse package label for *frame*."""
    if not frame.filename:
        return "<unknown>"
    parts = frame.filename.replace("\\", "/").split("/")
    # Prefer the top-level directory name as the package label.
    for part in parts:
        if part and part not in (".", ".."):
            return part
    return "<unknown>"


def segment_trace(trace: StackTrace) -> SegmentReport:
    """Group consecutive frames that share the same package into segments."""
    segments: List[Segment] = []
    for frame in trace.frames:
        label = _package_of(frame)
        if segments and segments[-1].label == label:
            segments[-1].frames.append(frame)
        else:
            segments.append(Segment(label=label, frames=[frame]))
    return SegmentReport(trace=trace, segments=segments)
