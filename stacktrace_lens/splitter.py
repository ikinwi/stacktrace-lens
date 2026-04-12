"""Split a multi-exception trace into individual StackTrace objects.

Python 3.11+ chained exceptions produce traces with multiple
'During handling of the above exception, another exception occurred:'
or 'The above exception was the direct cause of the following exception:'
boundaries.  This module detects those boundaries and returns one
StackTrace per exception in the chain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .parser import StackTrace, parse_stacktrace

_CHAIN_MARKERS = (
    "During handling of the above exception, another exception occurred:",
    "The above exception was the direct cause of the following exception:",
)


@dataclass
class SplitReport:
    """Result of splitting a chained traceback."""

    traces: List[StackTrace] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.traces)

    @property
    def is_chained(self) -> bool:
        return self.count > 1


def _split_raw(text: str) -> List[str]:
    """Return raw text segments, one per chained exception."""
    segments: List[str] = []
    current_lines: List[str] = []

    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped in _CHAIN_MARKERS:
            if current_lines:
                segments.append("".join(current_lines))
                current_lines = []
            # skip the marker line itself
        else:
            current_lines.append(line)

    if current_lines:
        segments.append("".join(current_lines))

    return [s for s in segments if s.strip()]


def split_trace(text: str) -> SplitReport:
    """Parse *text* and return a :class:`SplitReport` with one entry per
    chained exception found in the traceback."""
    segments = _split_raw(text)
    traces: List[StackTrace] = []
    for seg in segments:
        try:
            traces.append(parse_stacktrace(seg))
        except Exception:
            pass  # skip unparseable segments
    return SplitReport(traces=traces)


def format_split(report: SplitReport, *, colour: bool = True) -> str:
    """Render a :class:`SplitReport` as a human-readable string."""
    if not report.traces:
        return "(no traces found)"

    lines: List[str] = []
    sep = "\u2500" * 60
    for idx, trace in enumerate(report.traces, start=1):
        header = f"[{idx}/{report.count}] {trace.exception_type}: {trace.exception_message}"
        if colour:
            header = f"\033[1;33m{header}\033[0m"
        lines.append(header)
        lines.append(f"  frames : {len(trace.frames)}")
        if idx < report.count:
            lines.append(sep)
    return "\n".join(lines)
