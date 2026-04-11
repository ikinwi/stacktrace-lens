"""Enriches stack trace frames with additional metadata.

Adds line-level context such as local variable hints, call depth,
and whether a frame belongs to the user's project or a third-party library.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class EnrichedFrame:
    """A frame decorated with extra metadata."""

    frame: Frame
    depth: int
    is_third_party: bool
    is_stdlib: bool
    call_chain_position: str  # 'root' | 'middle' | 'leaf'
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        marker = "[3p]" if self.is_third_party else "[usr]"
        return f"{self.depth:>3}  {marker}  {self.frame.filename}:{self.frame.lineno}  {self.frame.function}"


@dataclass
class EnrichReport:
    """Result of enriching an entire stack trace."""

    original: StackTrace
    frames: List[EnrichedFrame]

    @property
    def user_frames(self) -> List[EnrichedFrame]:
        return [f for f in self.frames if not f.is_third_party and not f.is_stdlib]

    @property
    def third_party_frames(self) -> List[EnrichedFrame]:
        return [f for f in self.frames if f.is_third_party]


_STDLIB_PREFIXES = (
    "<frozen ",
    "<string>",
    "/usr/lib/python",
    "/usr/local/lib/python",
)

_THIRD_PARTY_MARKERS = (
    "site-packages",
    "dist-packages",
)


def _is_stdlib(filename: str) -> bool:
    return any(filename.startswith(p) for p in _STDLIB_PREFIXES)


def _is_third_party(filename: str) -> bool:
    return any(m in filename for m in _THIRD_PARTY_MARKERS)


def _position_label(index: int, total: int) -> str:
    if total == 1:
        return "root"
    if index == 0:
        return "root"
    if index == total - 1:
        return "leaf"
    return "middle"


def enrich_trace(trace: StackTrace) -> EnrichReport:
    """Enrich every frame in *trace* with metadata."""
    total = len(trace.frames)
    enriched: List[EnrichedFrame] = []
    for depth, frame in enumerate(trace.frames):
        filename = frame.filename or ""
        stdlib = _is_stdlib(filename)
        third_party = (not stdlib) and _is_third_party(filename)
        tags: List[str] = []
        if stdlib:
            tags.append("stdlib")
        if third_party:
            tags.append("third-party")
        enriched.append(
            EnrichedFrame(
                frame=frame,
                depth=depth,
                is_third_party=third_party,
                is_stdlib=stdlib,
                call_chain_position=_position_label(depth, total),
                tags=tags,
            )
        )
    return EnrichReport(original=trace, frames=enriched)


def format_enrich_report(report: EnrichReport, *, colour: bool = True) -> str:
    """Return a human-readable summary of the enriched report."""
    lines: List[str] = []
    reset = "\033[0m" if colour else ""
    cyan = "\033[36m" if colour else ""
    yellow = "\033[33m" if colour else ""
    green = "\033[32m" if colour else ""

    lines.append(f"{cyan}Enriched Stack Trace{reset}")
    lines.append(f"  exception : {report.original.exception_type}")
    lines.append(f"  frames    : {len(report.frames)}")
    lines.append(f"  user      : {len(report.user_frames)}")
    lines.append(f"  3rd-party : {len(report.third_party_frames)}")
    lines.append("")
    for ef in report.frames:
        colour_code = yellow if ef.is_third_party else (reset if ef.is_stdlib else green)
        tag_str = ",".join(ef.tags) if ef.tags else "user"
        lines.append(
            f"  {colour_code}{ef.depth:>3}  [{tag_str:<11}]  "
            f"{ef.frame.filename}:{ef.frame.lineno}  {ef.frame.function}{reset}"
        )
    return "\n".join(lines)
