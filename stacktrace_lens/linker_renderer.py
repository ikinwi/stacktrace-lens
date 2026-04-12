"""linker_renderer.py – coloured console rendering for LinkReport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from stacktrace_lens.linker import LinkReport, LinkedFrame


@dataclass
class LinkerRenderer:
    colour: bool = True

    # ANSI helpers
    def _c(self, code: str, text: str) -> str:
        if not self.colour:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _render_frame(self, lf: LinkedFrame, index: int) -> str:
        idx = self._c("2", f"#{index + 1}")
        func = self._c("1", lf.frame.function or "<unknown>")
        loc = self._c("33", f"{lf.frame.filename}:{lf.frame.lineno}")
        if lf.url:
            link = self._c("36", lf.url)
            return f"  {idx} {func}  {loc}\n       {link}"
        return f"  {idx} {func}  {loc}  (no link)"

    def render(self, report: LinkReport) -> str:
        header = self._c("1;34", f"Link Report [{report.scheme}]")
        summary = self._c("32", report.summary_line())
        body_lines = [header, summary]
        for i, lf in enumerate(report.frames):
            body_lines.append(self._render_frame(lf, i))
        return "\n".join(body_lines)


def render_link_report(report: LinkReport, colour: bool = True) -> str:
    """Convenience wrapper around LinkerRenderer."""
    return LinkerRenderer(colour=colour).render(report)
