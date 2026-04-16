"""Renderer for FuseReport."""
from __future__ import annotations
from stacktrace_lens.fuser import FuseReport, FusedFrame


SOURCE_COLORS = {
    "both": "32",
    "left": "33",
    "right": "36",
}

SOURCE_LABELS = {
    "both": "shared",
    "left": "left-only",
    "right": "right-only",
}


class FuserRenderer:
    def __init__(self, color: bool = True) -> None:
        self._color = color

    def _c(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self._color else text

    def _render_frame(self, ff: FusedFrame) -> str:
        code = SOURCE_COLORS[ff.source]
        label = SOURCE_LABELS[ff.source]
        fn = ff.frame.function or "<module>"
        body = f"{ff.frame.filename}:{ff.frame.lineno} in {fn}  [{label}]"
        return self._c(code, body)

    def render(self, report: FuseReport) -> str:
        lines = [
            self._c("1", report.summary_line()),
            f"  Left : {report.left_exception}",
            f"  Right: {report.right_exception}",
            "",
        ]
        for ff in report.frames:
            lines.append(self._render_frame(ff))
        return "\n".join(lines)
