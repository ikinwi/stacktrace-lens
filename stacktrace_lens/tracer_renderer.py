"""Render a Lineage tree to a coloured string."""
from __future__ import annotations

from typing import List, Optional

from stacktrace_lens.tracer import Lineage, TraceNode


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "red": "\033[31m",
}


class TracerRenderer:
    def __init__(self, colour: bool = True) -> None:
        self._colour = colour

    def _c(self, text: str, *codes: str) -> str:
        if not self._colour:
            return text
        prefix = "".join(ANSI.get(c, "") for c in codes)
        return f"{prefix}{text}{ANSI['reset']}"

    def _render_node(self, lineage: Lineage, node_id: str,
                     indent: int, lines: List[str]) -> None:
        node = lineage.get(node_id)
        if node is None:
            return
        depth = lineage.depth_of(node_id)
        connector = "  " * indent + ("└─ " if indent else "")
        exc = node.trace.exception_type or "Unknown"
        msg = node.trace.exception_message or ""
        short_msg = (msg[:40] + "…") if len(msg) > 40 else msg
        label_part = self._c(f" [{node.label}]", "green") if node.label else ""
        exc_part = self._c(exc, "red", "bold")
        msg_part = self._c(f": {short_msg}", "yellow") if short_msg else ""
        id_part = self._c(f" ({node.trace_id[:8]})", "cyan")
        lines.append(f"{connector}{exc_part}{msg_part}{label_part}{id_part}")
        for child_id in node.children:
            self._render_node(lineage, child_id, indent + 1, lines)

    def render(self, lineage: Lineage) -> str:
        lines: List[str] = []
        for root in lineage.roots():
            self._render_node(lineage, root.trace_id, 0, lines)
        return "\n".join(lines)

    def render_summary(self, lineage: Lineage) -> str:
        total = lineage.size()
        roots = len(lineage.roots())
        header = self._c(f"Lineage: {total} trace(s), {roots} root(s)", "bold")
        tree = self.render(lineage)
        return f"{header}\n{tree}" if tree else header
