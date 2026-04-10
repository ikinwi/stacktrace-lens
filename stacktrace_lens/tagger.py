"""Tag stack traces with user-defined or auto-generated labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from stacktrace_lens.parser import StackTrace

# Built-in auto-tag rules: (exception_type_substring, tag)
_AUTO_RULES: List[tuple[str, str]] = [
    ("ImportError", "import"),
    ("ModuleNotFoundError", "import"),
    ("AttributeError", "attribute"),
    ("TypeError", "type"),
    ("ValueError", "value"),
    ("KeyError", "key"),
    ("IndexError", "index"),
    ("ZeroDivisionError", "arithmetic"),
    ("FileNotFoundError", "io"),
    ("PermissionError", "io"),
    ("OSError", "io"),
    ("RuntimeError", "runtime"),
    ("RecursionError", "runtime"),
    ("MemoryError", "resource"),
    ("TimeoutError", "resource"),
    ("NotImplementedError", "not-implemented"),
    ("AssertionError", "assertion"),
]


@dataclass
class TagResult:
    trace: StackTrace
    tags: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


def auto_tag(trace: StackTrace) -> List[str]:
    """Return automatically derived tags based on the exception type."""
    exc = trace.exception_type or ""
    tags: List[str] = []
    for fragment, tag in _AUTO_RULES:
        if fragment in exc and tag not in tags:
            tags.append(tag)
    if not tags:
        tags.append("unknown")
    return tags


def tag_trace(
    trace: StackTrace,
    extra_tags: Optional[List[str]] = None,
    note: Optional[str] = None,
    include_auto: bool = True,
) -> TagResult:
    """Tag a trace, optionally combining auto-tags with caller-supplied ones."""
    tags: List[str] = []
    if include_auto:
        tags.extend(auto_tag(trace))
    if extra_tags:
        for t in extra_tags:
            if t not in tags:
                tags.append(t)
    return TagResult(trace=trace, tags=tags, note=note)


def format_tags(result: TagResult, *, colour: bool = False) -> str:
    """Return a human-readable string representation of the tag result."""
    exc_type = result.trace.exception_type or "<unknown>"
    tag_str = ", ".join(f"[{t}]" for t in result.tags)
    note_str = f"  # {result.note}" if result.note else ""
    if colour:
        tag_str = f"\033[36m{tag_str}\033[0m"
        exc_type = f"\033[31m{exc_type}\033[0m"
    return f"{exc_type}  {tag_str}{note_str}"
