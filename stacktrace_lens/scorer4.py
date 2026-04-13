"""Frame scoring based on recency, depth, and exception context."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace


_EXCEPTION_WEIGHT: dict[str, float] = {
    "RuntimeError": 1.5,
    "ValueError": 1.2,
    "TypeError": 1.2,
    "AttributeError": 1.1,
    "KeyError": 1.1,
    "IndexError": 1.0,
    "ImportError": 0.9,
    "ModuleNotFoundError": 0.9,
    "OSError": 0.8,
    "IOError": 0.8,
}


def _exception_weight(exc_type: str) -> float:
    for key, weight in _EXCEPTION_WEIGHT.items():
        if key in exc_type:
            return weight
    return 1.0


def _position_score(index: int, total: int) -> float:
    """Frames closer to the top of the trace score higher."""
    if total <= 1:
        return 1.0
    return 1.0 - (index / total) * 0.5


def _line_bonus(frame: Frame) -> float:
    if frame.lineno and frame.lineno > 0:
        return min(0.2, frame.lineno / 1000.0)
    return 0.0


@dataclass
class ScoredFrame4:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"{fn} ({self.frame.filename}:{self.frame.lineno}) score={self.score:.3f}"


@dataclass
class ScoreReport4:
    frames: List[ScoredFrame4] = field(default_factory=list)
    exception_type: str = ""
    exception_weight: float = 1.0

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> Optional[ScoredFrame4]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda f: f.score)

    def ranked(self) -> List[ScoredFrame4]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames4(trace: StackTrace) -> ScoreReport4:
    exc_type = trace.exception_type or ""
    weight = _exception_weight(exc_type)
    total = len(trace.frames)
    scored: List[ScoredFrame4] = []
    for i, frame in enumerate(trace.frames):
        pos = _position_score(i, total)
        bonus = _line_bonus(frame)
        score = round((pos + bonus) * weight, 4)
        scored.append(ScoredFrame4(frame=frame, score=score))
    return ScoreReport4(frames=scored, exception_type=exc_type, exception_weight=weight)
