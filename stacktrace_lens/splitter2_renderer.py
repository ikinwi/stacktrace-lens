"""Rich renderer for :class:`SegmentReport`."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from stacktrace_lens.splitter2 import Segment, SegmentReport


@dataclass
class Splitter2Renderer:
    """Render a :class:`SegmentReport` to a coloured string."""

    use_color: bool = True
    indent: str = "  "

    # ------------------------------------------------------------------
    def _c(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.use_color else text

    def _render_segment(self, seg: Segment, index: int) -> List[str]:
        lines: List[str] = []
        header = self._c("1;33", f"{self.indent}Segment {index + 1}: {seg.label}")
        lines.append(f"{header}  ({seg.count} frame(s))")
        for frame in seg.frames:
            fn = frame.function or "<module>"
            fname = self._c("36", frame.filename or "<unknown>")
            lineno = self._c("33", str(frame.lineno))
            func = self._c("32", fn)
            lines.append(f"{self.indent * 2}{fname}:{lineno}  {func}")
        return lines

    def render(self, report: SegmentReport) -> str:
        lines: List[str] = [
            self._c("1;34", report.summary_line()),
        ]
        for idx, seg in enumerate(report.segments):
            lines.extend(self._render_segment(seg, idx))
        return "\n".join(lines)
