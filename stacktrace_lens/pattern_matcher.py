"""Pattern-based matching and categorisation of stack trace frames."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class MatchResult:
    frame: Frame
    pattern: str
    label: str
    span: Optional[tuple] = None  # (start, end) within frame.filename

    def __str__(self) -> str:
        return f"[{self.label}] {self.frame.filename}:{self.frame.lineno} in {self.frame.function}"


@dataclass
class PatternMatchReport:
    total_frames: int
    matched_frames: int
    matches: List[MatchResult] = field(default_factory=list)

    @property
    def match_ratio(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return self.matched_frames / self.total_frames

    @property
    def unmatched_count(self) -> int:
        return self.total_frames - self.matched_frames


def _find_span(pattern: str, text: str) -> Optional[tuple]:
    try:
        m = re.search(pattern, text)
        return (m.start(), m.end()) if m else None
    except re.error:
        return None


def match_frames(
    trace: StackTrace,
    patterns: dict,  # {label: regex_pattern}
) -> PatternMatchReport:
    """Match each frame against labelled regex patterns.

    *patterns* is a mapping of ``label -> regex`` applied to
    ``frame.filename``.  The first matching pattern wins.
    """
    matches: List[MatchResult] = []
    matched_indices: set = set()

    for idx, frame in enumerate(trace.frames):
        for label, pattern in patterns.items():
            span = _find_span(pattern, frame.filename)
            if span is not None:
                matches.append(MatchResult(frame=frame, pattern=pattern, label=label, span=span))
                matched_indices.add(idx)
                break

    return PatternMatchReport(
        total_frames=len(trace.frames),
        matched_frames=len(matched_indices),
        matches=matches,
    )


def format_report(report: PatternMatchReport, colour: bool = True) -> str:
    """Return a human-readable string for *report*."""
    _RESET = "\033[0m" if colour else ""
    _BOLD = "\033[1m" if colour else ""
    _CYAN = "\033[36m" if colour else ""
    _YELLOW = "\033[33m" if colour else ""

    lines = [
        f"{_BOLD}Pattern Match Report{_RESET}",
        f"  Frames   : {report.total_frames}",
        f"  Matched  : {report.matched_frames} ({report.match_ratio:.0%})",
        f"  Unmatched: {report.unmatched_count}",
        "",
    ]
    for m in report.matches:
        lines.append(f"  {_CYAN}{m.label}{_RESET}  {_YELLOW}{m.frame.filename}{_RESET}:{m.frame.lineno}  {m.frame.function}")

    return "\n".join(lines)
