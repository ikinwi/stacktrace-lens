"""Redact sensitive values from stack trace frames and messages."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

# Default patterns map label -> compiled regex
_DEFAULT_PATTERNS: List[tuple[str, re.Pattern[str]]] = [
    ("password", re.compile(r"password=[^\s&'\"]+", re.IGNORECASE)),
    ("token", re.compile(r"token=[^\s&'\"]+", re.IGNORECASE)),
    ("api_key", re.compile(r"api[_-]?key=[^\s&'\"]+", re.IGNORECASE)),
    ("secret", re.compile(r"secret=[^\s&'\"]+", re.IGNORECASE)),
    ("auth", re.compile(r"auth(?:orization)?=[^\s&'\"]+", re.IGNORECASE)),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]

REDACT_PLACEHOLDER = "<REDACTED>"


@dataclass
class RedactOptions:
    redact_ips: bool = False
    extra_patterns: List[re.Pattern[str]] = field(default_factory=list)
    placeholder: str = REDACT_PLACEHOLDER


@dataclass
class RedactReport:
    trace: StackTrace
    redacted_count: int
    affected_fields: List[str]

    def summary_line(self) -> str:
        if self.redacted_count == 0:
            return "No sensitive values detected."
        fields = ", ".join(sorted(set(self.affected_fields)))
        return (
            f"{self.redacted_count} redaction(s) applied across: {fields}"
        )


def _apply(text: str, patterns: List[tuple[str, re.Pattern[str]]], placeholder: str) -> tuple[str, List[str]]:
    affected: List[str] = []
    for label, pat in patterns:
        new_text, n = pat.subn(placeholder, text)
        if n:
            affected.extend([label] * n)
            text = new_text
    return text, affected


def redact_trace(trace: StackTrace, options: Optional[RedactOptions] = None) -> RedactReport:
    """Return a new StackTrace with sensitive data replaced by a placeholder."""
    if options is None:
        options = RedactOptions()

    patterns = [(lbl, pat) for lbl, pat in _DEFAULT_PATTERNS if lbl != "ipv4"]
    if options.redact_ips:
        patterns.append(("ipv4", dict(_DEFAULT_PATTERNS)["ipv4"]))
    for pat in options.extra_patterns:
        patterns.append(("custom", pat))

    ph = options.placeholder
    total = 0
    all_affected: List[str] = []

    new_message, aff = _apply(trace.exception_message, patterns, ph)
    total += len(aff)
    all_affected.extend(aff)

    new_frames: List[Frame] = []
    for fr in trace.frames:
        new_line, aff2 = _apply(fr.line or "", patterns, ph)
        total += len(aff2)
        all_affected.extend(aff2)
        new_frames.append(
            Frame(
                filename=fr.filename,
                lineno=fr.lineno,
                function=fr.function,
                line=new_line if new_line else fr.line,
            )
        )

    new_trace = StackTrace(
        exception_type=trace.exception_type,
        exception_message=new_message,
        frames=new_frames,
    )
    return RedactReport(trace=new_trace, redacted_count=total, affected_fields=all_affected)
