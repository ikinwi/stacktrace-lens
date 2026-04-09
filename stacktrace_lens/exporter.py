"""Export parsed stack traces to various output formats (plain text, JSON, Markdown)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Literal

from stacktrace_lens.parser import StackTrace
from stacktrace_lens.suggestions import get_all_suggestions

ExportFormat = Literal["text", "json", "markdown"]


@dataclass
class ExportOptions:
    fmt: ExportFormat = "text"
    include_suggestions: bool = True
    indent: int = 2


class StackTraceExporter:
    def __init__(self, options: ExportOptions | None = None) -> None:
        self.options = options or ExportOptions()

    def export(self, trace: StackTrace) -> str:
        fmt = self.options.fmt
        if fmt == "json":
            return self._to_json(trace)
        if fmt == "markdown":
            return self._to_markdown(trace)
        return self._to_text(trace)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _suggestions(self, trace: StackTrace) -> list[str]:
        if not self.options.include_suggestions:
            return []
        return get_all_suggestions(trace)

    def _to_text(self, trace: StackTrace) -> str:
        lines: list[str] = []
        lines.append(f"Exception : {trace.exception_type}")
        lines.append(f"Message   : {trace.exception_message}")
        lines.append("Frames:")
        for i, frame in enumerate(trace.frames, 1):
            lines.append(f"  [{i}] {frame.filename}:{frame.lineno} in {frame.function}")
            if frame.code:
                lines.append(f"       > {frame.code.strip()}")
        suggestions = self._suggestions(trace)
        if suggestions:
            lines.append("Suggestions:")
            for s in suggestions:
                lines.append(f"  • {s}")
        return "\n".join(lines)

    def _to_json(self, trace: StackTrace) -> str:
        payload: dict = {
            "exception_type": trace.exception_type,
            "exception_message": trace.exception_message,
            "frames": [
                {
                    "filename": f.filename,
                    "lineno": f.lineno,
                    "function": f.function,
                    "code": f.code,
                }
                for f in trace.frames
            ],
        }
        if self.options.include_suggestions:
            payload["suggestions"] = self._suggestions(trace)
        return json.dumps(payload, indent=self.options.indent)

    def _to_markdown(self, trace: StackTrace) -> str:
        lines: list[str] = []
        lines.append(f"## `{trace.exception_type}`")
        lines.append(f"> {trace.exception_message}")
        lines.append("")
        lines.append("### Traceback")
        for i, frame in enumerate(trace.frames, 1):
            lines.append(f"{i}. **{frame.function}** — `{frame.filename}:{frame.lineno}`")
            if frame.code:
                lines.append(f"   ```python\n   {frame.code.strip()}\n   ```")
        suggestions = self._suggestions(trace)
        if suggestions:
            lines.append("")
            lines.append("### Suggestions")
            for s in suggestions:
                lines.append(f"- {s}")
        return "\n".join(lines)
