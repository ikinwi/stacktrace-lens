"""Prune frames from a stack trace based on depth and pattern rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class PruneOptions:
    max_frames: Optional[int] = None
    drop_patterns: List[str] = field(default_factory=list)
    keep_first: int = 0
    keep_last: int = 0


@dataclass
class PruneReport:
    trace: StackTrace
    original_count: int
    pruned_count: int

    @property
    def removed_count(self) -> int:
        return self.original_count - self.pruned_count

    def summary_line(self) -> str:
        return (
            f"Pruned {self.removed_count} of {self.original_count} frames "
            f"({self.pruned_count} remaining)."
        )


def _matches_drop(frame: Frame, patterns: List[str]) -> bool:
    for pat in patterns:
        if re.search(pat, frame.filename or "") or re.search(pat, frame.function or ""):
            return True
    return False


def prune_trace(trace: StackTrace, options: Optional[PruneOptions] = None) -> PruneReport:
    """Return a PruneReport with frames removed according to *options*."""
    if options is None:
        options = PruneOptions()

    frames: List[Frame] = list(trace.frames)
    original_count = len(frames)

    # Drop by pattern first
    if options.drop_patterns:
        frames = [f for f in frames if not _matches_drop(f, options.drop_patterns)]

    # Apply keep_first / keep_last anchors before max_frames cap
    if options.keep_first or options.keep_last:
        head = frames[: options.keep_first] if options.keep_first else []
        tail = frames[-options.keep_last :] if options.keep_last else []
        middle = frames[options.keep_first : len(frames) - options.keep_last if options.keep_last else len(frames)]
        # Drop middle frames if we have a cap
        if options.max_frames is not None:
            budget = max(0, options.max_frames - len(head) - len(tail))
            middle = middle[:budget]
        frames = head + middle + tail
    elif options.max_frames is not None:
        frames = frames[: options.max_frames]

    pruned_trace = StackTrace(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        frames=frames,
    )
    return PruneReport(
        trace=pruned_trace,
        original_count=original_count,
        pruned_count=len(frames),
    )
