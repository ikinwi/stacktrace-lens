"""Route stack traces to named destinations based on exception type or frame patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class RouteRule:
    name: str
    exception_pattern: Optional[str] = None
    file_pattern: Optional[str] = None
    handler: Optional[Callable[[StackTrace], None]] = None

    def matches(self, trace: StackTrace) -> bool:
        if self.exception_pattern:
            if not re.search(self.exception_pattern, trace.exception_type or "", re.IGNORECASE):
                return False
        if self.file_pattern:
            matched = any(
                re.search(self.file_pattern, f.filename or "", re.IGNORECASE)
                for f in trace.frames
            )
            if not matched:
                return False
        return True


@dataclass
class RouteResult:
    trace: StackTrace
    matched_rules: List[str] = field(default_factory=list)
    routed: bool = False

    def __str__(self) -> str:
        if self.routed:
            return f"Routed to: {', '.join(self.matched_rules)}"
        return "No route matched"


class Router:
    def __init__(self) -> None:
        self._rules: List[RouteRule] = []

    def add_rule(self, rule: RouteRule) -> None:
        self._rules.append(rule)

    def route(self, trace: StackTrace) -> RouteResult:
        result = RouteResult(trace=trace)
        for rule in self._rules:
            if rule.matches(trace):
                result.matched_rules.append(rule.name)
                result.routed = True
                if rule.handler:
                    rule.handler(trace)
        return result


def route_traces(traces: List[StackTrace], rules: List[RouteRule]) -> List[RouteResult]:
    router = Router()
    for rule in rules:
        router.add_rule(rule)
    return [router.route(t) for t in traces]
