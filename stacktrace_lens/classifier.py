"""Classify stack traces into broad categories based on exception type and frame content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from stacktrace_lens.parser import StackTrace

# Map exception type substrings to category labels
_CATEGORY_MAP: list[tuple[str, str]] = [
    ("ImportError", "dependency"),
    ("ModuleNotFoundError", "dependency"),
    ("AttributeError", "attribute"),
    ("TypeError", "type"),
    ("ValueError", "value"),
    ("KeyError", "key"),
    ("IndexError", "index"),
    ("ZeroDivisionError", "arithmetic"),
    ("ArithmeticError", "arithmetic"),
    ("OSError", "io"),
    ("IOError", "io"),
    ("FileNotFoundError", "io"),
    ("PermissionError", "io"),
    ("TimeoutError", "network"),
    ("ConnectionError", "network"),
    ("RuntimeError", "runtime"),
    ("RecursionError", "runtime"),
    ("MemoryError", "resource"),
    ("OverflowError", "resource"),
    ("AssertionError", "assertion"),
    ("NotImplementedError", "not_implemented"),
    ("StopIteration", "control_flow"),
    ("GeneratorExit", "control_flow"),
]


@dataclass
class ClassificationResult:
    exception_type: str
    category: str
    confidence: float  # 0.0 – 1.0
    note: Optional[str] = None


def _category_for_exception(exc_type: str) -> tuple[str, float]:
    """Return (category, confidence) for the given exception type string."""
    for pattern, category in _CATEGORY_MAP:
        if pattern in exc_type:
            # Exact match scores higher than substring match
            confidence = 1.0 if exc_type == pattern else 0.85
            return category, confidence
    return "unknown", 0.5


def classify_trace(trace: StackTrace) -> ClassificationResult:
    """Classify a StackTrace and return a ClassificationResult."""
    exc_type = trace.exception_type or ""
    category, confidence = _category_for_exception(exc_type)

    note: Optional[str] = None
    if category == "dependency":
        note = "Check that all required packages are installed and importable."
    elif category == "io":
        note = "Verify file paths, permissions, and that resources exist."
    elif category == "network":
        note = "Inspect network connectivity and timeout settings."
    elif category == "runtime" and "RecursionError" in exc_type:
        note = "Consider increasing recursion limit or refactoring to iteration."

    return ClassificationResult(
        exception_type=exc_type,
        category=category,
        confidence=confidence,
        note=note,
    )


def format_classification(result: ClassificationResult) -> str:
    """Render a ClassificationResult as a human-readable string."""
    lines = [
        f"Category   : {result.category}",
        f"Exception  : {result.exception_type}",
        f"Confidence : {result.confidence:.0%}",
    ]
    if result.note:
        lines.append(f"Note       : {result.note}")
    return "\n".join(lines)
