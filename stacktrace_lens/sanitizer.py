"""Sanitize stack traces by redacting sensitive values from exception messages and frame paths."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

# Patterns that may contain sensitive data
_PATTERNS: List[tuple[str, str]] = [
    (r'(?i)(password|passwd|pwd)\s*=\s*\S+', r'\1=<REDACTED>'),
    (r'(?i)(token|api[_-]?key|secret|auth)\s*=\s*\S+', r'\1=<REDACTED>'),
    (r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', '<EMAIL>'),
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP_ADDRESS>'),
    (r'(?i)/home/[^/\s]+', '/home/<USER>'),
    (r'(?i)/users/[^/\s]+', '/Users/<USER>'),
]


@dataclass
class SanitizeOptions:
    redact_message: bool = True
    redact_paths: bool = True
    extra_patterns: List[tuple[str, str]] = field(default_factory=list)


def _apply_patterns(
    text: str,
    patterns: List[tuple[str, str]],
) -> str:
    for pat, repl in patterns:
        text = re.sub(pat, repl, text)
    return text


def sanitize_frame(frame: Frame, options: Optional[SanitizeOptions] = None) -> Frame:
    """Return a new Frame with sensitive data redacted."""
    if options is None:
        options = SanitizeOptions()

    all_patterns = _PATTERNS + options.extra_patterns

    filename = frame.filename
    if options.redact_paths:
        filename = _apply_patterns(filename, all_patterns)

    return Frame(
        filename=filename,
        lineno=frame.lineno,
        function=frame.function,
        source=frame.source,
    )


def sanitize_trace(
    trace: StackTrace,
    options: Optional[SanitizeOptions] = None,
) -> StackTrace:
    """Return a new StackTrace with sensitive data redacted throughout."""
    if options is None:
        options = SanitizeOptions()

    all_patterns = _PATTERNS + options.extra_patterns

    sanitized_frames = [sanitize_frame(f, options) for f in trace.frames]

    message = trace.exception_message
    if options.redact_message and message:
        message = _apply_patterns(message, all_patterns)

    return StackTrace(
        exception_type=trace.exception_type,
        exception_message=message,
        frames=sanitized_frames,
    )


def format_sanitize_report(original: StackTrace, sanitized: StackTrace) -> str:
    """Return a human-readable summary of what was redacted."""
    lines: List[str] = ["=== Sanitization Report ==="]
    if original.exception_message != sanitized.exception_message:
        lines.append("  [message] sensitive data redacted")
    changed = sum(
        1 for a, b in zip(original.frames, sanitized.frames) if a.filename != b.filename
    )
    if changed:
        lines.append(f"  [frames]  {changed} path(s) redacted")
    if len(lines) == 1:
        lines.append("  no sensitive data detected")
    return "\n".join(lines)
