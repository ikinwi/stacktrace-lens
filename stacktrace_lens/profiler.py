"""Frame-level hotspot profiler: counts how often each file/function
appears across a collection of StackTrace objects and surfaces the
most-repeated locations as "hotspots"."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Sequence

from .parser import StackTrace


@dataclass
class Hotspot:
    filename: str
    function: str
    hit_count: int

    def __str__(self) -> str:
        return f"{self.filename}::{self.function} ({self.hit_count} hit{'s' if self.hit_count != 1 else ''})"


@dataclass
class ProfileReport:
    total_traces: int
    total_frames: int
    hotspots: List[Hotspot] = field(default_factory=list)


def profile_traces(
    traces: Sequence[StackTrace],
    top_n: int = 10,
) -> ProfileReport:
    """Aggregate frame occurrences across *traces* and return a ProfileReport."""
    counter: Counter[tuple[str, str]] = Counter()
    total_frames = 0

    for trace in traces:
        for frame in trace.frames:
            key = (frame.filename, frame.function)
            counter[key] += 1
            total_frames += 1

    hotspots = [
        Hotspot(filename=fname, function=func, hit_count=count)
        for (fname, func), count in counter.most_common(top_n)
    ]

    return ProfileReport(
        total_traces=len(traces),
        total_frames=total_frames,
        hotspots=hotspots,
    )


def format_profile(report: ProfileReport, colour: bool = True) -> str:
    """Render a ProfileReport as a human-readable string."""
    _R = "\033[0m" if colour else ""
    _B = "\033[1m" if colour else ""
    _Y = "\033[33m" if colour else ""
    _C = "\033[36m" if colour else ""

    lines: list[str] = [
        f"{_B}Profile Report{_R}",
        f"  Traces analysed : {report.total_traces}",
        f"  Total frames    : {report.total_frames}",
        f"  Top hotspots    :",
    ]
    for rank, hs in enumerate(report.hotspots, 1):
        lines.append(
            f"    {_Y}{rank:>2}.{_R} {_C}{hs.filename}{_R}::{hs.function}  "
            f"— {_B}{hs.hit_count}{_R} hit{'s' if hs.hit_count != 1 else ''}"
        )
    if not report.hotspots:
        lines.append("    (no frames found)")
    return "\n".join(lines)
