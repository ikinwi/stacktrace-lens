"""Rich-text renderer for CorrelationReport, reusing formatter colour helpers."""

from __future__ import annotations

from typing import List

from .correlator import CorrelationReport
from .formatter import FormatOptions


class CorrelationRenderer:
    """Render a CorrelationReport with optional ANSI colour."""

    def __init__(self, options: FormatOptions | None = None) -> None:
        self._opts = options or FormatOptions()

    def _c(self, text: str, code: str) -> str:
        if not self._opts.use_color:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _header(self, title: str) -> str:
        return self._c(title, "1;36")

    def _key(self, text: str) -> str:
        return self._c(text, "33")

    def _count(self, n: int) -> str:
        colour = "31" if n >= 5 else "32" if n == 1 else "33"
        return self._c(str(n), colour)

    def render(self, report: CorrelationReport) -> str:
        lines: List[str] = []
        lines.append(self._header(f"Correlation Report — {report.total_traces} trace(s)"))
        lines.append(self._c("=" * 44, "90"))

        mc_exc = report.most_common_exception()
        if mc_exc:
            lines.append(
                f"  Most common exception : {self._key(mc_exc[0])}  "
                f"[{self._count(mc_exc[1])}x]"
            )

        mc_file = report.most_common_file()
        if mc_file:
            lines.append(
                f"  Most common file      : {self._key(mc_file[0])}  "
                f"[{self._count(mc_file[1])}x]"
            )

        mc_fn = report.most_common_function()
        if mc_fn:
            lines.append(
                f"  Most common function  : {self._key(mc_fn[0])}  "
                f"[{self._count(mc_fn[1])}x]"
            )

        lines.append("")
        lines.append(self._header("Exception breakdown:"))
        for key, grp in sorted(
            report.by_exception.items(), key=lambda kv: -kv[1].count
        ):
            bar = self._c("█" * min(grp.count, 20), "35")
            lines.append(f"  {self._key(key):<40} {self._count(grp.count):>4}  {bar}")

        return "\n".join(lines)
