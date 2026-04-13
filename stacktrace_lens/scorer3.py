"""scorer3: score frames by recency (line-number proximity to exception site)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace


def _recency_score(index: int, total: int) -> float:
    """Frames closer to the exception (higher index) score higher."""
    if total <= 1:
        return 1.0
    return round(index / (total - 1), 4)


def _line_bonus(frame: Frame) -> float:
    """Small bonus for frames that carry a line number."""
    return 0.1 if frame.lineno is not None else 0.0


@dataclass
class ScoredFrame3:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.filename or "<unknown>"
        func = self.frame.function or "<module>"
        return f"[{self.score:.4f}] {fn}:{self.frame.lineno} in {func}"


@dataclass
class ScoreReport3:
    frames: List[ScoredFrame3] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> Optional[ScoredFrame3]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda sf: sf.score)

    def ranked(self) -> List[ScoredFrame3]:
        return sorted(self.frames, key=lambda sf: sf.score, reverse=True)

    def summary_line(self) -> str:
        t = self.top()
        if t is None:
            return "No frames scored."
        return f"{self.count} frames scored; top: {t}"


def score_frames3(trace: StackTrace) -> ScoreReport3:
    """Score every frame in *trace* by recency and return a ScoreReport3."""
    total = len(trace.frames)
    scored = [
        ScoredFrame3(
            frame=f,
            score=min(1.0, _recency_score(i, total) + _line_bonus(f)),
        )
        for i, f in enumerate(trace.frames)
    ]
    return ScoreReport3(frames=scored)
