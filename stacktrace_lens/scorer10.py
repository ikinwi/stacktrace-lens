"""scorer10 – composite frame scorer using entropy, depth, and exception weight."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from stacktrace_lens.parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ValueError": 1.2,
    "TypeError": 1.2,
    "AttributeError": 1.3,
    "ImportError": 1.4,
    "ModuleNotFoundError": 1.4,
    "KeyError": 1.1,
    "IndexError": 1.1,
    "RuntimeError": 1.3,
    "OSError": 1.2,
    "IOError": 1.2,
    "ZeroDivisionError": 1.0,
    "RecursionError": 1.5,
    "MemoryError": 1.6,
    "NotImplementedError": 1.0,
}


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return w
    return 1.0


def _entropy_bonus(frame: Frame, all_frames: List[Frame]) -> float:
    """Reward frames whose filename appears rarely in the trace."""
    total = len(all_frames)
    if total == 0:
        return 0.0
    count = sum(1 for f in all_frames if f.filename == frame.filename)
    freq = count / total
    return round(1.0 - freq, 4)


def _depth_score(index: int, total: int) -> float:
    """Frames near the bottom of the trace (innermost) score higher."""
    if total <= 1:
        return 1.0
    return round(index / (total - 1), 4)


@dataclass
class ScoredFrame10:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"[{self.score:.3f}] {self.frame.filename}:{self.frame.lineno} in {fn}"


@dataclass
class ScoreReport10:
    exception_type: str
    frames: List[ScoredFrame10] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> ScoredFrame10 | None:
        return max(self.frames, key=lambda f: f.score) if self.frames else None

    def ranked(self) -> List[ScoredFrame10]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames(trace: StackTrace) -> ScoreReport10:
    weight = _exception_weight(trace.exception_type)
    total = len(trace.frames)
    scored = []
    for i, frame in enumerate(trace.frames):
        s = (_depth_score(i, total) + _entropy_bonus(frame, trace.frames)) * weight
        scored.append(ScoredFrame10(frame=frame, score=round(s, 4)))
    return ScoreReport10(exception_type=trace.exception_type, frames=scored)
