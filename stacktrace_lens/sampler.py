"""sampler.py – randomly or systematically sample traces from a collection."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class SampleOptions:
    n: Optional[int] = None          # absolute number of traces to keep
    fraction: Optional[float] = None  # fraction in (0, 1]
    seed: Optional[int] = None        # for reproducibility
    every_nth: Optional[int] = None   # keep every N-th trace (1-based)


@dataclass
class SampleReport:
    original_count: int
    sampled: List[StackTrace] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.sampled)

    def summary_line(self) -> str:
        return (
            f"Sampled {self.count} / {self.original_count} traces "
            f"({100 * self.count // max(self.original_count, 1)}%)"
        )


def sample_traces(traces: List[StackTrace], options: Optional[SampleOptions] = None) -> SampleReport:
    """Return a SampleReport containing the chosen subset of *traces*."""
    if options is None:
        options = SampleOptions()

    original_count = len(traces)

    if not traces:
        return SampleReport(original_count=0, sampled=[])

    # every_nth takes priority over random sampling
    if options.every_nth is not None:
        n = max(1, options.every_nth)
        sampled = [t for i, t in enumerate(traces, start=1) if i % n == 0]
        return SampleReport(original_count=original_count, sampled=sampled)

    rng = random.Random(options.seed)
    pool = list(traces)

    if options.fraction is not None:
        fraction = max(0.0, min(1.0, options.fraction))
        k = max(1, round(len(pool) * fraction))
        sampled = rng.sample(pool, min(k, len(pool)))
    elif options.n is not None:
        sampled = rng.sample(pool, min(options.n, len(pool)))
    else:
        sampled = pool  # no filtering

    return SampleReport(original_count=original_count, sampled=sampled)


def format_sample(report: SampleReport) -> str:
    lines = [report.summary_line()]
    for i, trace in enumerate(report.sampled, start=1):
        lines.append(f"  [{i}] {trace.exception_type}: {trace.exception_message}")
    return "\n".join(lines)
