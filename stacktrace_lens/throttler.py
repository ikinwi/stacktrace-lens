"""Throttler: rate-limit a stream of stack traces by time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class ThrottleOptions:
    window_seconds: float = 60.0
    max_per_window: int = 10


@dataclass
class ThrottleReport:
    total: int
    allowed: int
    dropped: int
    traces: List[StackTrace]
    window_seconds: float
    max_per_window: int

    def summary_line(self) -> str:
        return (
            f"Throttled {self.dropped}/{self.total} traces "
            f"(window={self.window_seconds}s, max={self.max_per_window})"
        )


def throttle_traces(
    traces: List[StackTrace],
    options: Optional[ThrottleOptions] = None,
    *,
    now: Optional[datetime] = None,
) -> ThrottleReport:
    """Return only the first *max_per_window* traces that fall within each
    rolling time window.  Traces without a timestamp are always allowed."""
    if options is None:
        options = ThrottleOptions()
    if now is None:
        now = datetime.utcnow()

    window = timedelta(seconds=options.window_seconds)
    bucket_start: Optional[datetime] = None
    bucket_count = 0

    allowed: List[StackTrace] = []
    dropped = 0

    for trace in traces:
        ts: Optional[datetime] = getattr(trace, "timestamp", None)
        if ts is None:
            # No timestamp — always let through
            allowed.append(trace)
            continue

        if bucket_start is None or ts >= bucket_start + window:
            bucket_start = ts
            bucket_count = 0

        if bucket_count < options.max_per_window:
            allowed.append(trace)
            bucket_count += 1
        else:
            dropped += 1

    return ThrottleReport(
        total=len(traces),
        allowed=len(allowed),
        dropped=dropped,
        traces=allowed,
        window_seconds=options.window_seconds,
        max_per_window=options.max_per_window,
    )
