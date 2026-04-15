"""scorer6: scores frames by combining file origin, exception weight, and call depth."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ValueError": 1.2,
    "TypeError": 1.2,
    "AttributeError": 1.3,
    "KeyError": 1.1,
    "ImportError": 1.4,
    "ModuleNotFoundError": 1.4,
    "RuntimeError": 1.1,
    "OSError": 1.0,
    "IOError": 1.0,
    "ZeroDivisionError": 1.2,
    "IndexError": 1.1,
    "RecursionError": 1.5,
    "MemoryError": 1.5,
    "NotImplementedError": 0.9,
}


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return w
    return 1.0


def _origin_bonus(filename: str) -> float:
    if not filename:
        return 0.5
    if "site-packages" in filename or "dist-packages" in filename:
        return 0.6
    if filename.startswith("<") or "lib/python" in filename:
        return 0.4
    return 1.0


def _depth_score(index: int, total: int) -> float:
    """Frames closer to the top of the stack (higher index) score higher."""
    if total <= 1:
        return 1.0
    return 0.5 + 0.5 * (index / (total - 1))


@dataclass
class ScoredFrame6:
    frame: Frame
    score: float
    index: int

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        fname = self.frame.filename or "<unknown>"
        return f"[{self.score:.3f}] {fn} ({fname}:{self.frame.lineno})"


@dataclass
class ScoreReport6:
    exception_type: str
    frames: List[ScoredFrame6] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def top(self) -> Optional[ScoredFrame6]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda f: f.score)

    def ranked(self) -> List[ScoredFrame6]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames6(trace: StackTrace) -> ScoreReport6:
    exc_w = _exception_weight(trace.exception_type)
    total = len(trace.frames)
    scored = []
    for i, frame in enumerate(trace.frames):
        s = exc_w * _origin_bonus(frame.filename or "") * _depth_score(i, total)
        scored.append(ScoredFrame6(frame=frame, score=round(s, 6), index=i))
    return ScoreReport6(exception_type=trace.exception_type, frames=scored)
