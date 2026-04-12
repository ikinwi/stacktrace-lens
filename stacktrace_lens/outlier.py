"""Detect outlier frames that appear rarely across a collection of traces."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace


@dataclass
class OutlierFrame:
    frame: Frame
    occurrences: int
    total_traces: int

    @property
    def frequency(self) -> float:
        """Fraction of traces in which this frame appears (0.0 – 1.0)."""
        if self.total_traces == 0:
            return 0.0
        return self.occurrences / self.total_traces

    def __str__(self) -> str:
        pct = self.frequency * 100
        return (
            f"{self.frame.filename}:{self.frame.lineno} "
            f"in {self.frame.function} "
            f"[{self.occurrences}/{self.total_traces} traces, {pct:.1f}%]"
        )


@dataclass
class OutlierReport:
    total_traces: int
    threshold: float
    outliers: List[OutlierFrame] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.outliers)

    def rarest(self) -> Optional[OutlierFrame]:
        if not self.outliers:
            return None
        return min(self.outliers, key=lambda o: o.frequency)


def _frame_key(frame: Frame) -> str:
    return f"{frame.filename}:{frame.lineno}:{frame.function}"


def detect_outliers(
    traces: List[StackTrace],
    threshold: float = 0.2,
) -> OutlierReport:
    """Return frames whose frequency across *traces* is at or below *threshold*.

    Parameters
    ----------
    traces:
        Collection of parsed stack traces to analyse.
    threshold:
        Maximum frequency (0.0–1.0) for a frame to be considered an outlier.
        Defaults to 0.2 (appears in 20 % or fewer traces).
    """
    total = len(traces)
    counter: Counter[str] = Counter()
    key_to_frame: dict[str, Frame] = {}

    for trace in traces:
        seen_in_trace: set[str] = set()
        for frame in trace.frames:
            key = _frame_key(frame)
            if key not in seen_in_trace:
                counter[key] += 1
                seen_in_trace.add(key)
            key_to_frame[key] = frame

    outliers: List[OutlierFrame] = []
    for key, occurrences in counter.items():
        freq = occurrences / total if total else 0.0
        if freq <= threshold:
            outliers.append(
                OutlierFrame(
                    frame=key_to_frame[key],
                    occurrences=occurrences,
                    total_traces=total,
                )
            )

    outliers.sort(key=lambda o: o.frequency)
    return OutlierReport(total_traces=total, threshold=threshold, outliers=outliers)


def format_outliers(report: OutlierReport, *, colour: bool = False) -> str:
    """Render an *OutlierReport* as a human-readable string."""
    lines: List[str] = [
        f"Outlier frames (threshold ≤ {report.threshold * 100:.0f}%)",
        f"Traces analysed : {report.total_traces}",
        f"Outliers found  : {report.count}",
        "",
    ]
    if not report.outliers:
        lines.append("  (none)")
    else:
        for entry in report.outliers:
            lines.append(f"  {entry}")
    return "\n".join(lines)
