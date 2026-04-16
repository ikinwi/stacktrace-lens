"""Sliding window analysis over a sequence of stack traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class WindowStats:
    start_index: int
    end_index: int
    traces: List[StackTrace]
    exception_types: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.traces)

    @property
    def unique_exceptions(self) -> int:
        return len(set(self.exception_types))

    def most_common_exception(self) -> Optional[str]:
        if not self.exception_types:
            return None
        return max(set(self.exception_types), key=self.exception_types.count)

    def __str__(self) -> str:
        mc = self.most_common_exception() or "none"
        return (
            f"Window[{self.start_index}:{self.end_index}] "
            f"traces={self.count} unique_exceptions={self.unique_exceptions} "
            f"most_common={mc}"
        )


@dataclass
class WindowReport:
    windows: List[WindowStats]
    window_size: int
    step: int

    @property
    def count(self) -> int:
        return len(self.windows)

    def summary_line(self) -> str:
        return (
            f"WindowReport: {self.count} windows "
            f"(size={self.window_size}, step={self.step})"
        )


def build_windows(
    traces: List[StackTrace],
    window_size: int = 5,
    step: int = 1,
) -> WindowReport:
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if step < 1:
        raise ValueError("step must be >= 1")

    windows: List[WindowStats] = []
    i = 0
    while i < len(traces):
        chunk = traces[i : i + window_size]
        exc_types = [t.exception_type for t in chunk if t.exception_type]
        ws = WindowStats(
            start_index=i,
            end_index=i + len(chunk) - 1,
            traces=chunk,
            exception_types=exc_types,
        )
        windows.append(ws)
        i += step

    return WindowReport(windows=windows, window_size=window_size, step=step)
