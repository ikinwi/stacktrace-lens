"""Extract specific slices or subsets of frames from a stack trace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class ExtractOptions:
    """Options controlling which frames are extracted."""
    head: Optional[int] = None        # keep first N frames
    tail: Optional[int] = None        # keep last  N frames
    around_line: Optional[int] = None # keep frames whose lineno == this value
    window: int = 1                   # frames either side when using around_line
    filename_contains: Optional[str] = None  # keep frames matching substring


@dataclass
class ExtractReport:
    """Result of an extraction operation."""
    original_count: int
    frames: List[Frame] = field(default_factory=list)
    options: ExtractOptions = field(default_factory=ExtractOptions)

    @property
    def extracted_count(self) -> int:
        return len(self.frames)

    def summary_line(self) -> str:
        return (
            f"Extracted {self.extracted_count} / {self.original_count} frames"
        )

    def as_trace(self) -> StackTrace:
        """Return a new StackTrace containing only the extracted frames."""
        return StackTrace(
            exception_type=" ",
            exception_message="(extracted)",
            frames=list(self.frames),
        )


def extract_frames(trace: StackTrace, options: Optional[ExtractOptions] = None) -> ExtractReport:
    """Extract a subset of frames from *trace* according to *options*."""
    if options is None:
        options = ExtractOptions()

    frames: List[Frame] = list(trace.frames)
    original_count = len(frames)

    # Apply filename filter first so head/tail operate on the filtered set.
    if options.filename_contains is not None:
        needle = options.filename_contains
        frames = [f for f in frames if needle in f.filename]

    if options.around_line is not None:
        target = options.around_line
        w = options.window
        indices = [
            i for i, f in enumerate(frames)
            if abs(f.lineno - target) <= w
        ]
        if indices:
            lo = max(0, min(indices) - w)
            hi = min(len(frames), max(indices) + w + 1)
            frames = frames[lo:hi]
        else:
            frames = []

    if options.head is not None:
        frames = frames[: options.head]

    if options.tail is not None:
        frames = frames[-options.tail :] if options.tail else []

    return ExtractReport(
        original_count=original_count,
        frames=frames,
        options=options,
    )
