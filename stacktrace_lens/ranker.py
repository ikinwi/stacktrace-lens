"""Rank stack traces by a composite score derived from severity, depth, and recurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import StackTrace
from .severity import score_trace


# Weight constants
_W_SEVERITY = 0.50
_W_DEPTH = 0.30
_W_RECURRENCE = 0.20
_MAX_DEPTH = 20  # frames beyond this are clamped


@dataclass
class RankedTrace:
    trace: StackTrace
    severity_score: float
    depth_score: float
    recurrence_score: float
    composite: float
    label: Optional[str] = None

    def __str__(self) -> str:
        tag = f"[{self.label}] " if self.label else ""
        return (
            f"{tag}{self.trace.exception_type}: composite={self.composite:.3f} "
            f"(sev={self.severity_score:.2f}, depth={self.depth_score:.2f}, "
            f"rec={self.recurrence_score:.2f})"
        )


@dataclass
class RankReport:
    entries: List[RankedTrace] = field(default_factory=list)

    @property
    def top(self) -> Optional[RankedTrace]:
        return self.entries[0] if self.entries else None

    def ranked(self) -> List[RankedTrace]:
        """Return entries sorted by composite score descending."""
        return sorted(self.entries, key=lambda e: e.composite, reverse=True)


def _normalise_depth(n_frames: int) -> float:
    """Map frame count to [0, 1]."""
    return min(n_frames / _MAX_DEPTH, 1.0)


def rank_traces(
    traces: List[StackTrace],
    recurrence_counts: Optional[dict] = None,
    labels: Optional[List[Optional[str]]] = None,
) -> RankReport:
    """Rank *traces* and return a :class:`RankReport`.

    Parameters
    ----------
    traces:
        Traces to rank.
    recurrence_counts:
        Optional mapping of ``exception_type`` -> occurrence count used to
        compute the recurrence sub-score.  When omitted every trace gets 0.
    labels:
        Optional per-trace labels aligned by index.
    """
    recurrence_counts = recurrence_counts or {}
    labels = labels or [None] * len(traces)
    max_rec = max(recurrence_counts.values(), default=1) or 1

    entries: List[RankedTrace] = []
    for trace, label in zip(traces, labels):
        sev_result = score_trace(trace)
        sev_score = sev_result.score / 10.0  # normalise to [0, 1]
        depth_score = _normalise_depth(len(trace.frames))
        raw_rec = recurrence_counts.get(trace.exception_type, 0)
        rec_score = raw_rec / max_rec
        composite = (
            _W_SEVERITY * sev_score
            + _W_DEPTH * depth_score
            + _W_RECURRENCE * rec_score
        )
        entries.append(
            RankedTrace(
                trace=trace,
                severity_score=round(sev_score, 4),
                depth_score=round(depth_score, 4),
                recurrence_score=round(rec_score, 4),
                composite=round(composite, 4),
                label=label,
            )
        )

    entries.sort(key=lambda e: e.composite, reverse=True)
    return RankReport(entries=entries)


def format_rank(report: RankReport, *, colour: bool = False) -> str:
    """Return a human-readable string for *report*."""
    if not report.entries:
        return "No traces to rank."
    lines = ["Ranked traces (highest composite first):", ""]
    for i, entry in enumerate(report.ranked(), 1):
        lines.append(f"  {i:>3}. {entry}")
    return "\n".join(lines)
