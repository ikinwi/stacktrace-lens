"""Timeline module: assign timestamps to parsed stack traces and render a
simple chronological log of multiple traces."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class TimestampedTrace:
    """A stack trace paired with a capture timestamp."""

    trace: StackTrace
    captured_at: datetime.datetime = field(
        default_factory=datetime.datetime.utcnow
    )
    label: Optional[str] = None

    def age_seconds(self, reference: Optional[datetime.datetime] = None) -> float:
        ref = reference or datetime.datetime.utcnow()
        return (ref - self.captured_at).total_seconds()


@dataclass
class Timeline:
    """Ordered collection of timestamped traces."""

    entries: List[TimestampedTrace] = field(default_factory=list)

    def add(self, trace: StackTrace, label: Optional[str] = None,
            captured_at: Optional[datetime.datetime] = None) -> TimestampedTrace:
        ts = captured_at or datetime.datetime.utcnow()
        entry = TimestampedTrace(trace=trace, captured_at=ts, label=label)
        self.entries.append(entry)
        return entry

    def sorted_entries(self) -> List[TimestampedTrace]:
        return sorted(self.entries, key=lambda e: e.captured_at)

    def most_recent(self) -> Optional[TimestampedTrace]:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.captured_at)

    def earliest(self) -> Optional[TimestampedTrace]:
        if not self.entries:
            return None
        return min(self.entries, key=lambda e: e.captured_at)


def render_timeline(timeline: Timeline, use_colour: bool = True) -> str:
    """Render a human-readable timeline summary."""
    lines: List[str] = []
    RESET = "\033[0m" if use_colour else ""
    BOLD = "\033[1m" if use_colour else ""
    CYAN = "\033[36m" if use_colour else ""
    YELLOW = "\033[33m" if use_colour else ""

    entries = timeline.sorted_entries()
    if not entries:
        return "(no timeline entries)"

    lines.append(f"{BOLD}Timeline — {len(entries)} trace(s){RESET}")
    lines.append("─" * 50)

    for idx, entry in enumerate(entries, start=1):
        ts_str = entry.captured_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        label_str = f" [{entry.label}]" if entry.label else ""
        exc = f"{entry.trace.exception_type}: {entry.trace.exception_message}"
        frame_count = len(entry.trace.frames)
        lines.append(
            f"{CYAN}#{idx}{RESET} {YELLOW}{ts_str}{RESET}{label_str}\n"
            f"   {BOLD}{exc}{RESET}  ({frame_count} frame(s))"
        )

    return "\n".join(lines)
