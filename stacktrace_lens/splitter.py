from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import StackTrace, Frame


@dataclass
class SplitReport:
    traces: List[StackTrace] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.traces)

    @property
    def is_chained(self) -> bool:
        return len(self.traces) > 1


_CHAIN_MARKERS = ("During handling of the above exception", "The above exception was")
_CAUSED_BY = "Caused by"


def _split_raw(text: str) -> List[str]:
    """Split raw stacktrace text on chaining markers."""
    import re

    pattern = "|".join(
        re.escape(m) for m in _CHAIN_MARKERS
    ) + f"|{re.escape(_CAUSED_BY)}"
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]


def split_trace(text: str) -> SplitReport:
    """Parse and split a (possibly chained) exception text into multiple StackTrace objects."""
    from stacktrace_lens.parser import parse_stacktrace

    raw_parts = _split_raw(text)
    traces: List[StackTrace] = []
    for part in raw_parts:
        try:
            trace = parse_stacktrace(part)
            traces.append(trace)
        except Exception:
            pass

    if not traces:
        # Fallback: try parsing the whole text as one trace
        try:
            trace = parse_stacktrace(text)
            traces.append(trace)
        except Exception:
            pass

    return SplitReport(traces=traces)
