"""stacker.py – builds a call-stack depth profile from one or more traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class DepthBucket:
    """Aggregated information for traces that share the same frame depth."""

    depth: int
    count: int = 0
    exception_types: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"depth={self.depth} count={self.count}"


@dataclass
class StackProfile:
    """Result returned by :func:`build_stack_profile`."""

    total_traces: int
    buckets: List[DepthBucket]
    min_depth: Optional[int]
    max_depth: Optional[int]
    avg_depth: float

    # ------------------------------------------------------------------
    def summary_line(self) -> str:
        if self.total_traces == 0:
            return "No traces analysed."
        return (
            f"{self.total_traces} trace(s) | "
            f"depth min={self.min_depth} max={self.max_depth} "
            f"avg={self.avg_depth:.1f}"
        )

    def deepest_bucket(self) -> Optional[DepthBucket]:
        """Return the bucket with the greatest depth, or *None* if empty."""
        return max(self.buckets, key=lambda b: b.depth, default=None)

    def most_common_bucket(self) -> Optional[DepthBucket]:
        """Return the bucket that contains the most traces."""
        return max(self.buckets, key=lambda b: b.count, default=None)


def build_stack_profile(traces: List[StackTrace]) -> StackProfile:
    """Analyse *traces* and return a :class:`StackProfile`."""
    if not traces:
        return StackProfile(
            total_traces=0,
            buckets=[],
            min_depth=None,
            max_depth=None,
            avg_depth=0.0,
        )

    bucket_map: dict[int, DepthBucket] = {}
    for trace in traces:
        depth = len(trace.frames)
        if depth not in bucket_map:
            bucket_map[depth] = DepthBucket(depth=depth)
        bucket = bucket_map[depth]
        bucket.count += 1
        if trace.exception_type:
            bucket.exception_types.append(trace.exception_type)

    buckets = sorted(bucket_map.values(), key=lambda b: b.depth)
    depths = [b.depth for b in buckets for _ in range(b.count)]

    return StackProfile(
        total_traces=len(traces),
        buckets=buckets,
        min_depth=min(depths),
        max_depth=max(depths),
        avg_depth=sum(depths) / len(depths),
    )


def format_profile(profile: StackProfile, *, colour: bool = False) -> str:
    """Return a human-readable string representation of *profile*."""
    _R = "\033[0m" if colour else ""
    _B = "\033[1m" if colour else ""
    _C = "\033[36m" if colour else ""

    lines: List[str] = [f"{_B}{profile.summary_line()}{_R}"]
    for bucket in profile.buckets:
        bar = "█" * min(bucket.count, 40)
        lines.append(f"  {_C}depth {bucket.depth:>3}{_R}  {bar} {bucket.count}")
    return "\n".join(lines)
