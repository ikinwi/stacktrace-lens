"""Digest multiple stack traces into a concise statistical summary."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import StackTrace


@dataclass
class DigestReport:
    total_traces: int
    exception_counts: Counter
    file_counts: Counter
    function_counts: Counter
    avg_depth: float
    max_depth: int
    most_common_exception: Optional[str]
    most_common_file: Optional[str]

    def top_exceptions(self, n: int = 5) -> List[tuple]:
        return self.exception_counts.most_common(n)

    def top_files(self, n: int = 5) -> List[tuple]:
        return self.file_counts.most_common(n)


def digest_traces(traces: List[StackTrace]) -> DigestReport:
    """Aggregate a list of StackTrace objects into a DigestReport."""
    if not traces:
        return DigestReport(
            total_traces=0,
            exception_counts=Counter(),
            file_counts=Counter(),
            function_counts=Counter(),
            avg_depth=0.0,
            max_depth=0,
            most_common_exception=None,
            most_common_file=None,
        )

    exc_counter: Counter = Counter()
    file_counter: Counter = Counter()
    func_counter: Counter = Counter()
    depths: List[int] = []

    for trace in traces:
        exc_counter[trace.exception_type] += 1
        depths.append(len(trace.frames))
        for frame in trace.frames:
            file_counter[frame.filename] += 1
            func_counter[frame.function] += 1

    avg_depth = sum(depths) / len(depths) if depths else 0.0
    max_depth = max(depths) if depths else 0

    most_common_exc = exc_counter.most_common(1)[0][0] if exc_counter else None
    most_common_file = file_counter.most_common(1)[0][0] if file_counter else None

    return DigestReport(
        total_traces=len(traces),
        exception_counts=exc_counter,
        file_counts=file_counter,
        function_counts=func_counter,
        avg_depth=avg_depth,
        max_depth=max_depth,
        most_common_exception=most_common_exc,
        most_common_file=most_common_file,
    )


def format_digest(report: DigestReport, top_n: int = 3) -> str:
    """Return a human-readable string representation of a DigestReport."""
    lines = [
        f"Traces analysed : {report.total_traces}",
        f"Avg depth       : {report.avg_depth:.1f} frames",
        f"Max depth       : {report.max_depth} frames",
        "",
        "Top exceptions:",
    ]
    for exc, cnt in report.top_exceptions(top_n):
        lines.append(f"  {cnt:>4}x  {exc}")
    lines.append("")
    lines.append("Top files:")
    for fname, cnt in report.top_files(top_n):
        lines.append(f"  {cnt:>4}x  {fname}")
    return "\n".join(lines)
