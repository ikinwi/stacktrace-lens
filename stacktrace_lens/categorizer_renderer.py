"""Colour-aware renderer for CategorizationResult objects."""
from __future__ import annotations

from stacktrace_lens.categorizer import CategorizationResult

_CATEGORY_COLOURS = {
    "dependency": "\033[33m",   # yellow
    "runtime":    "\033[31m",   # red
    "io":         "\033[34m",   # blue
    "network":    "\033[35m",   # magenta
    "resource":   "\033[91m",   # bright red
    "assertion":  "\033[36m",   # cyan
    "syntax":     "\033[95m",   # bright magenta
    "unknown":    "\033[90m",   # dark grey
}
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"


class CategorizerRenderer:
    """Render a :class:`CategorizationResult` with optional ANSI colour."""

    def __init__(self, colour: bool = True) -> None:
        self._colour = colour

    def _c(self, code: str, text: str) -> str:
        if self._colour:
            return f"{code}{text}{_RESET}"
        return text

    def _category_badge(self, category: str) -> str:
        colour = _CATEGORY_COLOURS.get(category, _CATEGORY_COLOURS["unknown"])
        return self._c(colour, f"[{category.upper()}]")

    def _confidence_bar(self, confidence: float) -> str:
        filled = round(confidence * 10)
        bar = "█" * filled + "░" * (10 - filled)
        pct = f"{confidence:.0%}"
        return self._c(_DIM, f"|{bar}| {pct}")

    def render(self, result: CategorizationResult) -> str:
        """Return a formatted, optionally coloured string for *result*."""
        exc = self._c(_BOLD, result.exception_type)
        badge = self._category_badge(result.category)
        bar = self._confidence_bar(result.confidence)
        lines = [f"{exc}  {badge}  {bar}"]
        for note in result.notes:
            lines.append(self._c(_DIM, f"  ⚠  {note}"))
        return "\n".join(lines)
