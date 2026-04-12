"""Summarize one or more stack traces into a concise human-readable report."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import StackTrace


@dataclass
class SummaryReport:
    total_traces: int
    total_frames: int
    avg_depth: float
    most_common_exception: Optional[str]
    most_common_file: Optional[str]
    most_common_function: Optional[str]
    exception_counts: Counter = field(default_factory=Counter)
    file_counts: Counter = field(default_factory=Counter)
    function_counts: Counter = field(default_factory=Counter)

    @property
    def summary_line(self) -> str:
        return (
            f"{self.total_traces} trace(s), "
            f"{self.total_frames} frame(s), "
            f"avg depth {self.avg_depth:.1f}"
        )


def summarize_traces(traces: List[StackTrace]) -> SummaryReport:
    """Compute a SummaryReport from a list of StackTrace objects."""
    if not traces:
        return SummaryReport(
            total_traces=0,
            total_frames=0,
            avg_depth=0.0,
            most_common_exception=None,
            most_common_file=None,
            most_common_function=None,
        )

    exception_counts: Counter = Counter()
    file_counts: Counter = Counter()
    function_counts: Counter = Counter()
    total_frames = 0

    for trace in traces:
        exception_counts[trace.exception_type] += 1
        total_frames += len(trace.frames)
        for frame in trace.frames:
            file_counts[frame.filename] += 1
            function_counts[frame.function] += 1

    avg_depth = total_frames / len(traces)

    def _top(counter: Counter) -> Optional[str]:
        return counter.most_common(1)[0][0] if counter else None

    return SummaryReport(
        total_traces=len(traces),
        total_frames=total_frames,
        avg_depth=avg_depth,
        most_common_exception=_top(exception_counts),
        most_common_file=_top(file_counts),
        most_common_function=_top(function_counts),
        exception_counts=exception_counts,
        file_counts=file_counts,
        function_counts=function_counts,
    )


def format_summary(report: SummaryReport, *, colour: bool = True) -> str:
    """Render a SummaryReport as a printable string."""
    BOLD = "\033[1m" if colour else ""
    CYAN = "\033[36m" if colour else ""
    RESET = "\033[0m" if colour else ""

    lines = [
        f"{BOLD}=== Stack Trace Summary ==={RESET}",
        f"  Traces          : {CYAN}{report.total_traces}{RESET}",
        f"  Total frames    : {CYAN}{report.total_frames}{RESET}",
        f"  Avg depth       : {CYAN}{report.avg_depth:.1f}{RESET}",
        f"  Top exception   : {CYAN}{report.most_common_exception or 'n/a'}{RESET}",
        f"  Top file        : {CYAN}{report.most_common_file or 'n/a'}{RESET}",
        f"  Top function    : {CYAN}{report.most_common_function or 'n/a'}{RESET}",
    ]
    return "\n".join(lines)
