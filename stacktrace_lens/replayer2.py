"""replayer2: replay stack traces with configurable speed and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class ReplayOptions:
    max_events: Optional[int] = None
    skip_duplicates: bool = False
    reverse: bool = False


@dataclass
class ReplayEvent2:
    index: int
    trace: StackTrace
    skipped: bool = False

    def __str__(self) -> str:
        status = "[skipped]" if self.skipped else "[replayed]"
        return f"Event #{self.index} {status}: {self.trace.exception_type}"


@dataclass
class ReplayReport2:
    events: List[ReplayEvent2] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    @property
    def replayed_count(self) -> int:
        return sum(1 for e in self.events if not e.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for e in self.events if e.skipped)

    def summary_line(self) -> str:
        return (
            f"Replayed {self.replayed_count}/{self.count} events"
            f" ({self.skipped_count} skipped)"
        )


def replay_traces(
    traces: List[StackTrace],
    options: Optional[ReplayOptions] = None,
) -> ReplayReport2:
    """Replay a list of stack traces according to *options*."""
    if options is None:
        options = ReplayOptions()

    ordered = list(reversed(traces)) if options.reverse else list(traces)
    if options.max_events is not None:
        ordered = ordered[: options.max_events]

    report = ReplayReport2()
    seen: set = set()

    for idx, trace in enumerate(ordered):
        key = (trace.exception_type, trace.exception_message)
        skipped = options.skip_duplicates and key in seen
        if not skipped:
            seen.add(key)
        report.events.append(ReplayEvent2(index=idx, trace=trace, skipped=skipped))

    return report
