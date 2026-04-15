"""collapser.py – collapse consecutive stdlib or third-party frames into a
single summary line, reducing visual noise in long stack traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class CollapseOptions:
    collapse_stdlib: bool = True
    collapse_third_party: bool = False
    min_run: int = 2  # minimum consecutive frames before collapsing


@dataclass
class CollapsedFrame:
    """Represents either a kept frame or a collapsed group."""
    frame: Frame | None  # None when this is a collapsed group
    collapsed_count: int = 0
    label: str = ""

    @property
    def is_collapsed(self) -> bool:
        return self.frame is None

    def __str__(self) -> str:
        if self.is_collapsed:
            return f"[{self.collapsed_count} frames collapsed: {self.label}]"
        f = self.frame
        return f"{f.filename}:{f.lineno} in {f.function or '<module>'}"


@dataclass
class CollapseReport:
    frames: List[CollapsedFrame] = field(default_factory=list)
    original_count: int = 0
    collapsed_count: int = 0

    @property
    def kept_count(self) -> int:
        return self.original_count - self.collapsed_count

    def summary_line(self) -> str:
        return (
            f"Collapsed {self.collapsed_count}/{self.original_count} frames "
            f"({self.kept_count} kept, "
            f"{sum(1 for f in self.frames if f.is_collapsed)} groups)"
        )


def _is_stdlib(filename: str) -> bool:
    import sys, os
    stdlib_paths = (sys.prefix, os.path.join(sys.prefix, "lib"))
    return (
        filename.startswith("<")
        or "/lib/python" in filename
        or any(filename.startswith(p) for p in stdlib_paths)
    )


def _is_third_party(filename: str) -> bool:
    return "site-packages" in filename or "dist-packages" in filename


def collapse_frames(trace: StackTrace, opts: CollapseOptions | None = None) -> CollapseReport:
    if opts is None:
        opts = CollapseOptions()

    report = CollapseReport(original_count=len(trace.frames))
    frames = trace.frames
    i = 0
    while i < len(frames):
        f = frames[i]
        is_std = opts.collapse_stdlib and _is_stdlib(f.filename or "")
        is_tp = opts.collapse_third_party and _is_third_party(f.filename or "")
        if is_std or is_tp:
            run_start = i
            while i < len(frames):
                fn = frames[i].filename or ""
                if (opts.collapse_stdlib and _is_stdlib(fn)) or \
                   (opts.collapse_third_party and _is_third_party(fn)):
                    i += 1
                else:
                    break
            run_len = i - run_start
            if run_len >= opts.min_run:
                label = "stdlib" if is_std else "third-party"
                report.frames.append(CollapsedFrame(
                    frame=None, collapsed_count=run_len, label=label
                ))
                report.collapsed_count += run_len
            else:
                for j in range(run_start, i):
                    report.frames.append(CollapsedFrame(frame=frames[j]))
        else:
            report.frames.append(CollapsedFrame(frame=f))
            i += 1
    return report
