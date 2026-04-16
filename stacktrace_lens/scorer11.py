"""scorer11 – frame scorer combining package diversity, line proximity, and exception weight."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from stacktrace_lens.parser import Frame, StackTrace

_EXCEPTION_WEIGHTS = {
    "ZeroDivisionError": 1.4,
    "AttributeError": 1.3,
    "TypeError": 1.2,
    "ValueError": 1.2,
    "ImportError": 1.1,
    "ModuleNotFoundError": 1.1,
    "KeyError": 1.0,
    "IndexError": 1.0,
    "RuntimeError": 1.3,
    "RecursionError": 1.5,
}


def _exception_weight(exc_type: str) -> float:
    for key, w in _EXCEPTION_WEIGHTS.items():
        if key in exc_type:
            return w
    return 1.0


def _line_proximity(line: Optional[int], max_line: int) -> float:
    """Higher score for frames with higher line numbers (closer to error site)."""
    if line is None or max_line == 0:
        return 0.0
    return line / max_line


def _package_diversity_bonus(frame: Frame, all_frames: List[Frame]) -> float:
    """Bonus if this frame's file differs from the majority."""
    if not frame.filename:
        return 0.0
    pkg = frame.filename.split("/")[0] if "/" in frame.filename else frame.filename
    same = sum(1 for f in all_frames if f.filename and f.filename.startswith(pkg))
    ratio = same / len(all_frames) if all_frames else 1.0
    return 0.2 if ratio < 0.3 else 0.0


@dataclass
class ScoredFrame11:
    frame: Frame
    score: float

    def __str__(self) -> str:
        fn = self.frame.filename or "<unknown>"
        func = self.frame.function or "<module>"
        return f"{fn}:{func} score={self.score:.3f}"


@dataclass
class ScoreReport11:
    exception_type: str
    exception_message: str
    frames: List[ScoredFrame11] = field(default_factory=list)

    @property
    def top(self) -> Optional[ScoredFrame11]:
        return max(self.frames, key=lambda f: f.score, default=None)

    def ranked(self) -> List[ScoredFrame11]:
        return sorted(self.frames, key=lambda f: f.score, reverse=True)


def score_frames11(trace: StackTrace) -> ScoreReport11:
    report = ScoreReport11(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )
    ew = _exception_weight(trace.exception_type)
    lines = [f.lineno for f in trace.frames if f.lineno is not None]
    max_line = max(lines) if lines else 0
    for i, frame in enumerate(trace.frames):
        proximity = _line_proximity(frame.lineno, max_line)
        diversity = _package_diversity_bonus(frame, trace.frames)
        position = (i + 1) / len(trace.frames) if trace.frames else 0.0
        score = ew * (0.4 * proximity + 0.4 * position + 0.2) + diversity
        report.frames.append(ScoredFrame11(frame=frame, score=round(score, 4)))
    return report
