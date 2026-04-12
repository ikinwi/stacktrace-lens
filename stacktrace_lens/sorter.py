"""Sort a collection of stack traces by various criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


class SortKey(str, Enum):
    DEPTH = "depth"
    EXCEPTION = "exception"
    FILE = "file"
    NATURAL = "natural"


@dataclass
class SortOptions:
    key: SortKey = SortKey.NATURAL
    reverse: bool = False


@dataclass
class SortReport:
    traces: List[StackTrace]
    key: SortKey
    reversed: bool

    @property
    def count(self) -> int:
        return len(self.traces)

    def summary_line(self) -> str:
        direction = "descending" if self.reversed else "ascending"
        return (
            f"Sorted {self.count} trace(s) by '{self.key.value}' ({direction})."
        )


def _sort_key_fn(key: SortKey):
    """Return a callable suitable for use as the *key* argument to sorted()."""
    if key == SortKey.DEPTH:
        return lambda t: len(t.frames)
    if key == SortKey.EXCEPTION:
        return lambda t: (t.exception_type or "").lower()
    if key == SortKey.FILE:
        first_file = lambda t: (t.frames[0].filename if t.frames else "")
        return first_file
    # SortKey.NATURAL — preserve original order (stable sort on constant key)
    return lambda t: 0


def sort_traces(
    traces: List[StackTrace],
    options: Optional[SortOptions] = None,
) -> SortReport:
    """Sort *traces* according to *options* and return a :class:`SortReport`."""
    if options is None:
        options = SortOptions()

    key_fn = _sort_key_fn(options.key)
    sorted_traces = sorted(traces, key=key_fn, reverse=options.reverse)

    return SortReport(
        traces=sorted_traces,
        key=options.key,
        reversed=options.reverse,
    )


def format_sort(report: SortReport) -> str:
    """Return a human-readable string describing the sort result."""
    lines = [report.summary_line()]
    for idx, trace in enumerate(report.traces, start=1):
        depth = len(trace.frames)
        exc = trace.exception_type or "<unknown>"
        lines.append(f"  {idx:>3}. [{depth} frame(s)] {exc}")
    return "\n".join(lines)
