"""Validate stack traces against configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class ValidationRule:
    name: str
    description: str


@dataclass
class ValidationViolation:
    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"


@dataclass
class ValidationReport:
    trace: StackTrace
    violations: List[ValidationViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def summary_line(self) -> str:
        if self.is_valid:
            return "Trace is valid (no violations)"
        return f"{self.violation_count} violation(s) found"


@dataclass
class ValidateOptions:
    max_depth: Optional[int] = None
    require_message: bool = False
    disallow_empty_frames: bool = True
    known_exception_types: Optional[List[str]] = None


def validate_trace(trace: StackTrace, options: Optional[ValidateOptions] = None) -> ValidationReport:
    """Run validation rules against *trace* and return a report."""
    if options is None:
        options = ValidateOptions()

    violations: List[ValidationViolation] = []

    if options.max_depth is not None and len(trace.frames) > options.max_depth:
        violations.append(ValidationViolation(
            rule="max_depth",
            message=f"Frame depth {len(trace.frames)} exceeds maximum {options.max_depth}",
        ))

    if options.require_message and not (trace.exception_message or "").strip():
        violations.append(ValidationViolation(
            rule="require_message",
            message="Exception message is empty or missing",
        ))

    if options.disallow_empty_frames:
        for i, frame in enumerate(trace.frames):
            if not frame.filename.strip() or not frame.function.strip():
                violations.append(ValidationViolation(
                    rule="disallow_empty_frames",
                    message=f"Frame {i} has empty filename or function name",
                ))

    if options.known_exception_types is not None:
        if trace.exception_type not in options.known_exception_types:
            violations.append(ValidationViolation(
                rule="known_exception_types",
                message=f"Exception type '{trace.exception_type}' is not in the allowed list",
            ))

    return ValidationReport(trace=trace, violations=violations)


def format_validation(report: ValidationReport, *, colour: bool = True) -> str:
    """Render a *ValidationReport* as a human-readable string."""
    RED = "\033[31m" if colour else ""
    GREEN = "\033[32m" if colour else ""
    RESET = "\033[0m" if colour else ""

    lines = [f"Validation: {report.trace.exception_type}"]
    if report.is_valid:
        lines.append(f"{GREEN}✓ {report.summary_line()}{RESET}")
    else:
        lines.append(f"{RED}✗ {report.summary_line()}{RESET}")
        for v in report.violations:
            lines.append(f"  {RED}• {v}{RESET}")
    return "\n".join(lines)
