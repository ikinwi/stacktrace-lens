"""Zipper: pair frames from two traces side-by-side for aligned comparison."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class ZippedPair:
    """A single row in the zipped output, holding one frame from each trace."""

    left: Optional[Frame]
    right: Optional[Frame]

    def is_aligned(self) -> bool:
        """True when both sides have a frame with the same file and function."""
        if self.left is None or self.right is None:
            return False
        return (
            self.left.filename == self.right.filename
            and self.left.function == self.right.function
        )

    def __str__(self) -> str:
        def _fmt(f: Optional[Frame]) -> str:
            if f is None:
                return "<missing>"
            fn = f.function or "<module>"
            return f"{f.filename}:{f.lineno} in {fn}"

        marker = "=" if self.is_aligned() else "!"
        return f"[{marker}] {_fmt(self.left)}  |  {_fmt(self.right)}"


@dataclass
class ZipReport:
    """Result of zipping two stack traces together."""

    left_exception: str
    right_exception: str
    pairs: List[ZippedPair] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.pairs)

    @property
    def aligned_count(self) -> int:
        return sum(1 for p in self.pairs if p.is_aligned())

    @property
    def misaligned_count(self) -> int:
        return self.count - self.aligned_count

    def summary_line(self) -> str:
        return (
            f"Zipped {self.count} pair(s): "
            f"{self.aligned_count} aligned, {self.misaligned_count} misaligned "
            f"({self.left_exception} vs {self.right_exception})"
        )


def zip_traces(left: StackTrace, right: StackTrace) -> ZipReport:
    """Zip two traces together, padding the shorter one with None."""
    left_frames = left.frames
    right_frames = right.frames
    length = max(len(left_frames), len(right_frames))

    pairs: List[ZippedPair] = []
    for i in range(length):
        lf = left_frames[i] if i < len(left_frames) else None
        rf = right_frames[i] if i < len(right_frames) else None
        pairs.append(ZippedPair(left=lf, right=rf))

    return ZipReport(
        left_exception=left.exception_type,
        right_exception=right.exception_type,
        pairs=pairs,
    )
