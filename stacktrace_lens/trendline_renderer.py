"""Colour renderer for TrendReport objects."""
from __future__ import annotations

from stacktrace_lens.trendline import TrendReport


class TrendlineRenderer:
    """Renders a TrendReport with optional ANSI colour."""

    _RESET = "\x1b[0m"
    _BOLD = "\x1b[1m"
    _GREEN = "\x1b[32m"
    _RED = "\x1b[31m"
    _CYAN = "\x1b[36m"
    _YELLOW = "\x1b[33m"

    def __init__(self, colour: bool = True) -> None:
        self._colour = colour

    def _c(self, code: str, text: str) -> str:
        if not self._colour:
            return text
        return f"{code}{text}{self._RESET}"

    def _bar(self, count: int, max_count: int, width: int = 30) -> str:
        if max_count == 0:
            filled = 0
        else:
            filled = int((count / max_count) * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def render(self, report: TrendReport) -> str:
        lines: list[str] = []

        direction = "↑ rising" if report.rising else "→ stable/falling"
        dir_colour = self._RED if report.rising else self._GREEN
        header = (
            self._c(self._BOLD, "Trendline Report")
            + "  "
            + self._c(dir_colour, direction)
        )
        lines.append(header)

        top_exc = report.most_frequent_exception or "N/A"
        lines.append(
            f"  Total traces : {self._c(self._CYAN, str(report.total_traces))}"
        )
        lines.append(
            f"  Top exception: {self._c(self._YELLOW, top_exc)}"
        )
        lines.append("")

        max_count = max((p.count for p in report.points), default=1)
        for point in report.points:
            bar = self._bar(point.count, max_count)
            count_str = self._c(self._CYAN, str(point.count))
            lines.append(f"  {point.label:>14}  {bar}  {count_str}")

        return "\n".join(lines)
