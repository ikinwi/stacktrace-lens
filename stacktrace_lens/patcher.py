"""Patch frames in a stack trace by applying line-number or filename corrections."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class PatchRule:
    """A single patch rule that matches a frame and applies corrections."""
    filename_contains: Optional[str] = None
    function_name: Optional[str] = None
    replace_filename: Optional[str] = None
    replace_function: Optional[str] = None
    line_offset: int = 0


@dataclass
class PatchedFrame:
    original: Frame
    patched: Frame
    was_patched: bool

    def __str__(self) -> str:
        if self.was_patched:
            return (
                f"{self.patched.filename}:{self.patched.lineno} "
                f"in {self.patched.function_name} [patched]"
            )
        return f"{self.patched.filename}:{self.patched.lineno} in {self.patched.function_name}"


@dataclass
class PatchReport:
    original_trace: StackTrace
    patched_frames: List[PatchedFrame] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.patched_frames)

    @property
    def patched_count(self) -> int:
        return sum(1 for f in self.patched_frames if f.was_patched)

    def summary_line(self) -> str:
        return (
            f"{self.patched_count} of {self.count} frame(s) patched "
            f"({self.original_trace.exception_type})"
        )

    def as_trace(self) -> StackTrace:
        frames = [pf.patched for pf in self.patched_frames]
        return StackTrace(
            exception_type=self.original_trace.exception_type,
            exception_message=self.original_trace.exception_message,
            frames=frames,
        )


def _matches_rule(frame: Frame, rule: PatchRule) -> bool:
    if rule.filename_contains and rule.filename_contains not in frame.filename:
        return False
    if rule.function_name and rule.function_name != frame.function_name:
        return False
    return True


def _apply_rule(frame: Frame, rule: PatchRule) -> Frame:
    return Frame(
        filename=rule.replace_filename if rule.replace_filename is not None else frame.filename,
        lineno=frame.lineno + rule.line_offset,
        function_name=rule.replace_function if rule.replace_function is not None else frame.function_name,
        source_line=frame.source_line,
    )


def patch_trace(trace: StackTrace, rules: List[PatchRule]) -> PatchReport:
    report = PatchReport(original_trace=trace)
    for frame in trace.frames:
        patched = frame
        was_patched = False
        for rule in rules:
            if _matches_rule(frame, rule):
                patched = _apply_rule(frame, rule)
                was_patched = True
                break
        report.patched_frames.append(PatchedFrame(original=frame, patched=patched, was_patched=was_patched))
    return report
