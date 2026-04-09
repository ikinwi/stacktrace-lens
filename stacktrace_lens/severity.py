"""Severity scoring for stack traces based on exception type and frame depth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from stacktrace_lens.parser import StackTrace

# Higher score = more severe
_EXCEPTION_SEVERITY: Dict[str, int] = {
    "SystemExit": 10,
    "KeyboardInterrupt": 9,
    "MemoryError": 9,
    "RecursionError": 8,
    "SegmentationFault": 8,
    "OSError": 7,
    "IOError": 7,
    "RuntimeError": 6,
    "ValueError": 5,
    "TypeError": 5,
    "AttributeError": 5,
    "KeyError": 4,
    "IndexError": 4,
    "ImportError": 4,
    "ModuleNotFoundError": 4,
    "NameError": 3,
    "ZeroDivisionError": 3,
    "StopIteration": 2,
    "AssertionError": 2,
    "NotImplementedError": 2,
    "FileNotFoundError": 3,
    "PermissionError": 6,
    "TimeoutError": 5,
}

SEVERITY_LABELS = {
    (0, 3): "LOW",
    (3, 6): "MEDIUM",
    (6, 8): "HIGH",
    (8, 11): "CRITICAL",
}


@dataclass
class SeverityResult:
    score: int
    label: str
    exception_type: str
    frame_count: int


def _label_for_score(score: int) -> str:
    for (low, high), label in SEVERITY_LABELS.items():
        if low <= score < high:
            return label
    return "UNKNOWN"


def _depth_bonus(frame_count: int) -> int:
    """Add up to 2 points for deep stack traces."""
    if frame_count >= 20:
        return 2
    if frame_count >= 10:
        return 1
    return 0


def score_trace(trace: StackTrace) -> SeverityResult:
    """Compute a severity score for a parsed stack trace."""
    base = _EXCEPTION_SEVERITY.get(trace.exception_type, 3)
    bonus = _depth_bonus(len(trace.frames))
    total = min(base + bonus, 10)
    return SeverityResult(
        score=total,
        label=_label_for_score(total),
        exception_type=trace.exception_type,
        frame_count=len(trace.frames),
    )


def format_severity(result: SeverityResult, *, colour: bool = True) -> str:
    """Return a human-readable severity line."""
    _COLOURS = {"LOW": "\033[32m", "MEDIUM": "\033[33m", "HIGH": "\033[31m", "CRITICAL": "\033[35m"}
    reset = "\033[0m" if colour else ""
    c = (_COLOURS.get(result.label, "") if colour else "")
    return (
        f"{c}Severity: {result.label} (score={result.score}/10){reset}  "
        f"[{result.exception_type}, {result.frame_count} frame(s)]"
    )
