"""Censor module: replace sensitive tokens in stack trace frames."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

# Default patterns that are considered sensitive
_DEFAULT_PATTERNS: List[str] = [
    r'password\s*=\s*\S+',
    r'secret\s*=\s*\S+',
    r'token\s*=\s*\S+',
    r'api[_-]?key\s*=\s*\S+',
    r'auth\s*=\s*\S+',
]

PLACEHOLDER = "<CENSORED>"


@dataclass
class CensorOptions:
    patterns: List[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    placeholder: str = PLACEHOLDER
    case_sensitive: bool = False


@dataclass
class CensoredFrame:
    original: Frame
    censored_filename: str
    censored_line: Optional[str]
    replacements: int

    def __str__(self) -> str:
        loc = f"{self.censored_filename}:{self.original.lineno}"
        line = f" | {self.censored_line}" if self.censored_line else ""
        return f"  {self.original.function} ({loc}){line}"


@dataclass
class CensorReport:
    frames: List[CensoredFrame]
    total_replacements: int

    @property
    def count(self) -> int:
        return len(self.frames)

    def summary_line(self) -> str:
        return (
            f"Censored {self.total_replacements} sensitive value(s) "
            f"across {self.count} frame(s)."
        )


def _compile(patterns: List[str], case_sensitive: bool) -> List[re.Pattern]:
    flags = 0 if case_sensitive else re.IGNORECASE
    return [re.compile(p, flags) for p in patterns]


def _apply(text: str, compiled: List[re.Pattern], placeholder: str) -> tuple[str, int]:
    count = 0
    for pattern in compiled:
        new_text, n = pattern.subn(placeholder, text)
        text = new_text
        count += n
    return text, count


def censor_trace(trace: StackTrace, options: Optional[CensorOptions] = None) -> CensorReport:
    if options is None:
        options = CensorOptions()
    compiled = _compile(options.patterns, options.case_sensitive)
    censored_frames: List[CensoredFrame] = []
    total = 0
    for frame in trace.frames:
        fn, fn_count = _apply(frame.filename, compiled, options.placeholder)
        line_text = frame.line
        line_count = 0
        if line_text:
            line_text, line_count = _apply(line_text, compiled, options.placeholder)
        replacements = fn_count + line_count
        total += replacements
        censored_frames.append(
            CensoredFrame(
                original=frame,
                censored_filename=fn,
                censored_line=line_text,
                replacements=replacements,
            )
        )
    return CensorReport(frames=censored_frames, total_replacements=total)
