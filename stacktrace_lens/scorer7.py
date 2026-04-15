"""scorer7 – context-aware frame scorer combining exception weight,
call-depth penalty, file origin bonus, and line-number recency."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ZeroDivisionError": 1.4,
    "AttributeError": 1.3,
    "TypeError": 1.3,
    "ValueError": 1.2,
    "KeyError": 1.2,
    "IndexError": 1.2,
    "ImportError": 1.1,
    "ModuleNotFoundError": 1.1,
    "RuntimeError": 1.0,
    "OSError": 0.9,
    "IOError": 0.9,
}


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key.lower() in exc_type.lower():
            return w
    return 1.0


def _depth_penalty(index: int, total: int) -> float:
    """Frames closer to the top of the trace (innermost) score higher."""
    if total <= 1:
        return 1.0
    return 0.5 + 0.5 * (index / (total - 1))


def _origin_bonus(filename: Optional[str]) -> float:
    if not filename:
        return 0.8
    low = filename.lower()
    if any(low.startswith(p) for p in ("/usr/lib", "/usr/local/lib", "<frozen")):
        return 0.6
    if "site-packages" in low:
        return 0.7
    return 1.0


def _line_bonus(lineno: Optional[int]) -> float:
    return 1.05 if lineno and lineno > 0 else 1.0


@dataclass
class ScoredFrame7:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"{fn} ({self.frame.filename}:{self.frame.lineno}) score={self.score:.3f}"


@dataclass
class ScoreReport7:
    frames: List[ScoredFrame7] = field(default_factory=list)
    exception_type: str = ""

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self) -> Optional[ScoredFrame7]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda sf: sf.score)

    def ranked(self) -> List[ScoredFrame7]:
        return sorted(self.frames, key=lambda sf: sf.score, reverse=True)


def score_frames7(trace: StackTrace) -> ScoreReport7:
    exc_w = _exception_weight(trace.exception_type)
    total = len(trace.frames)
    scored = [
        ScoredFrame7(
            frame=f,
            score=round(
                exc_w
                * _depth_penalty(i, total)
                * _origin_bonus(f.filename)
                * _line_bonus(f.lineno),
                4,
            ),
        )
        for i, f in enumerate(trace.frames)
    ]
    return ScoreReport7(frames=scored, exception_type=trace.exception_type)
