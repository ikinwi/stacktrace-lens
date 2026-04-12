"""Merge multiple stack traces into a unified report."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import List, Optional

from stacktrace_lens.parser import StackTrace, Frame


@dataclass
class MergeReport:
    """Result of merging multiple stack traces."""
    total_traces: int
    merged_frames: List[Frame]
    exception_counts: Counter
    common_exception: Optional[str]
    common_file: Optional[str]
    unique_exceptions: int
    unique_files: int

    def summary_line(self) -> str:
        exc = self.common_exception or "unknown"
        return (
            f"{self.total_traces} trace(s) merged; "
            f"dominant exception: {exc}; "
            f"{len(self.merged_frames)} combined frame(s)"
        )


def _most_common(counter: Counter) -> Optional[str]:
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def merge_traces(traces: List[StackTrace]) -> MergeReport:
    """Merge *traces* into a single :class:`MergeReport`."""
    if not traces:
        return MergeReport(
            total_traces=0,
            merged_frames=[],
            exception_counts=Counter(),
            common_exception=None,
            common_file=None,
            unique_exceptions=0,
            unique_files=0,
        )

    exc_counter: Counter = Counter()
    file_counter: Counter = Counter()
    all_frames: List[Frame] = []

    for trace in traces:
        if trace.exception_type:
            exc_counter[trace.exception_type] += 1
        for frame in trace.frames:
            all_frames.append(frame)
            if frame.filename:
                file_counter[frame.filename] += 1

    return MergeReport(
        total_traces=len(traces),
        merged_frames=all_frames,
        exception_counts=exc_counter,
        common_exception=_most_common(exc_counter),
        common_file=_most_common(file_counter),
        unique_exceptions=len(exc_counter),
        unique_files=len(file_counter),
    )


def format_merge(report: MergeReport, *, colour: bool = False) -> str:
    """Return a human-readable string for *report*."""
    reset = "\033[0m" if colour else ""
    bold  = "\033[1m"  if colour else ""
    cyan  = "\033[36m" if colour else ""

    lines = [
        f"{bold}Merge Report{reset}",
        f"  Total traces   : {report.total_traces}",
        f"  Combined frames: {len(report.merged_frames)}",
        f"  Unique exceptions: {report.unique_exceptions}",
        f"  Unique files     : {report.unique_files}",
    ]
    if report.common_exception:
        lines.append(f"  Dominant exception: {cyan}{report.common_exception}{reset}")
    if report.common_file:
        lines.append(f"  Most common file  : {cyan}{report.common_file}{reset}")
    return "\n".join(lines)
