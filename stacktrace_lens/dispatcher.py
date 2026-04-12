"""Route a StackTrace to the most relevant command handler based on its properties."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from stacktrace_lens.parser import StackTrace


# Handler signature: (StackTrace) -> str
Handler = Callable[[StackTrace], str]


@dataclass
class DispatchRule:
    """A named rule that matches a trace and invokes a handler."""
    name: str
    predicate: Callable[[StackTrace], bool]
    handler: Handler
    priority: int = 0  # higher wins when multiple rules match


@dataclass
class DispatchResult:
    rule_name: str
    output: str
    matched: bool = True

    def __str__(self) -> str:  # pragma: no cover
        return self.output


@dataclass
class Dispatcher:
    rules: List[DispatchRule] = field(default_factory=list)
    fallback: Optional[Handler] = None

    def register(self, rule: DispatchRule) -> None:
        """Add a rule; rules are evaluated in descending priority order."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def dispatch(self, trace: StackTrace) -> DispatchResult:
        """Find the first matching rule and invoke its handler."""
        for rule in self.rules:
            if rule.predicate(trace):
                return DispatchResult(
                    rule_name=rule.name,
                    output=rule.handler(trace),
                    matched=True,
                )
        if self.fallback is not None:
            return DispatchResult(
                rule_name="fallback",
                output=self.fallback(trace),
                matched=False,
            )
        return DispatchResult(rule_name="none", output="", matched=False)


def build_default_dispatcher() -> Dispatcher:
    """Return a Dispatcher pre-loaded with common routing rules."""
    from stacktrace_lens.severity import score_trace
    from stacktrace_lens.suggestions import get_suggestion

    def _high_severity(trace: StackTrace) -> bool:
        result = score_trace(trace)
        return result.score >= 7

    def _has_suggestion(trace: StackTrace) -> bool:
        return get_suggestion(trace.exception_type) is not None

    def _render_high(trace: StackTrace) -> str:
        from stacktrace_lens.severity import format_severity
        return format_severity(score_trace(trace))

    def _render_suggestion(trace: StackTrace) -> str:
        suggestion = get_suggestion(trace.exception_type) or ""
        return f"[{trace.exception_type}] {suggestion}"

    d = Dispatcher(fallback=lambda t: f"{t.exception_type}: {t.exception_message}")
    d.register(DispatchRule("high_severity", _high_severity, _render_high, priority=10))
    d.register(DispatchRule("has_suggestion", _has_suggestion, _render_suggestion, priority=5))
    return d
