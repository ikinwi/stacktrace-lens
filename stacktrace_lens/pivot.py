"""pivot.py – pivot stack traces by a chosen dimension.

Groups a list of StackTrace objects by a key (exception type, top file,
or top function) and returns a PivotReport with per-group counts and
representative traces.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from stacktrace_lens.parser import StackTrace

PivotKey = Literal["exception", "file", "function"]


@dataclass
class PivotGroup:
    key: str
    traces: List[StackTrace] = field(default_factory=list)

    @property
    def count(self) -> int:  # noqa: D401
        return len(self.traces)

    @property
    def representative(self) -> Optional[StackTrace]:
        return self.traces[0] if self.traces else None

    def __str__(self) -> str:
        return f"{self.key} ({self.count} trace{'s' if self.count != 1 else ''})"


@dataclass
class PivotReport:
    pivot_key: PivotKey
    groups: List[PivotGroup] = field(default_factory=list)

    @property
    def total_traces(self) -> int:
        return sum(g.count for g in self.groups)

    @property
    def group_count(self) -> int:
        return len(self.groups)

    def by_key(self, key: str) -> Optional[PivotGroup]:
        for g in self.groups:
            if g.key == key:
                return g
        return None

    def summary_line(self) -> str:
        return (
            f"Pivoted {self.total_traces} trace(s) into "
            f"{self.group_count} group(s) by '{self.pivot_key}'."
        )


def _key_for(trace: StackTrace, pivot: PivotKey) -> str:
    if pivot == "exception":
        return trace.exception_type or "<unknown>"
    if not trace.frames:
        return "<no frames>"
    top = trace.frames[-1]
    if pivot == "file":
        return top.filename or "<unknown>"
    return top.function or "<unknown>"


def pivot_traces(traces: List[StackTrace], pivot: PivotKey = "exception") -> PivotReport:
    """Group *traces* by *pivot* key and return a :class:`PivotReport`."""
    buckets: Dict[str, List[StackTrace]] = defaultdict(list)
    for trace in traces:
        buckets[_key_for(trace, pivot)].append(trace)

    groups = [
        PivotGroup(key=k, traces=v)
        for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1]))
    ]
    return PivotReport(pivot_key=pivot, groups=groups)


def format_pivot(report: PivotReport) -> str:
    """Return a plain-text summary of a :class:`PivotReport`."""
    lines = [report.summary_line()]
    for g in report.groups:
        lines.append(f"  {g}")
    return "\n".join(lines)
