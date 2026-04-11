"""Heatmap: rank files and functions by how often they appear across traces."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Sequence

from stacktrace_lens.parser import StackTrace


@dataclass
class HeatmapEntry:
    label: str
    count: int
    percentage: float

    def __str__(self) -> str:  # pragma: no cover
        bar = "█" * min(int(self.percentage / 5), 20)
        return f"{self.label:<45} {self.count:>4}  {bar} {self.percentage:.1f}%"


@dataclass
class HeatmapReport:
    total_frames: int
    by_file: List[HeatmapEntry] = field(default_factory=list)
    by_function: List[HeatmapEntry] = field(default_factory=list)


def _entries_from_counter(counter: Counter, total: int) -> List[HeatmapEntry]:
    entries: List[HeatmapEntry] = []
    for label, cnt in counter.most_common():
        pct = (cnt / total * 100) if total else 0.0
        entries.append(HeatmapEntry(label=label, count=cnt, percentage=pct))
    return entries


def build_heatmap(traces: Sequence[StackTrace]) -> HeatmapReport:
    """Aggregate frame counts across *traces* and return a HeatmapReport."""
    file_counter: Counter = Counter()
    func_counter: Counter = Counter()
    total = 0

    for trace in traces:
        for frame in trace.frames:
            file_counter[frame.filename] += 1
            func_counter[frame.function] += 1
            total += 1

    return HeatmapReport(
        total_frames=total,
        by_file=_entries_from_counter(file_counter, total),
        by_function=_entries_from_counter(func_counter, total),
    )


def format_heatmap(report: HeatmapReport, top_n: int = 10) -> str:
    """Render a HeatmapReport as a plain-text string."""
    lines: List[str] = []
    lines.append(f"Heatmap  (total frames: {report.total_frames})")
    lines.append("")

    lines.append("── Top files ──")
    for entry in report.by_file[:top_n]:
        lines.append(str(entry))
    if not report.by_file:
        lines.append("  (no data)")

    lines.append("")
    lines.append("── Top functions ──")
    for entry in report.by_function[:top_n]:
        lines.append(str(entry))
    if not report.by_function:
        lines.append("  (no data)")

    return "\n".join(lines)
