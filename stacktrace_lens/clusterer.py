"""Cluster multiple stack traces by structural similarity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from stacktrace_lens.parser import StackTrace
from stacktrace_lens.fingerprinter import fingerprint_trace


@dataclass
class ClusterEntry:
    fingerprint: str
    traces: List[StackTrace] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.traces)

    @property
    def representative(self) -> StackTrace:
        return self.traces[0]

    def __str__(self) -> str:  # pragma: no cover
        return f"ClusterEntry(fp={self.fingerprint[:8]}, count={self.count})"


@dataclass
class ClusterReport:
    clusters: List[ClusterEntry]

    @property
    def total_traces(self) -> int:
        return sum(c.count for c in self.clusters)

    @property
    def total_clusters(self) -> int:
        return len(self.clusters)

    def largest(self) -> ClusterEntry | None:
        if not self.clusters:
            return None
        return max(self.clusters, key=lambda c: c.count)

    def ranked(self) -> List[ClusterEntry]:
        return sorted(self.clusters, key=lambda c: c.count, reverse=True)


def cluster_traces(traces: List[StackTrace]) -> ClusterReport:
    """Group traces by fingerprint, returning a ClusterReport."""
    buckets: Dict[str, ClusterEntry] = {}
    for trace in traces:
        fp = fingerprint_trace(trace).full
        if fp not in buckets:
            buckets[fp] = ClusterEntry(fingerprint=fp)
        buckets[fp].traces.append(trace)
    return ClusterReport(clusters=list(buckets.values()))


def format_cluster_report(report: ClusterReport, *, colour: bool = True) -> str:
    """Return a human-readable summary of the cluster report."""
    reset = "\033[0m" if colour else ""
    bold = "\033[1m" if colour else ""
    cyan = "\033[36m" if colour else ""
    yellow = "\033[33m" if colour else ""

    lines: List[str] = [
        f"{bold}Cluster Report{reset}",
        f"  Total traces : {cyan}{report.total_traces}{reset}",
        f"  Total clusters: {cyan}{report.total_clusters}{reset}",
        "",
    ]
    for i, entry in enumerate(report.ranked(), 1):
        rep = entry.representative
        lines.append(
            f"  {yellow}#{i}{reset} [{entry.fingerprint[:12]}]"
            f" — {bold}{rep.exception_type}{reset}"
            f" × {cyan}{entry.count}{reset}"
        )
        if rep.exception_message:
            snippet = rep.exception_message[:60]
            if len(rep.exception_message) > 60:
                snippet += "…"
            lines.append(f"      {snippet}")
    return "\n".join(lines)
