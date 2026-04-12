"""Resolve ambiguous or relative file paths in stack frames to absolute paths."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class ResolveOptions:
    search_paths: List[str] = field(default_factory=list)
    resolve_symlinks: bool = False
    skip_missing: bool = True


@dataclass
class ResolvedFrame:
    original: Frame
    resolved_filename: str
    was_resolved: bool

    def __str__(self) -> str:
        tag = "resolved" if self.was_resolved else "unresolved"
        return f"{self.resolved_filename} [{tag}] line {self.original.lineno} in {self.original.function}"


@dataclass
class ResolveReport:
    frames: List[ResolvedFrame]
    search_paths: List[str]

    @property
    def resolved_count(self) -> int:
        return sum(1 for f in self.frames if f.was_resolved)

    @property
    def unresolved_count(self) -> int:
        return len(self.frames) - self.resolved_count


def _resolve_path(filename: str, search_paths: List[str], resolve_symlinks: bool) -> Optional[str]:
    if os.path.isabs(filename):
        if os.path.exists(filename):
            path = os.path.realpath(filename) if resolve_symlinks else filename
            return path
        return None

    for base in search_paths:
        candidate = os.path.join(base, filename)
        if os.path.exists(candidate):
            path = os.path.realpath(candidate) if resolve_symlinks else os.path.abspath(candidate)
            return path

    return None


def resolve_frames(trace: StackTrace, options: Optional[ResolveOptions] = None) -> ResolveReport:
    if options is None:
        options = ResolveOptions()

    search_paths = options.search_paths or [os.getcwd()]
    resolved: List[ResolvedFrame] = []

    for frame in trace.frames:
        resolved_path = _resolve_path(frame.filename, search_paths, options.resolve_symlinks)
        if resolved_path is not None:
            resolved.append(ResolvedFrame(original=frame, resolved_filename=resolved_path, was_resolved=True))
        else:
            resolved.append(ResolvedFrame(original=frame, resolved_filename=frame.filename, was_resolved=False))

    return ResolveReport(frames=resolved, search_paths=search_paths)


def format_resolve_report(report: ResolveReport) -> str:
    lines = [
        f"Resolved: {report.resolved_count}  Unresolved: {report.unresolved_count}",
        "",
    ]
    for rf in report.frames:
        lines.append(f"  {rf}")
    return "\n".join(lines)
