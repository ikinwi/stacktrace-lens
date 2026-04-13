"""chainer.py – detect and model exception chains (raise X from Y / implicit chaining)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class ChainLink:
    """One exception in a chain."""
    trace: StackTrace
    cause: Optional[str]          # 'explicit' | 'implicit' | None
    cause_message: Optional[str]  # raw 'During handling …' / 'The above …' text

    def __str__(self) -> str:  # pragma: no cover
        label = f" [{self.cause}]" if self.cause else ""
        return f"ChainLink({self.trace.exception_type}{label})"


@dataclass
class ChainReport:
    links: List[ChainLink] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.links)

    @property
    def is_chained(self) -> bool:
        return self.count > 1

    def summary_line(self) -> str:
        if not self.is_chained:
            return "No exception chain detected."
        kinds = [lk.cause for lk in self.links if lk.cause]
        label = ", ".join(kinds) if kinds else "unknown"
        return f"Exception chain: {self.count} links ({label})."


_EXPLICIT_MARKERS = (
    "The above exception was the direct cause",
)
_IMPLICIT_MARKERS = (
    "During handling of the above exception",
)


def chain_traces(traces: List[StackTrace]) -> ChainReport:
    """Build a ChainReport from an ordered list of StackTrace objects.

    The list is expected to be in chronological order (outermost last),
    as produced by ``splitter.split_trace``.
    """
    if not traces:
        return ChainReport()

    links: List[ChainLink] = []
    for idx, trace in enumerate(traces):
        cause: Optional[str] = None
        cause_msg: Optional[str] = None

        if idx > 0:
            # Inspect raw text stored on the previous split boundary if present
            raw = getattr(trace, "_chain_marker", "") or ""
            if any(m in raw for m in _EXPLICIT_MARKERS):
                cause = "explicit"
                cause_msg = raw.strip()
            elif any(m in raw for m in _IMPLICIT_MARKERS):
                cause = "implicit"
                cause_msg = raw.strip()
            else:
                cause = "implicit"  # default assumption when chained

        links.append(ChainLink(trace=trace, cause=cause, cause_message=cause_msg))

    return ChainReport(links=links)


def format_chain(report: ChainReport) -> str:
    """Return a plain-text summary of the chain report."""
    lines: List[str] = [report.summary_line()]
    for i, link in enumerate(report.links, 1):
        cause_label = f" via {link.cause} cause" if link.cause else ""
        lines.append(
            f"  [{i}] {link.trace.exception_type}: {link.trace.exception_message}{cause_label}"
            f" ({len(link.trace.frames)} frame(s))"
        )
    return "\n".join(lines)
