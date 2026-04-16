"""scorer9: composite frame scorer using package depth, uniqueness, and exception weight."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ValueError": 1.2,
    "TypeError": 1.2,
    "AttributeError": 1.3,
    "KeyError": 1.1,
    "IndexError": 1.1,
    "ImportError": 1.4,
    "ModuleNotFoundError": 1.4,
    "RuntimeError": 1.5,
    "OSError": 1.3,
    "IOError": 1.3,
    "ZeroDivisionError": 1.0,
    "RecursionError": 1.6,
    "MemoryError": 1.8,
    "NotImplementedError": 1.1,
}


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return w
    return 1.0


def _package_depth(filename: str) -> int:
    """Number of path components — deeper == more specific user code."""
    if not filename:
        return 0
    return len(filename.replace("\\", "/").split("/"))


def _uniqueness_bonus(frame: Frame, all_frames: List[Frame]) -> float:
    """Bonus for frames whose function name appears only once."""
    name = frame.function or ""
    count = sum(1 for f in all_frames if f.function == name)
    return 0.5 if count == 1 else 0.0


def _recency_score(index: int, total: int) -> float:
    """Frames closer to the top of the trace (index 0 == innermost) score higher."""
    if total <= 1:
        return 1.0
    return 1.0 - (index / total)


@dataclass
class ScoredFrame9:
    frame: Frame
    score: float
    index: int

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"[{self.score:.3f}] {fn} ({self.frame.filename}:{self.frame.lineno})"


@dataclass
class ScoreReport9:
    frames: List[ScoredFrame9] = field(default_factory=list)
    exception_type: str = ""
    exception_message: str = ""

    @property
    def top(self) -> Optional[ScoredFrame9]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda f: f.score)

    @property
    def ranked(self) -> List[ScoredFrame9]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames9(trace: StackTrace) -> ScoreReport9:
    all_frames = trace.frames
    total = len(all_frames)
    exc_w = _exception_weight(trace.exception_type or "")
    scored: List[ScoredFrame9] = []
    for idx, frame in enumerate(all_frames):
        s = (
            exc_w
            * (1 + _package_depth(frame.filename or "") * 0.05)
            * (1 + _uniqueness_bonus(frame, all_frames))
            * (1 + _recency_score(idx, total))
        )
        scored.append(ScoredFrame9(frame=frame, score=round(s, 4), index=idx))
    return ScoreReport9(
        frames=scored,
        exception_type=trace.exception_type or "",
        exception_message=trace.exception_message or "",
    )
