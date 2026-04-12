"""Denoiser: strip low-signal frames from a stack trace.

A 'noisy' frame is one that comes from a test runner, an import
machinery stub, or a frozen bootstrap module – lines that rarely help
diagnose the real problem.  The denoiser removes them and reports what
was dropped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Sequence

from stacktrace_lens.parser import Frame, StackTrace

# Patterns that identify low-signal frames.
_NOISE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"<frozen "),
    re.compile(r"importlib"),
    re.compile(r"_pytest"),
    re.compile(r"pytest"),
    re.compile(r"unittest"),
    re.compile(r"runpy\.py"),
    re.compile(r"site-packages[\\/]_?six\.py"),
]


@dataclass
class DenoiseOptions:
    extra_patterns: List[str] = field(default_factory=list)
    keep_if_only_noise: bool = True  # keep all frames when *all* are noisy


@dataclass
class DenoiseReport:
    trace: StackTrace
    original_count: int
    removed_frames: List[Frame]

    @property
    def removed_count(self) -> int:
        return len(self.removed_frames)

    @property
    def kept_count(self) -> int:
        return len(self.trace.frames)

    def summary_line(self) -> str:
        return (
            f"Denoised {self.original_count} frames: "
            f"kept {self.kept_count}, removed {self.removed_count}"
        )


def _is_noisy(frame: Frame, compiled_extras: List[re.Pattern[str]]) -> bool:
    path = frame.filename or ""
    all_patterns = _NOISE_PATTERNS + compiled_extras
    return any(p.search(path) for p in all_patterns)


def denoise_trace(
    trace: StackTrace,
    options: DenoiseOptions | None = None,
) -> DenoiseReport:
    """Return a :class:`DenoiseReport` with noisy frames stripped out."""
    if options is None:
        options = DenoiseOptions()

    compiled_extras: List[re.Pattern[str]] = [
        re.compile(p) for p in options.extra_patterns
    ]

    kept: List[Frame] = []
    removed: List[Frame] = []

    for frame in trace.frames:
        if _is_noisy(frame, compiled_extras):
            removed.append(frame)
        else:
            kept.append(frame)

    # If everything is noise and the caller wants a fallback, keep original.
    if not kept and options.keep_if_only_noise:
        kept = list(trace.frames)
        removed = []

    cleaned = StackTrace(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        frames=kept,
    )
    return DenoiseReport(
        trace=cleaned,
        original_count=len(trace.frames),
        removed_frames=removed,
    )
