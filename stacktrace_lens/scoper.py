"""Scope analysis: identify which frames belong to user code, tests, or third-party libs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace

_TEST_PATTERNS = re.compile(r"(test_|_test\.py|/tests/|\\tests\\)")
_STDLIB_PREFIXES = ("/usr/lib/python", "/usr/local/lib/python", "<frozen ", "<string>")
_SITE_PACKAGES = re.compile(r"site-packages|dist-packages")


class Scope:
    USER = "user"
    TEST = "test"
    STDLIB = "stdlib"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


@dataclass
class ScopedFrame:
    frame: Frame
    scope: str

    def __str__(self) -> str:
        return f"[{self.scope}] {self.frame.filename}:{self.frame.lineno}"


@dataclass
class ScopeReport:
    frames: List[ScopedFrame] = field(default_factory=list)

    @property
    def user_frames(self) -> List[ScopedFrame]:
        return [f for f in self.frames if f.scope == Scope.USER]

    @property
    def test_frames(self) -> List[ScopedFrame]:
        return [f for f in self.frames if f.scope == Scope.TEST]

    @property
    def stdlib_frames(self) -> List[ScopedFrame]:
        return [f for f in self.frames if f.scope == Scope.STDLIB]

    @property
    def third_party_frames(self) -> List[ScopedFrame]:
        return [f for f in self.frames if f.scope == Scope.THIRD_PARTY]

    def summary_line(self) -> str:
        return (
            f"user={len(self.user_frames)} test={len(self.test_frames)} "
            f"stdlib={len(self.stdlib_frames)} third_party={len(self.third_party_frames)}"
        )


def _classify(filename: Optional[str]) -> str:
    if not filename:
        return Scope.UNKNOWN
    if _TEST_PATTERNS.search(filename):
        return Scope.TEST
    if any(filename.startswith(p) for p in _STDLIB_PREFIXES):
        return Scope.STDLIB
    if _SITE_PACKAGES.search(filename):
        return Scope.THIRD_PARTY
    return Scope.USER


def scope_trace(trace: StackTrace) -> ScopeReport:
    """Classify every frame in *trace* by its scope."""
    report = ScopeReport()
    for frame in trace.frames:
        scope = _classify(frame.filename)
        report.frames.append(ScopedFrame(frame=frame, scope=scope))
    return report


def format_scope_report(report: ScopeReport, *, colour: bool = True) -> str:
    lines: List[str] = [report.summary_line()]
    for sf in report.frames:
        lines.append(f"  {sf}")
    return "\n".join(lines)
