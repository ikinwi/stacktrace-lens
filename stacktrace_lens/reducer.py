"""Noise-reduction pass: collapse repeated frames and trim stdlib-only runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace


@dataclass
class ReduceOptions:
    max_consecutive_stdlib: int = 3
    collapse_duplicates: bool = True
    keep_top: Optional[int] = None  # keep only the N innermost frames


@dataclass
class ReducedFrame:
    frame: Frame
    repeat_count: int = 1
    collapsed: bool = False

    def __str__(self) -> str:
        suffix = f" (x{self.repeat_count})" if self.repeat_count > 1 else ""
        return f"{self.frame.filename}:{self.frame.lineno} in {self.frame.function}{suffix}"


@dataclass
class ReduceReport:
    original_count: int
    reduced_frames: List[ReducedFrame] = field(default_factory=list)

    @property
    def reduced_count(self) -> int:
        return len(self.reduced_frames)

    @property
    def removed_count(self) -> int:
        return self.original_count - self.reduced_count


def _is_stdlib(filename: str) -> bool:
    import sys
    import os
    stdlib = getattr(sys, "stdlib_module_names", set())
    norm = filename.replace("\\", "/")
    if "/lib/python" in norm and "site-packages" not in norm:
        return True
    parts = norm.split("/")
    if parts and parts[0] in stdlib:
        return True
    return False


def _frame_key(f: Frame) -> str:
    return f"{f.filename}:{f.lineno}:{f.function}"


def reduce_trace(trace: StackTrace, options: Optional[ReduceOptions] = None) -> ReduceReport:
    opts = options or ReduceOptions()
    frames = list(trace.frames)

    if opts.keep_top is not None and opts.keep_top > 0:
        frames = frames[-opts.keep_top:]

    reduced: List[ReducedFrame] = []
    for frame in frames:
        if opts.collapse_duplicates and reduced and _frame_key(reduced[-1].frame) == _frame_key(frame):
            reduced[-1].repeat_count += 1
            reduced[-1].collapsed = True
        else:
            reduced.append(ReducedFrame(frame=frame))

    # Collapse long stdlib runs
    if opts.max_consecutive_stdlib > 0:
        result: List[ReducedFrame] = []
        stdlib_run: List[ReducedFrame] = []
        for rf in reduced:
            if _is_stdlib(rf.frame.filename):
                stdlib_run.append(rf)
            else:
                if len(stdlib_run) > opts.max_consecutive_stdlib:
                    kept = stdlib_run[:1] + stdlib_run[-1:]
                    for k in kept:
                        result.append(k)
                else:
                    result.extend(stdlib_run)
                stdlib_run = []
                result.append(rf)
        if len(stdlib_run) > opts.max_consecutive_stdlib:
            result.extend(stdlib_run[:1] + stdlib_run[-1:])
        else:
            result.extend(stdlib_run)
        reduced = result

    return ReduceReport(original_count=len(frames), reduced_frames=reduced)
