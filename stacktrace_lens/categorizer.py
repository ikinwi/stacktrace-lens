"""Categorize stack traces into broad domain buckets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace

# Maps exception type substrings to domain categories
_CATEGORY_MAP = {
    "ImportError": "dependency",
    "ModuleNotFoundError": "dependency",
    "AttributeError": "runtime",
    "TypeError": "runtime",
    "ValueError": "runtime",
    "KeyError": "runtime",
    "IndexError": "runtime",
    "NameError": "runtime",
    "ZeroDivisionError": "runtime",
    "RuntimeError": "runtime",
    "NotImplementedError": "runtime",
    "OSError": "io",
    "IOError": "io",
    "FileNotFoundError": "io",
    "PermissionError": "io",
    "TimeoutError": "io",
    "ConnectionError": "network",
    "BrokenPipeError": "network",
    "MemoryError": "resource",
    "RecursionError": "resource",
    "OverflowError": "resource",
    "AssertionError": "assertion",
    "SyntaxError": "syntax",
    "IndentationError": "syntax",
}


@dataclass
class CategorizationResult:
    exception_type: str
    category: str
    confidence: float  # 0.0 – 1.0
    notes: List[str] = field(default_factory=list)

    def summary_line(self) -> str:
        return (
            f"{self.exception_type} → [{self.category}] "
            f"(confidence: {self.confidence:.0%})"
        )


def _resolve_category(exc_type: str) -> tuple[str, float]:
    """Return (category, confidence) for the given exception type string."""
    if exc_type in _CATEGORY_MAP:
        return _CATEGORY_MAP[exc_type], 1.0
    for key, cat in _CATEGORY_MAP.items():
        if key in exc_type:
            return cat, 0.7
    return "unknown", 0.0


def categorize_trace(trace: StackTrace) -> CategorizationResult:
    """Categorize *trace* by its exception type."""
    exc_type = trace.exception_type or "Unknown"
    category, confidence = _resolve_category(exc_type)
    notes: List[str] = []
    if confidence == 0.0:
        notes.append("Exception type not recognised; defaulting to 'unknown'.")
    if len(trace.frames) == 0:
        notes.append("Trace has no frames.")
    return CategorizationResult(
        exception_type=exc_type,
        category=category,
        confidence=confidence,
        notes=notes,
    )


def format_categorization(result: CategorizationResult) -> str:
    """Return a human-readable string for *result*."""
    lines = [result.summary_line()]
    for note in result.notes:
        lines.append(f"  note: {note}")
    return "\n".join(lines)
