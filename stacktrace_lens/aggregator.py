"""Aggregate multiple stack traces into a concise report."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import StackTrace


@dataclass
class AggregationReport:
    total_traces: int
    exception_counts: Counter
    file_counts: Counter
    function_counts: Counter
    most_common_exception: Optional[str]
    most_common_file: Optional[str]
    most_common_function: Optional[str]
    traces: List[StackTrace] = field(repr=False)


def _most_common_key(counter: Counter) -> Optional[str]:
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def aggregate_traces(traces: List[StackTrace]) -> AggregationReport:
    """Build an AggregationReport from a list of StackTrace objects."""
    exception_counts: Counter = Counter()
    file_counts: Counter = Counter()
    function_counts: Counter = Counter()

    for trace in traces:
        if trace.exception_type:
            exception_counts[trace.exception_type] += 1
        for frame in trace.frames:
            file_counts[frame.filename] += 1
            function_counts[frame.function] += 1

    return AggregationReport(
        total_traces=len(traces),
        exception_counts=exception_counts,
        file_counts=file_counts,
        function_counts=function_counts,
        most_common_exception=_most_common_key(exception_counts),
        most_common_file=_most_common_key(file_counts),
        most_common_function=_most_common_key(function_counts),
        traces=traces,
    )


def format_aggregation(report: AggregationReport, top_n: int = 5) -> str:
    """Return a human-readable summary of the aggregation report."""
    lines = [
        f"Aggregation Report ({report.total_traces} trace(s))",
        "=" * 40,
        f"Top {top_n} exception types:",
    ]
    for exc, count in report.exception_counts.most_common(top_n):
        lines.append(f"  {exc}: {count}")
    lines.append(f"Top {top_n} files:")
    for fname, count in report.file_counts.most_common(top_n):
        lines.append(f"  {fname}: {count}")
    lines.append(f"Top {top_n} functions:")
    for func, count in report.function_counts.most_common(top_n):
        lines.append(f"  {func}: {count}")
    return "\n".join(lines)
