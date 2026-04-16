"""Fuser: merge two stack traces into a unified diff-style report."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class FusedFrame:
    frame: Frame
    source: str  # 'left', 'right', or 'both'

    def __str__(self) -> str:
        tag = {"left": "<", "right": ">", "both": "="}[self.source]
        fn = self.frame.function or "<module>"
        return f"[{tag}] {self.frame.filename}:{self.frame.lineno} in {fn}"


@dataclass
class FuseReport:
    left_exception: str
    right_exception: str
    frames: List[FusedFrame] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def shared_count(self) -> int:
        return sum(1 for f in self.frames if f.source == "both")

    @property
    def left_only_count(self) -> int:
        return sum(1 for f in self.frames if f.source == "left")

    @property
    def right_only_count(self) -> int:
        return sum(1 for f in self.frames if f.source == "right")

    def summary_line(self) -> str:
        return (
            f"Fused {self.count} frames: "
            f"{self.shared_count} shared, "
            f"{self.left_only_count} left-only, "
            f"{self.right_only_count} right-only"
        )


def _frame_key(frame: Frame) -> str:
    return f"{frame.filename}:{frame.lineno}:{frame.function}"


def fuse_traces(left: StackTrace, right: StackTrace) -> FuseReport:
    left_keys = {_frame_key(f): f for f in left.frames}
    right_keys = {_frame_key(f): f for f in right.frames}

    frames: List[FusedFrame] = []
    seen = set()

    for f in left.frames:
        k = _frame_key(f)
        if k in right_keys:
            frames.append(FusedFrame(frame=f, source="both"))
        else:
            frames.append(FusedFrame(frame=f, source="left"))
        seen.add(k)

    for f in right.frames:
        k = _frame_key(f)
        if k not in seen:
            frames.append(FusedFrame(frame=f, source="right"))

    return FuseReport(
        left_exception=left.exception_type,
        right_exception=right.exception_type,
        frames=frames,
    )
