"""Render annotated frames as coloured terminal output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from stacktrace_lens.annotator import AnnotatedFrame, AnnotatedLine, AnnotationOptions
from stacktrace_lens.formatter import FormatOptions

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"


@dataclass
class AnnotationRenderer:
    format_opts: FormatOptions
    annotation_opts: AnnotationOptions

    def _colour(self, text: str, code: str) -> str:
        if not self.format_opts.colour:
            return text
        return f"{code}{text}{_RESET}"

    def _render_line(self, line: AnnotatedLine) -> str:
        lineno_str = f"{line.lineno:>4} | "
        if self.format_opts.colour:
            lineno_str = self._colour(lineno_str, _DIM)
        content = line.content
        if line.is_error_line:
            content = self._colour(content, _RED)
            marker = self._colour(" <--", _YELLOW + _BOLD)
            return f"{lineno_str}{content}{marker}"
        return f"{lineno_str}{content}"

    def render(self, annotated: AnnotatedFrame) -> str:
        """Return a multi-line string representing the annotated frame."""
        frame = annotated.frame
        header = self._colour(
            f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.function}",
            _CYAN,
        )
        parts: List[str] = [header]
        if annotated.source_available:
            for ln in annotated.lines:
                parts.append(self._render_line(ln))
        else:
            parts.append(self._colour("    <source not available>", _DIM))
        return "\n".join(parts)

    def render_all(self, frames: List[AnnotatedFrame]) -> str:
        return "\n".join(self.render(f) for f in frames)
