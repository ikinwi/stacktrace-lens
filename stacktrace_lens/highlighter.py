"""Highlight specific frames in a stack trace based on patterns or criteria."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class HighlightOptions:
    patterns: List[str] = field(default_factory=list)
    highlight_user_code: bool = False
    highlight_exception_origin: bool = True
    stdlib_prefixes: tuple = ("/usr/lib", "/usr/local/lib", "<frozen", "<string")


@dataclass
class HighlightedFrame:
    frame: Frame
    highlighted: bool
    reason: Optional[str] = None

    def __str__(self) -> str:
        marker = ">>> " if self.highlighted else "    "
        return f"{marker}File {self.frame.filename!r}, line {self.frame.lineno}, in {self.frame.function}"


@dataclass
class HighlightReport:
    frames: List[HighlightedFrame]
    exception_type: str
    exception_message: str

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def highlighted_count(self) -> int:
        return sum(1 for f in self.frames if f.highlighted)

    def summary_line(self) -> str:
        return (
            f"{self.exception_type}: {self.exception_message} "
            f"({self.highlighted_count}/{self.count} frames highlighted)"
        )


def _is_stdlib(filename: str, prefixes: tuple) -> bool:
    return any(filename.startswith(p) for p in prefixes)


def _matches_patterns(frame: Frame, patterns: List[str]) -> Optional[str]:
    for pattern in patterns:
        if re.search(pattern, frame.filename) or re.search(pattern, frame.function):
            return f"matches pattern {pattern!r}"
    return None


def highlight_frames(trace: StackTrace, options: Optional[HighlightOptions] = None) -> HighlightReport:
    if options is None:
        options = HighlightOptions()

    highlighted: List[HighlightedFrame] = []

    for i, frame in enumerate(trace.frames):
        reason: Optional[str] = None

        if options.patterns:
            reason = _matches_patterns(frame, options.patterns)

        if reason is None and options.highlight_user_code:
            if not _is_stdlib(frame.filename, options.stdlib_prefixes):
                reason = "user code"

        if reason is None and options.highlight_exception_origin and i == len(trace.frames) - 1:
            reason = "exception origin"

        highlighted.append(HighlightedFrame(frame=frame, highlighted=reason is not None, reason=reason))

    return HighlightReport(
        frames=highlighted,
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )


def format_highlight(report: HighlightReport, *, colour: bool = False) -> str:
    RED = "\033[31m" if colour else ""
    RESET = "\033[0m" if colour else ""
    lines: List[str] = [report.summary_line(), ""]
    for hf in report.frames:
        line = str(hf)
        if hf.highlighted:
            tag = f" [{hf.reason}]" if hf.reason else ""
            lines.append(f"{RED}{line}{tag}{RESET}")
        else:
            lines.append(line)
    return "\n".join(lines)
