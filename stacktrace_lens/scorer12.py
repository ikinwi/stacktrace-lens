"""scorer12 – scores frames using a combined signal of exception weight,
call-site entropy, and stdlib penalty."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import math

from stacktrace_lens.parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ZeroDivisionError": 1.2,
    "AttributeError": 1.1,
    "TypeError": 1.0,
    "ValueError": 1.0,
    "ImportError": 1.3,
    "ModuleNotFoundError": 1.3,
    "KeyError": 0.9,
    "IndexError": 0.9,
    "RuntimeError": 1.1,
    "RecursionError": 1.4,
}

_STDLIB_PREFIXES = ("/usr/lib/python", "<frozen", "<string>")


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return w
    return 1.0


def _stdlib_penalty(frame: Frame) -> float:
    fn = frame.filename or ""
    return 0.5 if any(fn.startswith(p) for p in _STDLIB_PREFIXES) else 1.0


def _entropy_bonus(frame: Frame, all_frames: List[Frame]) -> float:
    """Frames whose filename appears rarely get a small bonus."""
    total = len(all_frames)
    if total == 0:
        return 1.0
    count = sum(1 for f in all_frames if f.filename == frame.filename)
    p = count / total
    entropy = -p * math.log2(p) if p > 0 else 0.0
    return 1.0 + entropy * 0.1


@dataclass
class ScoredFrame12:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"{fn} ({self.frame.filename}:{self.frame.lineno}) score={self.score:.3f}"


@dataclass
class ScoreReport12:
    exception_type: str
    exception_message: str
    frames: List[ScoredFrame12] = field(default_factory=list)

    @property
    def top_frame(self) -> Optional[ScoredFrame12]:
        return max(self.frames, key=lambda f: f.score, default=None)

    def ranked(self) -> List[ScoredFrame12]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames12(trace: StackTrace) -> ScoreReport12:
    ew = _exception_weight(trace.exception_type)
    n = len(trace.frames)
    scored = []
    for i, frame in enumerate(trace.frames):
        position = (i + 1) / n if n else 1.0
        sp = _stdlib_penalty(frame)
        eb = _entropy_bonus(frame, trace.frames)
        score = ew * sp * eb * position
        scored.append(ScoredFrame12(frame=frame, score=round(score, 6)))
    return ScoreReport12(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        frames=scored,
    )
