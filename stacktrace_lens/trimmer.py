"""Trim stack traces by removing noise frames from the top or bottom."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class TrimOptions:
    strip_top: int = 0          # remove N frames from the outermost (top) end
    strip_bottom: int = 0       # remove N frames from the innermost (bottom) end
    drop_prefix: Optional[str] = None   # drop frames whose filename starts with this
    drop_suffix: Optional[str] = None   # drop frames whose filename ends with this


@dataclass
class TrimReport:
    original_count: int
    frames: List[Frame]
    stripped_top: int
    stripped_bottom: int
    dropped_prefix: int
    dropped_suffix: int
    trace: StackTrace

    @property
    def trimmed_count(self) -> int:
        return len(self.frames)

    @property
    def removed_count(self) -> int:
        return self.original_count - self.trimmed_count

    def summary_line(self) -> str:
        parts = []
        if self.stripped_top:
            parts.append(f"top:{self.stripped_top}")
        if self.stripped_bottom:
            parts.append(f"bottom:{self.stripped_bottom}")
        if self.dropped_prefix:
            parts.append(f"prefix:{self.dropped_prefix}")
        if self.dropped_suffix:
            parts.append(f"suffix:{self.dropped_suffix}")
        detail = ", ".join(parts) if parts else "none"
        return (
            f"{self.original_count} frames -> {self.trimmed_count} kept "
            f"(removed {self.removed_count}: {detail})"
        )


def trim_trace(trace: StackTrace, options: Optional[TrimOptions] = None) -> TrimReport:
    """Apply trimming rules to *trace* and return a TrimReport."""
    if options is None:
        options = TrimOptions()

    frames: List[Frame] = list(trace.frames)
    original_count = len(frames)

    # Strip from top (outermost call)
    top_cut = min(options.strip_top, len(frames))
    frames = frames[top_cut:]

    # Strip from bottom (innermost call)
    bottom_cut = min(options.strip_bottom, len(frames))
    if bottom_cut:
        frames = frames[:-bottom_cut]

    # Drop by prefix
    before_prefix = len(frames)
    if options.drop_prefix:
        frames = [f for f in frames if not f.filename.startswith(options.drop_prefix)]
    dropped_prefix = before_prefix - len(frames)

    # Drop by suffix
    before_suffix = len(frames)
    if options.drop_suffix:
        frames = [f for f in frames if not f.filename.endswith(options.drop_suffix)]
    dropped_suffix = before_suffix - len(frames)

    trimmed_trace = StackTrace(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        frames=frames,
    )

    return TrimReport(
        original_count=original_count,
        frames=frames,
        stripped_top=top_cut,
        stripped_bottom=bottom_cut,
        dropped_prefix=dropped_prefix,
        dropped_suffix=dropped_suffix,
        trace=trimmed_trace,
    )
