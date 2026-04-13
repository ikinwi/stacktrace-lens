"""Renderer for split (chained) stack trace reports."""
from __future__ import annotations

from typing import List

from .splitter import SplitReport
from .parser import StackTrace


class SplitterRenderer:
    """Pretty-print a SplitReport with optional colour."""

    _COLOURS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "cyan": "\033[36m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "dim": "\033[2m",
    }

    def __init__(self, colour: bool = True) -> None:
        self._colour = colour

    def _c(self, code: str, text: str) -> str:
        if not self._colour:
            return text
        return f"{self._COLOURS.get(code, '')}{text}{self._COLOURS['reset']}"

    def _render_trace(self, index: int, trace: StackTrace) -> List[str]:
        lines: List[str] = []
        header = self._c("cyan", f"── Trace {index + 1} ")
        exc = self._c("bold", trace.exception_type or "<unknown>")
        msg = self._c("dim", f": {trace.exception_message}") if trace.exception_message else ""
        lines.append(f"{header}{exc}{msg}")
        for frame in trace.frames:
            filename = self._c("yellow", frame.filename or "<unknown>")
            lineno = frame.lineno or "?"
            func = frame.function or "<module>"
            lines.append(f"  File {filename}, line {lineno}, in {func}")
            if frame.code:
                lines.append(f"    {self._c('dim', frame.code.strip())}")
        return lines

    def render(self, report: SplitReport) -> str:
        """Return a formatted string representing the split report."""
        lines: List[str] = []
        chained_label = (
            self._c("red", "[chained exception]")
            if report.is_chained
            else self._c("dim", "[single exception]")
        )
        lines.append(
            self._c("bold", f"SplitReport") + f" — {len(report.traces)} trace(s) {chained_label}"
        )
        lines.append("")
        for i, trace in enumerate(report.traces):
            lines.extend(self._render_trace(i, trace))
            lines.append("")
        return "\n".join(lines).rstrip()
