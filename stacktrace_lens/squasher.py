"""squasher.py – collapse consecutive duplicate frames into a single entry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class SquashedFrame:
    frame: Frame
    repeat_count: int = 1

    def __str__(self) -> str:  # pragma: no cover
        suffix = f" (x{self.repeat_count})" if self.repeat_count > 1 else ""
        fn = self.frame.function or "<module>"
        return f"{self.frame.filename}:{self.frame.lineno} in {fn}{suffix}"


@dataclass
class SquashReport:
    original_count: int
    frames: List[SquashedFrame] = field(default_factory=list)

    @property
    def squashed_count(self) -> int:
        return len(self.frames)

    @property
    def removed_count(self) -> int:
        return self.original_count - self.squashed_count

    def summary_line(self) -> str:
        return (
            f"{self.squashed_count} frames after squashing "
            f"({self.removed_count} duplicates removed)"
        )


def _frame_key(frame: Frame) -> tuple:
    return (frame.filename, frame.lineno, frame.function)


def squash_trace(trace: StackTrace) -> SquashReport:
    """Collapse consecutive duplicate frames in *trace*."""
    original_count = len(trace.frames)
    squashed: List[SquashedFrame] = []

    for frame in trace.frames:
        key = _frame_key(frame)
        if squashed and _frame_key(squashed[-1].frame) == key:
            squashed[-1].repeat_count += 1
        else:
            squashed.append(SquashedFrame(frame=frame))

    return SquashReport(original_count=original_count, frames=squashed)


def format_squash(report: SquashReport, *, colour: bool = False) -> str:
    """Return a human-readable string for *report*."""
    lines: List[str] = [report.summary_line()]
    for sf in report.frames:
        lines.append(f"  {sf}")
    return "\n".join(lines)
