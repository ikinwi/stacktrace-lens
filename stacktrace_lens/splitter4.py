"""Split a stack trace into layers based on call depth buckets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class DepthLayer:
    """A contiguous slice of frames sharing the same depth bucket."""

    bucket: str  # e.g. "0-4", "5-9", …
    frames: List[Frame] = field(default_factory=list)

    @property
    def count(self) -> int:  # noqa: D401
        return len(self.frames)

    def __str__(self) -> str:
        return f"[{self.bucket}] {self.count} frame(s)"


@dataclass
class LayerReport:
    """Result of splitting a trace into depth layers."""

    exception_type: str
    exception_message: str
    layers: List[DepthLayer] = field(default_factory=list)
    bucket_size: int = 5

    @property
    def count(self) -> int:  # noqa: D401
        return len(self.layers)

    @property
    def total_frames(self) -> int:
        return sum(lay.count for lay in self.layers)

    def summary_line(self) -> str:
        return (
            f"{self.exception_type}: {self.total_frames} frame(s) "
            f"across {self.count} layer(s) "
            f"(bucket_size={self.bucket_size})"
        )

    def largest_layer(self) -> DepthLayer | None:
        """Return the depth layer containing the most frames, or None if empty."""
        if not self.layers:
            return None
        return max(self.layers, key=lambda lay: lay.count)


def _bucket_label(index: int, bucket_size: int) -> str:
    lo = (index // bucket_size) * bucket_size
    hi = lo + bucket_size - 1
    return f"{lo}-{hi}"


def split_by_depth(trace: StackTrace, bucket_size: int = 5) -> LayerReport:
    """Group frames into fixed-size depth buckets.

    Args:
        trace: The parsed stack trace to split.
        bucket_size: Number of consecutive frame indices per bucket.  Must be
            at least 1.

    Returns:
        A :class:`LayerReport` whose ``layers`` list contains one
        :class:`DepthLayer` per distinct bucket encountered in *trace*.
    """
    if bucket_size < 1:
        raise ValueError("bucket_size must be >= 1")

    report = LayerReport(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        bucket_size=bucket_size,
    )

    current_label: str | None = None
    current_layer: DepthLayer | None = None

    for idx, frame in enumerate(trace.frames):
        label = _bucket_label(idx, bucket_size)
        if label != current_label:
            current_layer = DepthLayer(bucket=label)
            report.layers.append(current_layer)
            current_label = label
        assert current_layer is not None
        current_layer.frames.append(frame)

    return report
