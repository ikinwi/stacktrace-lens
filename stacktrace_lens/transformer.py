"""Transform stack trace frames by applying a series of user-defined
rename / rewrite rules to filenames, function names, and line numbers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class TransformRule:
    """A single rewrite rule applied to a Frame."""
    name: str
    apply: Callable[[Frame], Frame]


@dataclass
class TransformedFrame:
    original: Frame
    result: Frame
    rules_applied: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.result.filename}:{self.result.lineno} in {self.result.function}"


@dataclass
class TransformReport:
    original_trace: StackTrace
    frames: List[TransformedFrame] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def modified_count(self) -> int:
        return sum(1 for f in self.frames if f.rules_applied)

    def summary_line(self) -> str:
        return (
            f"{self.modified_count}/{self.count} frame(s) transformed "
            f"across {len(self._all_rules())} rule(s)"
        )

    def _all_rules(self) -> List[str]:
        seen: List[str] = []
        for tf in self.frames:
            for r in tf.rules_applied:
                if r not in seen:
                    seen.append(r)
        return seen

    def to_trace(self) -> StackTrace:
        return StackTrace(
            exception_type=self.original_trace.exception_type,
            exception_message=self.original_trace.exception_message,
            frames=[tf.result for tf in self.frames],
        )


def transform_trace(
    trace: StackTrace,
    rules: Optional[List[TransformRule]] = None,
) -> TransformReport:
    """Apply *rules* to every frame in *trace* and return a TransformReport."""
    rules = rules or []
    report = TransformReport(original_trace=trace)

    for frame in trace.frames:
        current = frame
        applied: List[str] = []
        for rule in rules:
            rewritten = rule.apply(current)
            if rewritten is not current:
                applied.append(rule.name)
                current = rewritten
        report.frames.append(
            TransformedFrame(original=frame, result=current, rules_applied=applied)
        )

    return report
