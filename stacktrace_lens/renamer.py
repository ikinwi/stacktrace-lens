"""Rename files and functions in stack trace frames using substitution rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class RenameRule:
    """A single find-and-replace rule applied to frame fields."""
    find: str
    replace: str
    target: str = "filename"  # 'filename' | 'function' | 'both'


@dataclass
class RenamedFrame:
    original: Frame
    frame: Frame
    renamed: bool

    def __str__(self) -> str:
        tag = " [renamed]" if self.renamed else ""
        return f"  File \"{self.frame.filename}\", line {self.frame.lineno}, in {self.frame.function}{tag}"


@dataclass
class RenameReport:
    frames: List[RenamedFrame] = field(default_factory=list)
    rules_applied: int = 0

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def renamed_count(self) -> int:
        return sum(1 for f in self.frames if f.renamed)

    def summary_line(self) -> str:
        return (
            f"{self.renamed_count}/{self.count} frame(s) renamed "
            f"using {self.rules_applied} rule(s)"
        )


def _apply_rules(value: str, rules: List[RenameRule], target_field: str) -> str:
    for rule in rules:
        if rule.target in (target_field, "both"):
            value = value.replace(rule.find, rule.replace)
    return value


def rename_frames(
    trace: StackTrace,
    rules: Optional[List[RenameRule]] = None,
) -> RenameReport:
    """Apply rename rules to every frame in *trace*."""
    rules = rules or []
    report = RenameReport(rules_applied=len(rules))

    for original in trace.frames:
        new_filename = _apply_rules(original.filename, rules, "filename")
        new_function = _apply_rules(original.function, rules, "function")
        changed = new_filename != original.filename or new_function != original.function

        new_frame = Frame(
            filename=new_filename,
            lineno=original.lineno,
            function=new_function,
            source=original.source,
        )
        report.frames.append(RenamedFrame(original=original, frame=new_frame, renamed=changed))

    return report
