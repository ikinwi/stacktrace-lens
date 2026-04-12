"""masker.py – redact or mask sensitive values inside stack-trace frames.

Different from sanitizer (which strips file-path prefixes) and redactor
(which targets free-text patterns): masker focuses on *structured* fields
such as line numbers, function argument snippets embedded in the message,
and configurable keyword-value pairs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import Frame, StackTrace

_DEFAULT_PATTERNS: List[str] = [
    r'password=[^\s&]+',
    r'token=[^\s&]+',
    r'secret=[^\s&]+',
    r'api_key=[^\s&]+',
    r'Authorization:\s*\S+',
]


@dataclass
class MaskOptions:
    patterns: List[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    placeholder: str = "***"
    mask_line_numbers: bool = False


@dataclass
class MaskedFrame:
    original: Frame
    masked_filename: str
    masked_lineno: Optional[int]
    masked_function: str
    masked_context: Optional[str]
    replacements: int

    def __str__(self) -> str:  # pragma: no cover
        lineno = self.masked_lineno if self.masked_lineno is not None else "?"
        return (
            f'  File "{self.masked_filename}", line {lineno}, '
            f"in {self.masked_function}"
        )


@dataclass
class MaskReport:
    frames: List[MaskedFrame]
    total_replacements: int
    exception_type: str
    exception_message: str

    @property
    def count(self) -> int:
        return len(self.frames)

    def summary_line(self) -> str:
        return (
            f"{self.count} frame(s) processed, "
            f"{self.total_replacements} replacement(s) made."
        )


def _apply_patterns(text: str, patterns: List[re.Pattern], placeholder: str) -> tuple[str, int]:
    count = 0
    for pat in patterns:
        new_text, n = pat.subn(placeholder, text)
        text = new_text
        count += n
    return text, count


def mask_trace(trace: StackTrace, opts: Optional[MaskOptions] = None) -> MaskReport:
    """Apply masking to every frame in *trace* and return a MaskReport."""
    if opts is None:
        opts = MaskOptions()

    compiled = [re.compile(p, re.IGNORECASE) for p in opts.patterns]
    masked_frames: List[MaskedFrame] = []
    total = 0

    for frame in trace.frames:
        replacements = 0

        filename, n = _apply_patterns(frame.filename, compiled, opts.placeholder)
        replacements += n

        function, n = _apply_patterns(frame.function, compiled, opts.placeholder)
        replacements += n

        context: Optional[str] = None
        if frame.context:
            context, n = _apply_patterns(frame.context, compiled, opts.placeholder)
            replacements += n

        lineno = None if opts.mask_line_numbers else frame.lineno

        masked_frames.append(
            MaskedFrame(
                original=frame,
                masked_filename=filename,
                masked_lineno=lineno,
                masked_function=function,
                masked_context=context,
                replacements=replacements,
            )
        )
        total += replacements

    return MaskReport(
        frames=masked_frames,
        total_replacements=total,
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )
