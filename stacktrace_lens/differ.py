"""Frame-level diff renderer that highlights additions and removals between two traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.comparator import TraceDiff, FrameDiff


@dataclass
class DiffLine:
    kind: str  # 'added', 'removed', 'unchanged'
    text: str

    def __str__(self) -> str:  # pragma: no cover
        return self.text


@dataclass
class DiffRenderOptions:
    colour: bool = True
    context_lines: int = 2
    show_unchanged: bool = True


_COLOURS = {
    "added": "\033[32m",
    "removed": "\033[31m",
    "unchanged": "\033[0m",
    "reset": "\033[0m",
    "header": "\033[36m",
}


def _frame_text(fd: FrameDiff) -> str:
    f = fd.frame
    return f"  File \"{f.filename}\", line {f.lineno}, in {f.function}"


def render_diff(diff: TraceDiff, options: Optional[DiffRenderOptions] = None) -> str:
    """Render a TraceDiff as a human-readable unified-style string."""
    if options is None:
        options = DiffRenderOptions()

    lines: List[DiffLine] = []

    def _c(kind: str, text: str) -> str:
        if not options.colour:
            return text
        return f"{_COLOURS.get(kind, '')}{text}{_COLOURS['reset']}"

    # Header
    if diff.exception_type_changed:
        lines.append(DiffLine("removed", _c("removed", f"- exception: {diff.left.exception_type}")))
        lines.append(DiffLine("added", _c("added", f"+ exception: {diff.right.exception_type}")))
    else:
        lines.append(DiffLine("unchanged", _c("unchanged", f"  exception: {diff.left.exception_type}")))

    if diff.exception_message_changed:
        lines.append(DiffLine("removed", _c("removed", f"- message: {diff.left.exception_message}")))
        lines.append(DiffLine("added", _c("added", f"+ message: {diff.right.exception_message}")))
    else:
        lines.append(DiffLine("unchanged", _c("unchanged", f"  message: {diff.left.exception_message}")))

    lines.append(DiffLine("unchanged", ""))

    for fd in diff.frame_diffs:
        if fd.status == "added":
            lines.append(DiffLine("added", _c("added", f"+ {_frame_text(fd).strip()}")))
        elif fd.status == "removed":
            lines.append(DiffLine("removed", _c("removed", f"- {_frame_text(fd).strip()}")))
        else:
            if options.show_unchanged:
                lines.append(DiffLine("unchanged", _c("unchanged", f"  {_frame_text(fd).strip()}")))

    return "\n".join(dl.text for dl in lines)


def summary_line(diff: TraceDiff) -> str:
    """Return a one-line summary of a TraceDiff."""
    from stacktrace_lens.comparator import added_count, removed_count
    a = added_count(diff)
    r = removed_count(diff)
    changed = int(diff.exception_type_changed) + int(diff.exception_message_changed)
    return f"TraceDiff: +{a} frame(s), -{r} frame(s), {changed} header change(s)"
