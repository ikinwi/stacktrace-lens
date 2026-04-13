"""Pinpointer: identify the most likely root-cause frame in a stack trace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace

# Patterns that suggest a frame is *not* the root cause
_NOISE_PREFIXES = (
    "/usr/lib",
    "/usr/local/lib",
    "<frozen ",
    "<string>",
    "site-packages/pytest",
    "site-packages/_pytest",
    "site-packages/pluggy",
)


def _is_noise(frame: Frame) -> bool:
    filename = frame.filename or ""
    return any(filename.startswith(p) for p in _NOISE_PREFIXES)


def _score(frame: Frame, index: int, total: int) -> float:
    """Higher score => more likely to be the root cause."""
    score = 0.0
    if not _is_noise(frame):
        score += 5.0
    # Frames closer to the bottom of the trace (innermost) score higher
    score += (index + 1) / total * 3.0
    if frame.lineno and frame.lineno > 0:
        score += 1.0
    if frame.function and frame.function not in ("<module>", "<lambda>"):
        score += 1.0
    return score


@dataclass
class PinpointResult:
    trace: StackTrace
    best_frame: Optional[Frame]
    best_index: Optional[int]
    scores: List[float] = field(default_factory=list)

    @property
    def summary_line(self) -> str:
        if self.best_frame is None:
            return "No frames to pinpoint."
        return (
            f"Root-cause candidate: {self.best_frame.filename}:"
            f"{self.best_frame.lineno} in {self.best_frame.function}"
        )


def pinpoint_trace(trace: StackTrace) -> PinpointResult:
    """Score every frame and return the most likely root-cause frame."""
    frames = trace.frames
    if not frames:
        return PinpointResult(trace=trace, best_frame=None, best_index=None)

    total = len(frames)
    scores = [_score(f, i, total) for i, f in enumerate(frames)]
    best_index = max(range(total), key=lambda i: scores[i])
    return PinpointResult(
        trace=trace,
        best_frame=frames[best_index],
        best_index=best_index,
        scores=scores,
    )


def format_pinpoint(result: PinpointResult, *, colour: bool = True) -> str:
    lines: List[str] = []
    _b = (lambda s: f"\033[1m{s}\033[0m") if colour else (lambda s: s)
    _y = (lambda s: f"\033[33m{s}\033[0m") if colour else (lambda s: s)
    lines.append(_b(f"Exception: {result.trace.exception_type}"))
    lines.append(result.trace.exception_message or "")
    lines.append("")
    for i, (frame, score) in enumerate(zip(result.trace.frames, result.scores)):
        marker = " >>" if i == result.best_index else "   "
        label = f"{frame.filename}:{frame.lineno} in {frame.function}"
        score_str = f"[{score:.1f}]"
        line = f"{marker} {score_str} {label}"
        lines.append(_y(line) if i == result.best_index else line)
    lines.append("")
    lines.append(result.summary_line)
    return "\n".join(lines)
