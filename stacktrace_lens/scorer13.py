"""scorer13: scores frames by combining uniqueness, stdlib penalty, and line proximity."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .parser import StackTrace, Frame

_KNOWN_WEIGHTS = {
    "ValueError": 1.2,
    "TypeError": 1.1,
    "AttributeError": 1.3,
    "ImportError": 1.4,
    "KeyError": 1.1,
    "RuntimeError": 1.2,
    "OSError": 1.0,
    "IOError": 1.0,
}

_STDLIB_PREFIXES = ("/usr/lib/python", "<frozen", "<string>")


def _exception_weight(exc_type: str) -> float:
    for key, w in _KNOWN_WEIGHTS.items():
        if key.lower() in exc_type.lower():
            return w
    return 1.0


def _stdlib_penalty(frame: Frame) -> float:
    fn = frame.filename or ""
    if any(fn.startswith(p) for p in _STDLIB_PREFIXES):
        return 0.5
    return 1.0


def _line_proximity(frame: Frame, max_line: int) -> float:
    if max_line == 0:
        return 0.0
    return min((frame.lineno or 0) / max_line, 1.0) * 0.2


@dataclass
class ScoredFrame13:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.function or "<module>"
        return f"{fn} [{self.frame.filename}:{self.frame.lineno}] score={self.score:.3f}"


@dataclass
class ScoreReport13:
    frames: List[ScoredFrame13]
    exception_type: str

    @property
    def top_frame(self) -> ScoredFrame13 | None:
        return max(self.frames, key=lambda f: f.score, default=None)

    def ranked(self) -> List[ScoredFrame13]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames(trace: StackTrace) -> ScoreReport13:
    max_line = max((f.lineno or 0 for f in trace.frames), default=0)
    ew = _exception_weight(trace.exception_type)
    scored = []
    for frame in trace.frames:
        s = ew * _stdlib_penalty(frame) + _line_proximity(frame, max_line)
        scored.append(ScoredFrame13(frame=frame, score=round(s, 4)))
    return ScoreReport13(frames=scored, exception_type=trace.exception_type)
