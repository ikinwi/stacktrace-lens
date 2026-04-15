"""scorer8 – composite frame scorer combining recency, origin, exception weight,
and unique-file diversity bonus."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ZeroDivisionError": 1.4,
    "AttributeError": 1.3,
    "TypeError": 1.2,
    "ValueError": 1.2,
    "KeyError": 1.1,
    "IndexError": 1.1,
    "ImportError": 1.0,
    "ModuleNotFoundError": 1.0,
    "RuntimeError": 1.3,
    "RecursionError": 1.5,
    "MemoryError": 1.5,
    "OSError": 1.1,
    "IOError": 1.1,
}


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key.lower() in exc_type.lower():
            return w
    return 1.0


def _recency_score(index: int, total: int) -> float:
    """Frames closer to the top of the trace (higher index) score higher."""
    if total <= 1:
        return 1.0
    return (index + 1) / total


def _origin_bonus(filename: str) -> float:
    if not filename:
        return 0.0
    low = filename.lower()
    if any(p in low for p in ("site-packages", "dist-packages", "<frozen", "lib/python")):
        return 0.0
    return 0.2


def _diversity_bonus(filename: str, seen_files: set) -> float:
    if filename and filename not in seen_files:
        return 0.15
    return 0.0


@dataclass
class ScoredFrame8:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"{self.score:.3f}  {self.frame.filename}:{self.frame.lineno}  {fn}"


@dataclass
class ScoreReport8:
    frames: List[ScoredFrame8] = field(default_factory=list)
    exception_type: str = ""

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> Optional[ScoredFrame8]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda sf: sf.score)

    def ranked(self) -> List[ScoredFrame8]:
        return sorted(self.frames, key=lambda sf: sf.score, reverse=True)


def score_frames8(trace: StackTrace) -> ScoreReport8:
    total = len(trace.frames)
    exc_w = _exception_weight(trace.exception_type)
    seen: set = set()
    scored: List[ScoredFrame8] = []
    for idx, frame in enumerate(trace.frames):
        s = _recency_score(idx, total)
        s += _origin_bonus(frame.filename or "")
        s += _diversity_bonus(frame.filename or "", seen)
        s *= exc_w
        if frame.filename:
            seen.add(frame.filename)
        scored.append(ScoredFrame8(frame=frame, score=round(s, 4)))
    return ScoreReport8(frames=scored, exception_type=trace.exception_type)
