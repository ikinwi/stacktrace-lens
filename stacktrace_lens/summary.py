"""High-level summary renderer combining filters and grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.filters import FilterOptions, filter_frames
from stacktrace_lens.grouper import FrameGroup, group_frames
from stacktrace_lens.parser import StackTrace


@dataclass
class SummaryOptions:
    """Options for the summary view."""

    filter_options: FilterOptions = field(default_factory=FilterOptions)
    show_frame_detail: bool = False
    indent: str = "  "


def render_summary(trace: StackTrace, options: SummaryOptions | None = None) -> str:
    """Return a concise multi-line summary string for *trace*."""
    if options is None:
        options = SummaryOptions()

    filtered = filter_frames(trace, options.filter_options)
    groups: List[FrameGroup] = group_frames(filtered)

    lines: List[str] = []
    lines.append(
        f"{trace.exception_type}: {trace.exception_message}"
    )
    lines.append(f"Traceback ({len(filtered.frames)} frames across {len(groups)} group(s)):")

    for group in groups:
        lines.append(f"{options.indent}[{group.label}] — {group.count} frame(s)")
        if options.show_frame_detail:
            for frame in group.frames:
                lines.append(
                    f"{options.indent * 2}{frame.filename}:{frame.lineno} in {frame.function}()"
                )

    return "\n".join(lines)
