"""Flatten a nested chain of stack traces into a single ordered list of frames."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class FlattenReport:
    """Result of flattening one or more chained stack traces."""

    frames: List[Frame] = field(default_factory=list)
    source_traces: List[StackTrace] = field(default_factory=list)
    exception_chain: List[str] = field(default_factory=list)

    @property
    def total_frames(self) -> int:
        return len(self.frames)

    @property
    def trace_count(self) -> int:
        return len(self.source_traces)

    def summary_line(self) -> str:
        exc = " -> ".join(self.exception_chain) if self.exception_chain else "(none)"
        return (
            f"{self.trace_count} trace(s), "
            f"{self.total_frames} frame(s) total, "
            f"chain: {exc}"
        )


def flatten_traces(traces: List[StackTrace]) -> FlattenReport:
    """Merge all frames from *traces* into a single flat list.

    Frames are appended in the order the traces are supplied, preserving
    the original per-trace frame order.  Duplicate consecutive frames
    (same file + lineno + function) are collapsed into one entry.
    """
    report = FlattenReport()
    seen_key: Optional[tuple] = None

    for trace in traces:
        report.source_traces.append(trace)
        exc_label = trace.exception_type or "Unknown"
        if exc_label not in report.exception_chain:
            report.exception_chain.append(exc_label)

        for frame in trace.frames:
            key = (frame.filename, frame.lineno, frame.function)
            if key != seen_key:
                report.frames.append(frame)
                seen_key = key

    return report


def format_flatten(report: FlattenReport, *, colour: bool = False) -> str:
    """Return a human-readable string representation of *report*."""
    _R = "\033[0m"
    _B = "\033[1m" if colour else ""
    _E = _R if colour else ""

    lines: List[str] = []
    lines.append(f"{_B}Flattened Trace{_E}")
    lines.append(f"  {report.summary_line()}")
    lines.append("")
    for i, frame in enumerate(report.frames, 1):
        lines.append(
            f"  [{i:>3}] {frame.filename}:{frame.lineno} in {frame.function}"
        )
    return "\n".join(lines)
