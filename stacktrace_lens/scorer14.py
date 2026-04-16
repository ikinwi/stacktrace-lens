"""scorer14 – scores frames using a combination of exception weight,
call-stack centrality (middle frames score higher) and a noise penalty."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ValueError": 1.2,
    "TypeError": 1.2,
    "AttributeError": 1.3,
    "KeyError": 1.1,
    "IndexError": 1.1,
    "ImportError": 1.4,
    "ModuleNotFoundError": 1.4,
    "RuntimeError": 1.0,
    "OSError": 1.0,
    "IOError": 1.0,
    "NotImplementedError": 0.9,
    "RecursionError": 1.5,
    "MemoryError": 1.5,
}

_NOISE_PREFIXES = ("<", "frozen ", "_bootstrap")


def _exception_weight(exc_type: Optional[str]) -> float:
    if not exc_type:
        return 1.0
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return w
    return 1.0


def _centrality_score(index: int, total: int) -> float:
    """Frames near the middle of the stack get a small bonus."""
    if total <= 1:
        return 1.0
    mid = (total - 1) / 2.0
    distance = abs(index - mid) / mid
    return 1.0 + 0.3 * (1.0 - distance)


def _noise_penalty(frame: Frame) -> float:
    fn = frame.filename or ""
    for prefix in _NOISE_PREFIXES:
        if fn.startswith(prefix):
            return 0.5
    return 1.0


@dataclass
class ScoredFrame14:
    frame: Frame
    score: float
    index: int

    def __str__(self) -> str:
        fn = self.frame.filename or "<unknown>"
        func = self.frame.function or "<module>"
        return f"[{self.score:.3f}] {fn}:{self.frame.lineno} in {func}"


@dataclass
class ScoreReport14:
    exception_type: Optional[str]
    exception_message: Optional[str]
    frames: List[ScoredFrame14] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> Optional[ScoredFrame14]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda sf: sf.score)

    def ranked(self) -> List[ScoredFrame14]:
        return sorted(self.frames, key=lambda sf: sf.score, reverse=True)


def score_frames14(trace: StackTrace) -> ScoreReport14:
    report = ScoreReport14(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )
    total = len(trace.frames)
    ew = _exception_weight(trace.exception_type)
    for i, frame in enumerate(trace.frames):
        score = ew * _centrality_score(i, total) * _noise_penalty(frame)
        report.frames.append(ScoredFrame14(frame=frame, score=round(score, 6), index=i))
    return report
