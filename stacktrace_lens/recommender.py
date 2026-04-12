"""Recommender: suggest actionable fixes based on stack trace analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace
from stacktrace_lens.enricher import EnrichedFrame, enrich_trace
from stacktrace_lens.severity import score_trace


@dataclass
class Recommendation:
    title: str
    detail: str
    priority: int  # 1 = high, 2 = medium, 3 = low

    def __str__(self) -> str:
        badge = ["[HIGH]", "[MED] ", "[LOW] "][min(self.priority - 1, 2)]
        return f"{badge} {self.title}: {self.detail}"


@dataclass
class RecommendationReport:
    exception_type: str
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.recommendations)

    def top(self) -> Optional[Recommendation]:
        if not self.recommendations:
            return None
        return min(self.recommendations, key=lambda r: r.priority)


_EXCEPTION_ADVICE: dict[str, tuple[str, str, int]] = {
    "ImportError": (
        "Check installed packages",
        "Run `pip install <package>` or verify your virtual environment is active.",
        1,
    ),
    "ModuleNotFoundError": (
        "Missing module",
        "Ensure the module is installed and the package name is correct.",
        1,
    ),
    "AttributeError": (
        "Check object type",
        "Verify the object is not None and has the expected attribute before access.",
        2,
    ),
    "KeyError": (
        "Use dict.get()",
        "Replace direct key access with dict.get(key, default) to avoid KeyError.",
        2,
    ),
    "IndexError": (
        "Guard list access",
        "Check len(list) before indexing or use try/except IndexError.",
        2,
    ),
    "TypeError": (
        "Inspect argument types",
        "Add type hints and validate inputs; consider using isinstance() checks.",
        2,
    ),
    "ValueError": (
        "Validate input values",
        "Add input validation before the failing call and provide clear error messages.",
        2,
    ),
    "RecursionError": (
        "Check for infinite recursion",
        "Add a base case or increase sys.setrecursionlimit() if depth is intentional.",
        1,
    ),
    "ZeroDivisionError": (
        "Guard division operations",
        "Check the denominator is non-zero before dividing.",
        1,
    ),
    "FileNotFoundError": (
        "Verify file paths",
        "Use pathlib.Path.exists() before opening files and check working directory.",
        1,
    ),
    "PermissionError": (
        "Check file permissions",
        "Ensure the process has read/write access to the target path.",
        2,
    ),
    "TimeoutError": (
        "Add timeout handling",
        "Wrap network/IO calls with explicit timeouts and retry logic.",
        2,
    ),
    "MemoryError": (
        "Reduce memory usage",
        "Stream large data instead of loading it all at once; profile with tracemalloc.",
        1,
    ),
}


def _depth_recommendation(trace: StackTrace) -> Optional[Recommendation]:
    depth = len(trace.frames)
    if depth >= 20:
        return Recommendation(
            title="Deep call stack detected",
            detail=f"Stack is {depth} frames deep; consider refactoring to reduce nesting.",
            priority=2,
        )
    return None


def _user_frame_recommendation(report: list[EnrichedFrame]) -> Optional[Recommendation]:
    user_frames = [f for f in report if not f.is_stdlib and not f.is_third_party]
    if not user_frames:
        return Recommendation(
            title="No user code in trace",
            detail="All frames are stdlib/third-party; the error may stem from bad arguments passed by your code.",
            priority=3,
        )
    return None


def recommend(trace: StackTrace) -> RecommendationReport:
    """Analyse *trace* and return a :class:`RecommendationReport`."""
    report = RecommendationReport(exception_type=trace.exception_type)

    # Exception-specific advice
    exc = trace.exception_type
    if exc in _EXCEPTION_ADVICE:
        title, detail, priority = _EXCEPTION_ADVICE[exc]
        report.recommendations.append(Recommendation(title=title, detail=detail, priority=priority))
    else:
        # Generic fallback
        report.recommendations.append(
            Recommendation(
                title="Review exception context",
                detail=f"No specific advice for {exc}; read the full message and inspect the innermost frame.",
                priority=3,
            )
        )

    # Depth-based recommendation
    depth_rec = _depth_recommendation(trace)
    if depth_rec:
        report.recommendations.append(depth_rec)

    # Enrich frames and add user-code recommendation
    try:
        enriched = enrich_trace(trace)
        user_rec = _user_frame_recommendation(enriched.frames)
        if user_rec:
            report.recommendations.append(user_rec)
    except Exception:  # pragma: no cover
        pass

    # High-severity extra nudge
    severity = score_trace(trace)
    if severity.score >= 8:
        report.recommendations.append(
            Recommendation(
                title="High severity — act immediately",
                detail="This trace scored high on severity. Prioritise fixing it before other issues.",
                priority=1,
            )
        )

    # Sort by priority
    report.recommendations.sort(key=lambda r: r.priority)
    return report


def format_recommendations(report: RecommendationReport, *, colour: bool = True) -> str:
    """Render *report* as a human-readable string."""
    reset = "\033[0m" if colour else ""
    bold = "\033[1m" if colour else ""
    yellow = "\033[33m" if colour else ""
    red = "\033[31m" if colour else ""
    cyan = "\033[36m" if colour else ""

    priority_colour = {1: red, 2: yellow, 3: cyan}

    lines = [f"{bold}Recommendations for {report.exception_type}{reset} ({report.count} item(s))"]
    for rec in report.recommendations:
        col = priority_colour.get(rec.priority, "")
        badge = ["HIGH", "MED", "LOW"][min(rec.priority - 1, 2)]
        lines.append(f"  {col}[{badge}]{reset} {bold}{rec.title}{reset}")
        lines.append(f"       {rec.detail}")
    return "\n".join(lines)
