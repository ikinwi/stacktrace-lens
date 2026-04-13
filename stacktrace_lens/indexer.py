"""Index stack trace frames by file, function, and line for fast lookup."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class IndexEntry:
    frame: Frame
    trace_index: int  # position of the owning trace in the input list
    frame_index: int  # position within that trace

    def __str__(self) -> str:
        return (
            f"{self.frame.filename}:{self.frame.lineno} "
            f"in {self.frame.function} "
            f"(trace={self.trace_index}, frame={self.frame_index})"
        )


@dataclass
class IndexReport:
    entries: List[IndexEntry] = field(default_factory=list)
    _by_file: Dict[str, List[IndexEntry]] = field(default_factory=lambda: defaultdict(list), repr=False)
    _by_function: Dict[str, List[IndexEntry]] = field(default_factory=lambda: defaultdict(list), repr=False)

    @property
    def total(self) -> int:
        return len(self.entries)

    def by_file(self, filename: str) -> List[IndexEntry]:
        return list(self._by_file.get(filename, []))

    def by_function(self, function: str) -> List[IndexEntry]:
        return list(self._by_function.get(function, []))

    def files(self) -> List[str]:
        return sorted(self._by_file.keys())

    def functions(self) -> List[str]:
        return sorted(self._by_function.keys())


def index_traces(traces: List[StackTrace]) -> IndexReport:
    """Build a searchable index from a list of stack traces."""
    report = IndexReport()
    for trace_idx, trace in enumerate(traces):
        for frame_idx, frame in enumerate(trace.frames):
            entry = IndexEntry(
                frame=frame,
                trace_index=trace_idx,
                frame_index=frame_idx,
            )
            report.entries.append(entry)
            report._by_file[frame.filename].append(entry)
            report._by_function[frame.function].append(entry)
    return report


def format_index(report: IndexReport, query_file: Optional[str] = None, query_fn: Optional[str] = None) -> str:
    """Render a human-readable summary of the index or a filtered view."""
    lines: List[str] = []
    lines.append(f"Index: {report.total} frame(s) across {len(report.files())} file(s)")
    if query_file:
        hits = report.by_file(query_file)
        lines.append(f"  File '{query_file}': {len(hits)} hit(s)")
        for e in hits:
            lines.append(f"    {e}")
    if query_fn:
        hits = report.by_function(query_fn)
        lines.append(f"  Function '{query_fn}': {len(hits)} hit(s)")
        for e in hits:
            lines.append(f"    {e}")
    if not query_file and not query_fn:
        for fname in report.files():
            lines.append(f"  {fname}: {len(report.by_file(fname))} frame(s)")
    return "\n".join(lines)
