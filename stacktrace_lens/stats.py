"""Compute statistics from a parsed stack trace."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List

from stacktrace_lens.parser import StackTrace


@dataclass
class StackTraceStats:
    """Aggregated statistics for a single stack trace."""

    total_frames: int = 0
    unique_files: int = 0
    unique_functions: int = 0
    exception_type: str = ""
    top_file: str = ""          # file that appears most often
    top_function: str = ""      # function that appears most often
    packages: Dict[str, int] = field(default_factory=dict)
    file_counts: Dict[str, int] = field(default_factory=dict)
    function_counts: Dict[str, int] = field(default_factory=dict)


def _package_of(filename: str) -> str:
    """Return a rough top-level package name from a file path."""
    parts = filename.replace("\\", "/").split("/")
    for part in parts:
        if part and part not in (".", "..") and not part.endswith(".py"):
            return part
    return "<unknown>"


def compute_stats(trace: StackTrace) -> StackTraceStats:
    """Return a :class:`StackTraceStats` computed from *trace*."""
    stats = StackTraceStats()
    stats.total_frames = len(trace.frames)
    stats.exception_type = trace.exception_type

    file_counter: Counter[str] = Counter()
    func_counter: Counter[str] = Counter()
    pkg_counter: Counter[str] = Counter()

    for frame in trace.frames:
        file_counter[frame.filename] += 1
        func_counter[frame.function] += 1
        pkg_counter[_package_of(frame.filename)] += 1

    stats.file_counts = dict(file_counter)
    stats.function_counts = dict(func_counter)
    stats.packages = dict(pkg_counter)
    stats.unique_files = len(file_counter)
    stats.unique_functions = len(func_counter)

    if file_counter:
        stats.top_file = file_counter.most_common(1)[0][0]
    if func_counter:
        stats.top_function = func_counter.most_common(1)[0][0]

    return stats


def format_stats(stats: StackTraceStats) -> str:
    """Return a human-readable summary string for *stats*."""
    lines: List[str] = [
        f"Exception   : {stats.exception_type}",
        f"Frames      : {stats.total_frames}",
        f"Unique files: {stats.unique_files}",
        f"Unique funcs: {stats.unique_functions}",
    ]
    if stats.top_file:
        lines.append(f"Hottest file: {stats.top_file} ({stats.file_counts[stats.top_file]}x)")
    if stats.top_function:
        lines.append(f"Hottest func: {stats.top_function} ({stats.function_counts[stats.top_function]}x)")
    if stats.packages:
        pkg_summary = ", ".join(
            f"{k}({v})" for k, v in sorted(stats.packages.items(), key=lambda x: -x[1])
        )
        lines.append(f"Packages    : {pkg_summary}")
    return "\n".join(lines)
