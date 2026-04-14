"""scorer5: scores frames by combining recency, exception weight, and file origin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

_EXCEPTION_WEIGHTS: dict[str, float] = {
    "MemoryError": 2.0,
    "RecursionError": 1.8,
    "SystemExit": 1.5,
    "KeyboardInterrupt": 1.4,
    "RuntimeError": 1.3,
    "ValueError": 1.1,
    "TypeError": 1.1,
    "AttributeError": 1.0,
    "ImportError": 1.0,
    "ModuleNotFoundError": 1.0,
    "FileNotFoundError": 0.9,
    "OSError": 0.9,
    "KeyError": 0.8,
    "IndexError": 0.8,
    "StopIteration": 0.5,
}

_STDLIB_PREFIXES = ("/usr/lib/python", "<frozen ", "<string>")


def _exception_weight(exc_type: str) -> float:
    for key, weight in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return weight
    return 1.0


def _origin_bonus(filename: str) -> float:
    """User code scores higher than stdlib or third-party."""
    if not filename:
        return 0.0
    if any(filename.startswith(p) for p in _STDLIB_PREFIXES):
        return 0.0
    if "site-packages" in filename:
        return 0.3
    return 1.0


def _recency_score(index: int, total: int) -> float:
    """Frames closer to the top of the stack (higher index) score higher."""
    if total <= 1:
        return 1.0
    return (index + 1) / total


@dataclass
class ScoredFrame5:
    frame: Frame
    score: float
    rank: int = 0

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"[{self.rank}] {fn} ({self.frame.filename}:{self.frame.lineno}) score={self.score:.3f}"


@dataclass
class ScoreReport5:
    exception_type: str
    frames: List[ScoredFrame5] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> Optional[ScoredFrame5]:
        return self.frames[0] if self.frames else None

    def ranked(self) -> List[ScoredFrame5]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames5(trace: StackTrace) -> ScoreReport5:
    total = len(trace.frames)
    weight = _exception_weight(trace.exception_type or "")
    scored: List[ScoredFrame5] = []
    for i, frame in enumerate(trace.frames):
        s = _recency_score(i, total) * weight + _origin_bonus(frame.filename or "")
        scored.append(ScoredFrame5(frame=frame, score=round(s, 4)))
    ranked = sorted(scored, key=lambda f: f.score, reverse=True)
    for rank, sf in enumerate(ranked, start=1):
        sf.rank = rank
    return ScoreReport5(exception_type=trace.exception_type or "", frames=scored)
