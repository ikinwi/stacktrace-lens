"""Maps stack trace frames to structured path/module metadata."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class MappedFrame:
    frame: Frame
    module: str
    package: str
    relative_path: str
    is_absolute: bool

    def __str__(self) -> str:
        return f"{self.package}::{self.module} ({self.relative_path})"


@dataclass
class MapReport:
    frames: List[MappedFrame] = field(default_factory=list)
    exception_type: str = ""
    exception_message: str = ""

    @property
    def count(self) -> int:
        return len(self.frames)

    def packages(self) -> List[str]:
        seen: list = []
        for f in self.frames:
            if f.package not in seen:
                seen.append(f.package)
        return seen

    def summary_line(self) -> str:
        pkgs = len(self.packages())
        return (
            f"{self.count} frame(s) across {pkgs} package(s) "
            f"[{self.exception_type}]"
        )


def _module_from_path(filepath: str) -> str:
    """Derive a dotted module name from a file path."""
    clean = filepath.replace(os.sep, "/")
    if clean.endswith(".py"):
        clean = clean[:-3]
    return clean.replace("/", ".")


def _package_from_path(filepath: str) -> str:
    """Return the top-level package name from a file path."""
    parts = filepath.replace("\\", "/").split("/")
    for part in parts:
        if part and part != "." and not part.startswith("<"):
            return part.replace(".py", "")
    return "<unknown>"


def map_trace(trace: StackTrace) -> MapReport:
    """Map all frames in a stack trace to structured metadata."""
    report = MapReport(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )
    for frame in trace.frames:
        filepath = frame.filename or ""
        is_absolute = os.path.isabs(filepath)
        relative = os.path.relpath(filepath) if is_absolute else filepath
        module = _module_from_path(relative)
        package = _package_from_path(relative)
        report.frames.append(
            MappedFrame(
                frame=frame,
                module=module,
                package=package,
                relative_path=relative,
                is_absolute=is_absolute,
            )
        )
    return report


def format_map(report: MapReport, *, colour: bool = False) -> str:
    """Render a MapReport as a human-readable string."""
    lines: List[str] = [report.summary_line(), ""]
    for mf in report.frames:
        lines.append(f"  {mf.package:20s}  {mf.relative_path}:{mf.frame.lineno}")
    return "\n".join(lines)
