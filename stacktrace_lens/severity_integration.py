"""Integration helpers: attach severity info to existing formatter/exporter output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from stacktrace_lens.parser import StackTrace
from stacktrace_lens.severity import SeverityResult, format_severity, score_trace

_BADGE = {
    "LOW": "[●]",
    "MEDIUM": "[◆]",
    "HIGH": "[▲]",
    "CRITICAL": "[✖]",
}


@dataclass
class AnnotatedOutput:
    """Wraps formatted output with a prepended severity badge."""

    severity: SeverityResult
    body: str

    def render(self, *, colour: bool = True) -> str:
        badge = _BADGE.get(self.severity.label, "[?]")
        severity_line = format_severity(self.severity, colour=colour)
        divider = "-" * 60
        return f"{badge} {severity_line}\n{divider}\n{self.body}"


def annotate_with_severity(
    trace: StackTrace,
    body: str,
    *,
    colour: bool = True,
) -> AnnotatedOutput:
    """Score *trace* and return an AnnotatedOutput wrapping *body*."""
    result = score_trace(trace)
    return AnnotatedOutput(severity=result, body=body)


def severity_badge(trace: StackTrace) -> str:
    """Return just the short badge string for a trace, e.g. '[▲] HIGH'."""
    result = score_trace(trace)
    badge = _BADGE.get(result.label, "[?]")
    return f"{badge} {result.label}"
