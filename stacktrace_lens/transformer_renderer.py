"""Colour-aware renderer for TransformReport output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.transformer import TransformReport, TransformedFrame


@dataclass
class TransformerRenderer:
    use_colour: bool = True

    # ANSI helpers
    def _c(self, code: str, text: str) -> str:
        if not self.use_colour:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _render_frame(self, tf: TransformedFrame, index: int) -> str:
        num = self._c("2", f"#{index + 1}")
        filename = self._c("36", tf.result.filename)
        lineno = self._c("33", str(tf.result.lineno))
        func = self._c("32", tf.result.function)
        line = f"  {num} {filename}:{lineno} in {func}"
        if tf.rules_applied:
            tags = ", ".join(self._c("35", r) for r in tf.rules_applied)
            line += f"  [{tags}]"
        return line

    def render(self, report: TransformReport) -> str:
        lines: List[str] = []

        exc_type = self._c("1;31", report.original_trace.exception_type)
        exc_msg = self._c("37", report.original_trace.exception_message)
        lines.append(f"{exc_type}: {exc_msg}")
        lines.append("")

        for i, tf in enumerate(report.frames):
            lines.append(self._render_frame(tf, i))

        lines.append("")
        summary = self._c("1", report.summary_line())
        lines.append(summary)
        return "\n".join(lines)

    def render_all(self, reports: List[TransformReport]) -> str:
        return "\n\n".join(self.render(r) for r in reports)
