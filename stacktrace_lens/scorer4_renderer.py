"""Rich renderer for ScoreReport4 objects."""
from __future__ import annotations

from typing import List

from .scorer4 import ScoreReport4, ScoredFrame4


class Scorer4Renderer:
    def __init__(self, no_color: bool = False) -> None:
        self._no_color = no_color

    def _c(self, text: str, code: str) -> str:
        if self._no_color:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _bar(self, score: float, width: int = 20) -> str:
        filled = int(score * width)
        bar = "█" * filled + "░" * (width - filled)
        return self._c(bar, "32")

    def _render_frame(self, sf: ScoredFrame4, rank: int) -> str:
        fn = self._c(sf.frame.function or "<module>", "36")
        loc = self._c(f"{sf.frame.filename}:{sf.frame.lineno}", "90")
        score_str = self._c(f"{sf.score:.4f}", "33")
        bar = self._bar(min(sf.score, 1.0))
        return f"  #{rank:>2}  {fn}  {loc}\n        score={score_str}  {bar}"

    def render(self, report: ScoreReport4, top: int = 0) -> str:
        lines: List[str] = []
        title = self._c("Score4 Report", "1;35")
        exc = self._c(report.exception_type or "<unknown>", "1;31")
        w = self._c(f"{report.exception_weight:.2f}", "33")
        lines.append(f"{title} — {exc} (weight={w})")
        lines.append(self._c("-" * 50, "90"))
        frames = report.ranked()
        if top > 0:
            frames = frames[:top]
        for rank, sf in enumerate(frames, start=1):
            lines.append(self._render_frame(sf, rank))
        lines.append(self._c("-" * 50, "90"))
        total_str = self._c(str(report.count), "1")
        lines.append(f"Total frames scored: {total_str}")
        return "\n".join(lines)
