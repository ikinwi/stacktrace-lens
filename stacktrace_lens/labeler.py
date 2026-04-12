"""Assign human-readable labels to stack traces based on heuristics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace

# Maps exception type substrings to short labels
_EXCEPTION_LABELS: dict[str, str] = {
    "ZeroDivisionError": "math-error",
    "ImportError": "import-failure",
    "ModuleNotFoundError": "import-failure",
    "AttributeError": "attribute-miss",
    "KeyError": "missing-key",
    "IndexError": "out-of-bounds",
    "TypeError": "type-mismatch",
    "ValueError": "bad-value",
    "FileNotFoundError": "io-error",
    "PermissionError": "io-error",
    "OSError": "io-error",
    "RuntimeError": "runtime-fault",
    "RecursionError": "recursion",
    "MemoryError": "resource-exhausted",
    "TimeoutError": "timeout",
    "NotImplementedError": "not-implemented",
    "AssertionError": "assertion-failed",
}

_DEEP_THRESHOLD = 10  # frames
_SHALLOW_THRESHOLD = 2


@dataclass
class LabelResult:
    exception_label: Optional[str]
    depth_label: str
    custom_labels: List[str] = field(default_factory=list)

    @property
    def all_labels(self) -> List[str]:
        labels: List[str] = []
        if self.exception_label:
            labels.append(self.exception_label)
        labels.append(self.depth_label)
        labels.extend(self.custom_labels)
        return labels

    def __str__(self) -> str:  # pragma: no cover
        return "[" + ", ".join(self.all_labels) + "]"


def _exception_label(exc_type: str) -> Optional[str]:
    for key, label in _EXCEPTION_LABELS.items():
        if key in exc_type:
            return label
    return None


def _depth_label(frame_count: int) -> str:
    if frame_count >= _DEEP_THRESHOLD:
        return "deep-trace"
    if frame_count <= _SHALLOW_THRESHOLD:
        return "shallow-trace"
    return "normal-depth"


def label_trace(trace: StackTrace, extra: Optional[List[str]] = None) -> LabelResult:
    """Derive labels for *trace* and return a :class:`LabelResult`."""
    exc_lbl = _exception_label(trace.exception_type)
    depth_lbl = _depth_label(len(trace.frames))
    return LabelResult(
        exception_label=exc_lbl,
        depth_label=depth_lbl,
        custom_labels=list(extra) if extra else [],
    )


def format_labels(result: LabelResult) -> str:
    """Return a plain-text representation of *result*."""
    lines = ["Labels:"]
    if result.exception_label:
        lines.append(f"  exception : {result.exception_label}")
    lines.append(f"  depth     : {result.depth_label}")
    if result.custom_labels:
        lines.append("  custom    : " + ", ".join(result.custom_labels))
    return "\n".join(lines)
