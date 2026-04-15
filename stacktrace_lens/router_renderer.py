"""Render RouteResult objects with optional colour."""
from __future__ import annotations

from typing import List

from stacktrace_lens.router import RouteResult


class RouterRenderer:
    def __init__(self, color: bool = True) -> None:
        self._color = color

    def _c(self, text: str, code: str) -> str:
        if not self._color:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _render_result(self, result: RouteResult, index: int) -> str:
        lines: List[str] = []
        header = self._c(f"[Trace {index + 1}]", "1;34")
        exc = self._c(
            result.trace.exception_type or "<unknown>", "1;31"
        )
        lines.append(f"{header} {exc}: {result.trace.exception_message or ''}".rstrip())
        if result.routed:
            rules_str = ", ".join(
                self._c(r, "1;33") for r in result.matched_rules
            )
            lines.append(f"  Routed to: {rules_str}")
        else:
            lines.append("  " + self._c("No route matched", "2"))
        return "\n".join(lines)

    def render(self, results: List[RouteResult]) -> str:
        if not results:
            return self._c("No results to display.", "2")
        return "\n\n".join(self._render_result(r, i) for i, r in enumerate(results))

    def render_all(self, results: List[RouteResult]) -> None:
        print(self.render(results))
