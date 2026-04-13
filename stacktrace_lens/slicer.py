"""slicer.py – extract a contiguous slice of frames from a stack trace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class SliceOptions:
    start: int = 0          # inclusive, 0-based
    end: Optional[int] = None  # exclusive; None means "to the end"
    step: int = 1


@dataclass
class SliceReport:
    original_count: int
    frames: List[Frame] = field(default_factory=list)
    start: int = 0
    end: Optional[int] = None
    step: int = 1

    @property
    def sliced_count(self) -> int:
        return len(self.frames)

    @property
    def removed_count(self) -> int:
        return self.original_count - self.sliced_count

    def summary_line(self) -> str:
        end_label = self.end if self.end is not None else self.original_count
        return (
            f"Sliced frames [{self.start}:{end_label}:{self.step}] "
            f"– kept {self.sliced_count}/{self.original_count} frame(s)."
        )

    def as_trace(self) -> StackTrace:
        return StackTrace(
            exception_type="<sliced>",
            exception_message="",
            frames=list(self.frames),
        )


def slice_trace(trace: StackTrace, options: Optional[SliceOptions] = None) -> SliceReport:
    """Return a SliceReport containing the requested subset of *trace*'s frames."""
    if options is None:
        options = SliceOptions()

    frames = trace.frames
    start = max(0, options.start)
    end = options.end  # may be None
    step = options.step if options.step >= 1 else 1

    sliced = frames[start:end:step]

    return SliceReport(
        original_count=len(frames),
        frames=list(sliced),
        start=start,
        end=end,
        step=step,
    )
