"""Rich renderer for ValidationReport objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from stacktrace_lens.validator import ValidationReport, ValidationViolation


@dataclass
class ValidatorRenderer:
    colour: bool = True

    # ------------------------------------------------------------------ colours
    def _c(self, code: str, text: str) -> str:
        if not self.colour:
            return text
        return f"{code}{text}\033[0m"

    def _red(self, t: str) -> str:
        return self._c("\033[31m", t)

    def _green(self, t: str) -> str:
        return self._c("\033[32m", t)

    def _yellow(self, t: str) -> str:
        return self._c("\033[33m", t)

    def _bold(self, t: str) -> str:
        return self._c("\033[1m", t)

    # ----------------------------------------------------------------- rendering
    def _render_header(self, report: ValidationReport) -> str:
        status = self._green("PASS") if report.is_valid else self._red("FAIL")
        exc = self._bold(report.trace.exception_type)
        return f"[{status}] {exc}: {report.trace.exception_message}"

    def _render_violation(self, v: ValidationViolation) -> str:
        rule = self._yellow(v.rule)
        return f"  ✗ {rule}: {v.message}"

    def render(self, report: ValidationReport) -> str:
        lines: List[str] = [self._render_header(report)]
        if report.is_valid:
            lines.append(self._green("  No violations found."))
        else:
            for v in report.violations:
                lines.append(self._render_violation(v))
            lines.append(self._red(f"  Total: {report.violation_count} violation(s)"))
        return "\n".join(lines)

    def render_all(self, reports: List[ValidationReport]) -> str:
        if not reports:
            return self._yellow("No reports to display.")
        sections = [self.render(r) for r in reports]
        sep = "\n" + "-" * 60 + "\n"
        return sep.join(sections)
