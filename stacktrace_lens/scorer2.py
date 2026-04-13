"""Frame-level relevance scorer based on heuristics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


_NOISE_PREFIXES = (
    "/usr/lib",
    "/usr/local/lib",
    "<frozen ",
    "<string>",
    "site-packages/pytest",
    "site-packages/_pytest",
    "site-packages/pluggy",
)

_HIGH_VALUE_KEYWORDS = ("test_", "main", "run", "execute", "handle", "process")


def _base_score(frame: Frame) -> float:
    """Return a heuristic relevance score in [0.0, 1.0] for *frame*."""
    filename = frame.filename or ""
    function = frame.function or ""

    # Noise frames get a very low score.
    for prefix in _NOISE_PREFIXES:
        if filename.startswith(prefix):
            return 0.1

    score = 0.5

    # Reward user-looking paths.
    if not filename.startswith("/"):
        score += 0.15
    if "site-packages" not in filename:
        score += 0.1

    # Reward recognisable entry-point functions.
    for kw in _HIGH_VALUE_KEYWORDS:
        if kw in function:
            score += 0.1
            break

    return min(score, 1.0)


@dataclass
class ScoredFrame2:
    frame: Frame
    score: float

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.score:.2f}  {self.frame.filename}:{self.frame.lineno} in {self.frame.function}"


@dataclass
class ScoreReport2:
    frames: List[ScoredFrame2] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    def top(self, n: int = 5) -> List[ScoredFrame2]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)[:n]

    def highest(self) -> Optional[ScoredFrame2]:
        if not self.frames:
            return None
        return max(self.frames, key=lambda f: f.score)


def score_frames(trace: StackTrace) -> ScoreReport2:
    """Score every frame in *trace* and return a :class:`ScoreReport2`."""
    scored = [ScoredFrame2(frame=f, score=_base_score(f)) for f in trace.frames]
    return ScoreReport2(frames=scored)
