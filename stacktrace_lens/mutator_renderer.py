"""Renderer for MutateReport with optional colour output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from stacktrace_lens.mutator import MutateReport, MutatedFrame


@dataclass
class MutatorRenderer:
    colour: bool = True

    def _c(self, text: str, code: str) -> str:
        if not self.colour:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _render_frame(self, mf: MutatedFrame) -> str:
        tag = (
            self._c("[changed]", "33")
            if mf.changed
            else self._c("[unchanged]", "90")
        )
        filename = self._c(mf.result.filename, "36")
        lineno = self._c(str(mf.result.lineno), "33")
        function = self._c(mf.result.function, "32")
        return f"  {tag} {filename}:{lineno} in {function}"

    def render(self, report: MutateReport) -> str:
        lines: List[str] = []
        header = self._c(report.summary_line(), "1")
        lines.append(header)
        for mf in report.frames:
            lines.append(self._render_frame(mf))
        return "\n".join(lines)
