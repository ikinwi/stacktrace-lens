"""Deduplicator: collapse repeated consecutive frames in a stack trace."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class DeduplicatedFrame:
    """A frame that may represent multiple identical consecutive occurrences."""

    frame: Frame
    count: int = 1

    @property
    def is_repeated(self) -> bool:
        return self.count > 1


@dataclass
class DeduplicateOptions:
    """Options controlling deduplication behaviour."""

    min_repeat: int = 2  # minimum repetitions before collapsing
    key_on_function: bool = True  # include function name in equality key
    key_on_lineno: bool = False  # include line number in equality key


def _frame_key(frame: Frame, opts: DeduplicateOptions) -> tuple:
    parts: list = [frame.filename]
    if opts.key_on_function:
        parts.append(frame.function)
    if opts.key_on_lineno:
        parts.append(frame.lineno)
    return tuple(parts)


def deduplicate_frames(
    trace: StackTrace,
    opts: DeduplicateOptions | None = None,
) -> List[DeduplicatedFrame]:
    """Return a list of DeduplicatedFrame objects with consecutive duplicates collapsed."""
    if opts is None:
        opts = DeduplicateOptions()

    result: List[DeduplicatedFrame] = []

    for frame in trace.frames:
        key = _frame_key(frame, opts)
        if result and _frame_key(result[-1].frame, opts) == key:
            result[-1].count += 1
        else:
            result.append(DeduplicatedFrame(frame=frame, count=1))

    # Expand back any groups that don't meet the min_repeat threshold
    expanded: List[DeduplicatedFrame] = []
    for df in result:
        if df.count < opts.min_repeat:
            for _ in range(df.count):
                expanded.append(DeduplicatedFrame(frame=df.frame, count=1))
        else:
            expanded.append(df)

    return expanded


def format_deduplicated(
    deduped: List[DeduplicatedFrame],
    colour: bool = True,
) -> str:
    """Render a deduplicated frame list to a human-readable string."""
    YELLOW = "\033[33m" if colour else ""
    RESET = "\033[0m" if colour else ""

    lines: List[str] = []
    for df in deduped:
        f = df.frame
        line = f'  File "{f.filename}", line {f.lineno}, in {f.function}'
        if df.is_repeated:
            line += f"  {YELLOW}[repeated {df.count}\u00d7]{RESET}"
        lines.append(line)
        if f.code:
            lines.append(f"    {f.code}")
    return "\n".join(lines)


def summary_stats(deduped: List[DeduplicatedFrame]) -> dict:
    """Return basic statistics about a deduplicated frame list.

    Returns a dict with:
      - ``total_frames``: number of frames before deduplication (sum of counts).
      - ``unique_frames``: number of distinct frame entries after deduplication.
      - ``collapsed_frames``: number of frames that were collapsed (repeated ones).
    """
    total = sum(df.count for df in deduped)
    unique = len(deduped)
    collapsed = sum(df.count - 1 for df in deduped if df.is_repeated)
    return {
        "total_frames": total,
        "unique_frames": unique,
        "collapsed_frames": collapsed,
    }
