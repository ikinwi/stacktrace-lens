"""Truncator: shorten long stack traces by keeping head and tail frames."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class TruncateOptions:
    head: int = 3  # frames to keep from the top
    tail: int = 3  # frames to keep from the bottom
    placeholder: str = "... {n} frames omitted ..."


@dataclass
class TruncateReport:
    original_count: int
    kept_count: int
    omitted_count: int
    frames: List[Frame]
    placeholder_index: int  # index where placeholder sits (-1 if no truncation)
    exception_type: str
    exception_message: str

    @property
    def was_truncated(self) -> bool:
        return self.omitted_count > 0

    def summary_line(self) -> str:
        if not self.was_truncated:
            return f"All {self.original_count} frame(s) kept — no truncation needed."
        return (
            f"Truncated {self.original_count} → {self.kept_count} frames "
            f"({self.omitted_count} omitted)."
        )


def truncate_trace(
    trace: StackTrace,
    options: TruncateOptions | None = None,
) -> TruncateReport:
    """Return a TruncateReport with head + tail frames from *trace*."""
    opts = options or TruncateOptions()
    frames = list(trace.frames)
    total = len(frames)
    head = max(0, opts.head)
    tail = max(0, opts.tail)

    if head + tail >= total:
        # Nothing to omit
        return TruncateReport(
            original_count=total,
            kept_count=total,
            omitted_count=0,
            frames=frames,
            placeholder_index=-1,
            exception_type=trace.exception_type,
            exception_message=trace.exception_message,
        )

    kept_head = frames[:head]
    kept_tail = frames[total - tail :] if tail else []
    omitted = total - head - tail
    kept = kept_head + kept_tail

    return TruncateReport(
        original_count=total,
        kept_count=len(kept),
        omitted_count=omitted,
        frames=kept,
        placeholder_index=head,
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
    )


def format_truncation(
    report: TruncateReport,
    options: TruncateOptions | None = None,
    colour: bool = True,
) -> str:
    """Render a truncated trace to a human-readable string."""
    opts = options or TruncateOptions()
    _YELLOW = "\033[33m" if colour else ""
    _CYAN = "\033[36m" if colour else ""
    _RESET = "\033[0m" if colour else ""

    lines: List[str] = []
    lines.append(
        f"{_CYAN}{report.exception_type}{_RESET}: {report.exception_message}"
    )

    for idx, frame in enumerate(report.frames):
        if report.was_truncated and idx == report.placeholder_index:
            placeholder = opts.placeholder.format(n=report.omitted_count)
            lines.append(f"  {_YELLOW}{placeholder}{_RESET}")
        lines.append(f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.function}")

    lines.append("")
    lines.append(report.summary_line())
    return "\n".join(lines)
