"""Frame filtering utilities for stacktrace-lens."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class FilterOptions:
    """Options controlling which frames are included in output."""

    exclude_patterns: List[str] = field(default_factory=list)
    include_only_patterns: List[str] = field(default_factory=list)
    exclude_stdlib: bool = False
    max_frames: Optional[int] = None


_STDLIB_PATTERNS = [
    "/lib/python*",
    "*/site-packages/*",
    "<frozen *",
]


def _matches_any(path: str, patterns: List[str]) -> bool:
    return any(fnmatch(path, p) for p in patterns)


def _is_stdlib(frame: Frame) -> bool:
    return _matches_any(frame.filename, _STDLIB_PATTERNS)


def filter_frames(trace: StackTrace, options: FilterOptions) -> StackTrace:
    """Return a new StackTrace with frames filtered according to *options*."""
    frames = list(trace.frames)

    if options.exclude_stdlib:
        frames = [f for f in frames if not _is_stdlib(f)]

    if options.exclude_patterns:
        frames = [
            f for f in frames
            if not _matches_any(f.filename, options.exclude_patterns)
        ]

    if options.include_only_patterns:
        frames = [
            f for f in frames
            if _matches_any(f.filename, options.include_only_patterns)
        ]

    if options.max_frames is not None:
        frames = frames[-options.max_frames:]

    return StackTrace(
        frames=frames,
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )
