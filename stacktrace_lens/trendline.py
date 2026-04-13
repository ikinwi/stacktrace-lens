"""Trendline: detect frequency trends across a sequence of timestamped traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from collections import Counter

from stacktrace_lens.timeline import TimestampedTrace


@dataclass
class TrendPoint:
    """A single data point in a trend series."""
    label: str
    count: int

    def __str__(self) -> str:
        return f"{self.label}: {self.count}"


@dataclass
class TrendReport:
    """Report describing exception frequency trends."""
    points: List[TrendPoint] = field(default_factory=list)
    most_frequent_exception: Optional[str] = None
    total_traces: int = 0
    rising: bool = False

    @property
    def count(self) -> int:
        return len(self.points)

    def summary_line(self) -> str:
        direction = "rising" if self.rising else "stable/falling"
        return (
            f"Trend: {self.total_traces} traces, "
            f"top exception={self.most_frequent_exception or 'N/A'}, "
            f"direction={direction}"
        )


def _bucket_label(entry: TimestampedTrace, bucket_size: int) -> str:
    """Return a bucket label based on truncated Unix timestamp."""
    ts = int(entry.timestamp.timestamp())
    bucket = (ts // bucket_size) * bucket_size
    return str(bucket)


def build_trendline(
    entries: List[TimestampedTrace],
    bucket_size: int = 60,
) -> TrendReport:
    """Aggregate entries into bucketed TrendPoints and detect rising trend."""
    if not entries:
        return TrendReport()

    bucket_counts: Counter = Counter()
    exception_counts: Counter = Counter()

    for entry in entries:
        label = _bucket_label(entry, bucket_size)
        bucket_counts[label] += 1
        exception_counts[entry.trace.exception_type] += 1

    sorted_labels = sorted(bucket_counts.keys())
    points = [TrendPoint(label=lbl, count=bucket_counts[lbl]) for lbl in sorted_labels]

    rising = False
    if len(points) >= 2:
        mid = len(points) // 2
        first_half = sum(p.count for p in points[:mid])
        second_half = sum(p.count for p in points[mid:])
        rising = second_half > first_half

    most_common = exception_counts.most_common(1)
    top_exception = most_common[0][0] if most_common else None

    return TrendReport(
        points=points,
        most_frequent_exception=top_exception,
        total_traces=len(entries),
        rising=rising,
    )


def format_trendline(report: TrendReport) -> str:
    """Render a TrendReport as a plain-text string."""
    lines = [report.summary_line(), ""]
    for point in report.points:
        bar = "#" * min(point.count, 40)
        lines.append(f"  {point.label:>12}  {bar} ({point.count})")
    return "\n".join(lines)
