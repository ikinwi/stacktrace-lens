"""Inspector: extract key diagnostic fields from a StackTrace for quick triage."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import StackTrace, Frame


@dataclass
class InspectionResult:
    exception_type: str
    exception_message: str
    depth: int
    root_file: Optional[str]
    root_function: Optional[str]
    tip_file: Optional[str]
    tip_function: Optional[str]
    unique_files: List[str] = field(default_factory=list)
    unique_functions: List[str] = field(default_factory=list)
    has_recursion: bool = False

    def summary_line(self) -> str:
        return (
            f"{self.exception_type}: {self.exception_message} "
            f"[depth={self.depth}, files={len(self.unique_files)}]"
        )


def _detect_recursion(frames: List[Frame]) -> bool:
    """Return True if any (file, function) pair appears more than once."""
    seen: set = set()
    for f in frames:
        key = (f.filename, f.function)
        if key in seen:
            return True
        seen.add(key)
    return False


def inspect_trace(trace: StackTrace) -> InspectionResult:
    """Derive an InspectionResult from *trace*."""
    frames = trace.frames

    root: Optional[Frame] = frames[0] if frames else None
    tip: Optional[Frame] = frames[-1] if frames else None

    seen_files: dict = {}
    seen_funcs: dict = {}
    for fr in frames:
        seen_files.setdefault(fr.filename, None)
        seen_funcs.setdefault(fr.function, None)

    return InspectionResult(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        depth=len(frames),
        root_file=root.filename if root else None,
        root_function=root.function if root else None,
        tip_file=tip.filename if tip else None,
        tip_function=tip.function if tip else None,
        unique_files=list(seen_files.keys()),
        unique_functions=list(seen_funcs.keys()),
        has_recursion=_detect_recursion(frames),
    )


def format_inspection(result: InspectionResult, *, colour: bool = True) -> str:
    """Render an InspectionResult as a human-readable string."""
    reset = "\033[0m" if colour else ""
    bold = "\033[1m" if colour else ""
    cyan = "\033[36m" if colour else ""
    yellow = "\033[33m" if colour else ""

    lines = [
        f"{bold}Exception :{reset} {cyan}{result.exception_type}{reset}",
        f"{bold}Message   :{reset} {result.exception_message}",
        f"{bold}Depth     :{reset} {result.depth} frame(s)",
        f"{bold}Root      :{reset} {result.root_file} in {result.root_function}",
        f"{bold}Tip       :{reset} {result.tip_file} in {result.tip_function}",
        f"{bold}Files     :{reset} {', '.join(result.unique_files) or '—'}",
        f"{bold}Functions :{reset} {', '.join(result.unique_functions) or '—'}",
    ]
    if result.has_recursion:
        lines.append(f"{yellow}⚠ Possible recursion detected{reset}")
    return "\n".join(lines)
