"""Correlate multiple stack traces by shared frames or exception types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .parser import Frame, StackTrace


@dataclass
class CorrelationGroup:
    """A set of traces that share a common key (file, function, or exception)."""

    key: str
    traces: List[StackTrace] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.traces)


@dataclass
class CorrelationReport:
    """Full correlation report across a collection of traces."""

    by_exception: Dict[str, CorrelationGroup]
    by_file: Dict[str, CorrelationGroup]
    by_function: Dict[str, CorrelationGroup]
    total_traces: int

    def most_common_exception(self) -> Tuple[str, int] | None:
        if not self.by_exception:
            return None
        key = max(self.by_exception, key=lambda k: self.by_exception[k].count)
        return key, self.by_exception[key].count

    def most_common_file(self) -> Tuple[str, int] | None:
        if not self.by_file:
            return None
        key = max(self.by_file, key=lambda k: self.by_file[k].count)
        return key, self.by_file[key].count

    def most_common_function(self) -> Tuple[str, int] | None:
        if not self.by_function:
            return None
        key = max(self.by_function, key=lambda k: self.by_function[k].count)
        return key, self.by_function[key].count


def correlate_traces(traces: List[StackTrace]) -> CorrelationReport:
    """Group traces by exception type, file, and function name."""
    by_exception: Dict[str, CorrelationGroup] = {}
    by_file: Dict[str, CorrelationGroup] = {}
    by_function: Dict[str, CorrelationGroup] = {}

    for trace in traces:
        exc = trace.exception_type or "Unknown"
        by_exception.setdefault(exc, CorrelationGroup(key=exc)).traces.append(trace)

        for frame in trace.frames:
            by_file.setdefault(frame.filename, CorrelationGroup(key=frame.filename)).traces.append(trace)
            by_function.setdefault(frame.function, CorrelationGroup(key=frame.function)).traces.append(trace)

    return CorrelationReport(
        by_exception=by_exception,
        by_file=by_file,
        by_function=by_function,
        total_traces=len(traces),
    )


def format_correlation(report: CorrelationReport) -> str:
    """Render a human-readable summary of the correlation report."""
    lines: List[str] = []
    lines.append(f"Correlation Report  ({report.total_traces} traces)")
    lines.append("=" * 40)

    mc_exc = report.most_common_exception()
    if mc_exc:
        lines.append(f"Most common exception : {mc_exc[0]}  ({mc_exc[1]}x)")

    mc_file = report.most_common_file()
    if mc_file:
        lines.append(f"Most common file      : {mc_file[0]}  ({mc_file[1]}x)")

    mc_fn = report.most_common_function()
    if mc_fn:
        lines.append(f"Most common function  : {mc_fn[0]}  ({mc_fn[1]}x)")

    lines.append("")
    lines.append("Exception breakdown:")
    for key, grp in sorted(report.by_exception.items(), key=lambda kv: -kv[1].count):
        lines.append(f"  {key}: {grp.count}")

    return "\n".join(lines)
