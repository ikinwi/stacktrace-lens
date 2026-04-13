"""Replay recorded stack traces with timing and playback controls."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional
import time

from stacktrace_lens.parser import StackTrace


@dataclass
class ReplayOptions:
    speed: float = 1.0          # multiplier: 2.0 = twice as fast
    max_entries: Optional[int] = None
    loop: bool = False


@dataclass
class ReplayEvent:
    index: int
    trace: StackTrace
    elapsed: float              # seconds since replay started
    label: Optional[str] = None

    def __str__(self) -> str:
        tag = f"[{self.label}] " if self.label else ""
        return (
            f"Event #{self.index} {tag}@ {self.elapsed:.2f}s — "
            f"{self.trace.exception_type}: {self.trace.exception_message}"
        )


@dataclass
class ReplayReport:
    events: List[ReplayEvent] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    def summary_line(self) -> str:
        return f"Replayed {self.count} event(s)."


def replay_traces(
    entries: List[tuple],          # list of (StackTrace, Optional[str]) pairs
    options: Optional[ReplayOptions] = None,
) -> ReplayReport:
    """Replay *entries* according to *options* and return a ReplayReport.

    Each entry is a ``(trace, label)`` tuple.  Timing is simulated; no
    real sleeping is performed so the function is safe to call in tests.
    """
    if options is None:
        options = ReplayOptions()

    pool = list(entries)
    if options.max_entries is not None:
        pool = pool[: options.max_entries]

    report = ReplayReport()
    start = time.monotonic()
    idx = 0

    iteration = pool if not options.loop else _loop_forever(pool)
    for trace, label in iteration:
        elapsed = (time.monotonic() - start) / max(options.speed, 1e-9)
        event = ReplayEvent(index=idx, trace=trace, elapsed=elapsed, label=label)
        report.events.append(event)
        idx += 1
        if options.max_entries is not None and idx >= options.max_entries:
            break

    return report


def _loop_forever(pool: List) -> Iterator:
    while True:
        yield from pool
