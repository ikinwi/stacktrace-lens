"""streaker.py – detect repeated exception streaks across a sequence of traces.

A 'streak' is a consecutive run of traces sharing the same exception type.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class Streak:
    exception_type: str
    count: int
    start_index: int
    end_index: int

    def __str__(self) -> str:
        return (
            f"{self.exception_type} x{self.count} "
            f"(traces {self.start_index}–{self.end_index})"
        )


@dataclass
class StreakReport:
    streaks: List[Streak] = field(default_factory=list)
    total_traces: int = 0

    @property
    def count(self) -> int:
        return len(self.streaks)

    @property
    def longest(self) -> Optional[Streak]:
        if not self.streaks:
            return None
        return max(self.streaks, key=lambda s: s.count)

    def summary_line(self) -> str:
        if not self.streaks:
            return "No streaks detected."
        longest = self.longest
        return (
            f"{self.count} streak(s) across {self.total_traces} trace(s); "
            f"longest: {longest.exception_type} x{longest.count}"
        )


def detect_streaks(traces: List[StackTrace], min_length: int = 2) -> StreakReport:
    """Return a StreakReport describing consecutive runs of the same exception."""
    report = StreakReport(total_traces=len(traces))
    if not traces:
        return report

    run_type = traces[0].exception_type
    run_start = 0
    run_len = 1

    def _flush(exc: str, start: int, length: int) -> None:
        if length >= min_length:
            report.streaks.append(
                Streak(
                    exception_type=exc,
                    count=length,
                    start_index=start,
                    end_index=start + length - 1,
                )
            )

    for idx in range(1, len(traces)):
        if traces[idx].exception_type == run_type:
            run_len += 1
        else:
            _flush(run_type, run_start, run_len)
            run_type = traces[idx].exception_type
            run_start = idx
            run_len = 1

    _flush(run_type, run_start, run_len)
    return report


def format_streaks(report: StreakReport) -> str:
    lines = [report.summary_line()]
    for streak in report.streaks:
        lines.append(f"  {streak}")
    return "\n".join(lines)
