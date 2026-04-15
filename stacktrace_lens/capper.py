"""capper.py – cap (limit) the number of frames per trace, keeping either
the head (first N) or the tail (last N) frames.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class CapOptions:
    max_frames: int = 10
    keep: str = "tail"  # "head" | "tail"


@dataclass
class CapReport:
    original_count: int
    frames: List[Frame]
    exception_type: str
    exception_message: str
    was_capped: bool

    @property
    def kept_count(self) -> int:
        return len(self.frames)

    @property
    def dropped_count(self) -> int:
        return max(0, self.original_count - self.kept_count)

    def summary_line(self) -> str:
        if not self.was_capped:
            return f"No frames dropped (total: {self.original_count})"
        return (
            f"Capped {self.original_count} → {self.kept_count} frames "
            f"(dropped {self.dropped_count})"
        )

    def as_trace(self) -> StackTrace:
        return StackTrace(
            exception_type=self.exception_type,
            exception_message=self.exception_message,
            frames=self.frames,
        )


def cap_trace(trace: StackTrace, options: Optional[CapOptions] = None) -> CapReport:
    """Return a CapReport that limits *trace* to at most *options.max_frames*."""
    if options is None:
        options = CapOptions()

    original = list(trace.frames)
    n = options.max_frames

    if n <= 0:
        kept: List[Frame] = []
    elif options.keep == "head":
        kept = original[:n]
    else:  # default: tail
        kept = original[-n:] if len(original) > n else original

    was_capped = len(kept) < len(original)

    return CapReport(
        original_count=len(original),
        frames=kept,
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        was_capped=was_capped,
    )
