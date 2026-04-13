"""Batch processing of multiple stack traces into grouped result sets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class BatchOptions:
    max_batch_size: int = 50
    group_by_exception: bool = False
    label: Optional[str] = None


@dataclass
class BatchEntry:
    index: int
    trace: StackTrace
    group_key: str

    def __str__(self) -> str:
        return f"[{self.index}] {self.group_key}: {self.trace.exception_type}"


@dataclass
class BatchReport:
    entries: List[BatchEntry] = field(default_factory=list)
    options: BatchOptions = field(default_factory=BatchOptions)
    label: Optional[str] = None

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def groups(self) -> List[str]:
        seen: list = []
        for e in self.entries:
            if e.group_key not in seen:
                seen.append(e.group_key)
        return seen

    def by_group(self, key: str) -> List[BatchEntry]:
        return [e for e in self.entries if e.group_key == key]

    def summary_line(self) -> str:
        g = len(self.groups)
        return (
            f"Batch '{self.label or 'unnamed'}': "
            f"{self.count} trace(s) across {g} group(s)"
        )


def _group_key(trace: StackTrace, group_by_exception: bool) -> str:
    if group_by_exception:
        return trace.exception_type or "Unknown"
    return "default"


def batch_traces(
    traces: List[StackTrace],
    options: Optional[BatchOptions] = None,
) -> BatchReport:
    opts = options or BatchOptions()
    capped = traces[: opts.max_batch_size]
    entries = [
        BatchEntry(
            index=i,
            trace=t,
            group_key=_group_key(t, opts.group_by_exception),
        )
        for i, t in enumerate(capped)
    ]
    return BatchReport(entries=entries, options=opts, label=opts.label)


def format_batch(report: BatchReport) -> str:
    lines = [report.summary_line()]
    for group in report.groups:
        lines.append(f"  [{group}]")
        for entry in report.by_group(group):
            lines.append(f"    {entry}")
    return "\n".join(lines)
