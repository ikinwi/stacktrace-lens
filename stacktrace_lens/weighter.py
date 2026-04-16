"""Assigns importance weights to frames based on heuristics."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from stacktrace_lens.parser import Frame, StackTrace

_NOISE_PREFIXES = (
    "/usr/lib",
    "/usr/local/lib",
    "<frozen ",
    "<string>",
)

_HIGH_WEIGHT_EXCEPTIONS = {
    "ValueError", "TypeError", "KeyError", "AttributeError",
    "RuntimeError", "AssertionError",
}


def _is_noise(frame: Frame) -> bool:
    fn = frame.filename or ""
    return any(fn.startswith(p) for p in _NOISE_PREFIXES)


def _exception_multiplier(exception_type: str) -> float:
    for known in _HIGH_WEIGHT_EXCEPTIONS:
        if known in exception_type:
            return 1.5
    return 1.0


def _position_weight(index: int, total: int) -> float:
    """Frames near the end (innermost) get higher weight."""
    if total <= 1:
        return 1.0
    return 0.5 + 0.5 * (index / (total - 1))


@dataclass
class WeightedFrame:
    frame: Frame
    weight: float

    def __str__(self) -> str:
        fn = self.frame.filename or "<unknown>"
        func = self.frame.function or "<module>"
        return f"{fn}:{self.frame.lineno} {func} (weight={self.weight:.2f})"


@dataclass
class WeightReport:
    frames: List[WeightedFrame] = field(default_factory=list)
    exception_type: str = ""
    top_frame: Optional[WeightedFrame] = None

    @property
    def count(self) -> int:
        return len(self.frames)

    def summary_line(self) -> str:
        top = self.top_frame
        if top is None:
            return "No frames."
        return f"Top frame: {top}"


def weight_frames(trace: StackTrace) -> WeightReport:
    frames = trace.frames
    total = len(frames)
    mult = _exception_multiplier(trace.exception_type or "")
    weighted: List[WeightedFrame] = []
    for i, frame in enumerate(frames):
        base = _position_weight(i, total)
        if _is_noise(frame):
            base *= 0.3
        w = round(base * mult, 4)
        weighted.append(WeightedFrame(frame=frame, weight=w))
    top = max(weighted, key=lambda wf: wf.weight) if weighted else None
    return WeightReport(frames=weighted, exception_type=trace.exception_type or "", top_frame=top)
