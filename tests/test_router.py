"""Tests for stacktrace_lens.router."""
from __future__ import annotations

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.router import (
    RouteResult,
    RouteRule,
    Router,
    route_traces,
)


def _frame(filename: str = "app.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(filename=filename, function=function, lineno=lineno)


def _trace(exc_type: str = "ValueError", msg: str = "bad value") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=msg,
        frames=[_frame()],
    )


def test_route_result_routed_false_by_default():
    t = _trace()
    r = RouteResult(trace=t)
    assert r.routed is False


def test_route_result_str_no_match():
    t = _trace()
    r = RouteResult(trace=t)
    assert "No route" in str(r)


def test_route_result_str_matched():
    t = _trace()
    r = RouteResult(trace=t, matched_rules=["alerts"], routed=True)
    assert "alerts" in str(r)


def test_rule_matches_exception_pattern():
    rule = RouteRule(name="ve", exception_pattern="ValueError")
    assert rule.matches(_trace("ValueError")) is True


def test_rule_no_match_wrong_exception():
    rule = RouteRule(name="te", exception_pattern="TypeError")
    assert rule.matches(_trace("ValueError")) is False


def test_rule_matches_file_pattern():
    rule = RouteRule(name="app", file_pattern=r"app\.py")
    assert rule.matches(_trace()) is True


def test_rule_no_match_wrong_file():
    rule = RouteRule(name="db", file_pattern=r"db\.py")
    assert rule.matches(_trace()) is False


def test_rule_both_patterns_must_match():
    rule = RouteRule(name="combo", exception_pattern="ValueError", file_pattern=r"db\.py")
    assert rule.matches(_trace()) is False


def test_router_returns_route_result():
    router = Router()
    router.add_rule(RouteRule(name="r1", exception_pattern="ValueError"))
    result = router.route(_trace())
    assert isinstance(result, RouteResult)


def test_router_matched_rule_name():
    router = Router()
    router.add_rule(RouteRule(name="critical", exception_pattern="ValueError"))
    result = router.route(_trace())
    assert "critical" in result.matched_rules


def test_router_no_match_produces_unrouted():
    router = Router()
    router.add_rule(RouteRule(name="r1", exception_pattern="TypeError"))
    result = router.route(_trace("ValueError"))
    assert result.routed is False


def test_router_multiple_rules_all_matching_captured():
    router = Router()
    router.add_rule(RouteRule(name="a", exception_pattern="ValueError"))
    router.add_rule(RouteRule(name="b", file_pattern=r"app\.py"))
    result = router.route(_trace())
    assert "a" in result.matched_rules
    assert "b" in result.matched_rules


def test_route_traces_returns_list():
    traces = [_trace(), _trace("TypeError")]
    rules = [RouteRule(name="ve", exception_pattern="ValueError")]
    results = route_traces(traces, rules)
    assert isinstance(results, list)
    assert len(results) == 2


def test_route_traces_handler_called(monkeypatch):
    called = []
    rule = RouteRule(name="h", exception_pattern="ValueError", handler=lambda t: called.append(t))
    route_traces([_trace()], [rule])
    assert len(called) == 1
