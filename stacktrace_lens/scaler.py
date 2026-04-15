"""scaler.py – normalise a collection of traces to a common depth scale.

Given a list of StackTrace objects the scaler computes a *scaled depth*
for every frame so that the deepest trace always maps to 1.0.  Frames in
shorter traces are scaled proportionally, making cross-trace depth
comparisons meaningful.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class ScaledFrame:
    frame: Frame
    depth_index: int        # 0-based position within its trace
    trace_depth: int        # total frames in the source trace
    scaled_depth: float     # depth_index / (max_depth - 1), range [0, 1]

    def __str__(self) -> str:  # pragma: no cover
        fname = self.frame.filename or "<unknown>"
        func = self.frame.function or "<module>"
        return f"{fname}:{self.frame.lineno} {func} (scaled={self.scaled_depth:.3f})"


@dataclass
class ScaleReport:
    traces: List[StackTrace]
    scaled: List[List[ScaledFrame]]
    max_depth: int

    # ------------------------------------------------------------------ #
    @property
    def total_frames(self) -> int:
        return sum(len(g) for g in self.scaled)

    @property
    def trace_count(self) -> int:
        return len(self.traces)

    def summary_line(self) -> str:
        return (
            f"{self.trace_count} trace(s) scaled "
            f"(max_depth={self.max_depth}, total_frames={self.total_frames})"
        )

    def flat(self) -> List[ScaledFrame]:
        """Return all ScaledFrames in a single flat list."""
        return [sf for group in self.scaled for sf in group]


def scale_traces(traces: List[StackTrace]) -> ScaleReport:
    """Scale every frame across *traces* to a normalised depth in [0, 1]."""
    if not traces:
        return ScaleReport(traces=[], scaled=[], max_depth=0)

    max_depth: int = max(len(t.frames) for t in traces)

    scaled_groups: List[List[ScaledFrame]] = []
    for trace in traces:
        group: List[ScaledFrame] = []
        n =for idx, frame in enumerate(trace.frames):
            if max_depth <= 1:
                sd = 0.0
            else:
                sd = idx / (max_depth - 1)
            group.append(
                ScaledFrame(
                    frame=frame,
                    depth_index=idx,
                    trace_depth=n,
                    scaled_depth=round(sd, 6),
                )
            )
        scaled_groups.append(group)

    return ScaleReport(traces=traces, scaled=scaled_groups, max_depth=max_depth)
