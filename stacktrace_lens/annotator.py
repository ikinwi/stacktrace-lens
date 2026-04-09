"""Annotate stack frames with source code snippets."""
from __future__ import annotations

import linecache
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class AnnotationOptions:
    context_lines: int = 3
    show_line_numbers: bool = True
    highlight_error_line: bool = True


@dataclass
class AnnotatedLine:
    lineno: int
    content: str
    is_error_line: bool = False


@dataclass
class AnnotatedFrame:
    frame: Frame
    lines: List[AnnotatedLine] = field(default_factory=list)
    source_available: bool = False


def _fetch_lines(
    filename: str,
    error_lineno: int,
    context: int,
) -> Optional[List[AnnotatedLine]]:
    """Return surrounding source lines for *filename* around *error_lineno*."""
    start = max(1, error_lineno - context)
    end = error_lineno + context

    result: List[AnnotatedLine] = []
    for lineno in range(start, end + 1):
        raw = linecache.getline(filename, lineno)
        if not raw and lineno <= error_lineno:
            return None
        content = raw.rstrip("\n") if raw else ""
        result.append(
            AnnotatedLine(
                lineno=lineno,
                content=content,
                is_error_line=(lineno == error_lineno),
            )
        )
    return result or None


def annotate_frame(frame: Frame, options: AnnotationOptions) -> AnnotatedFrame:
    """Attach source context to a single *frame*."""
    lines = _fetch_lines(frame.filename, frame.lineno, options.context_lines)
    if lines is None:
        return AnnotatedFrame(frame=frame, lines=[], source_available=False)
    return AnnotatedFrame(frame=frame, lines=lines, source_available=True)


def annotate_trace(
    trace: StackTrace, options: Optional[AnnotationOptions] = None
) -> List[AnnotatedFrame]:
    """Return annotated frames for every frame in *trace*."""
    opts = options or AnnotationOptions()
    return [annotate_frame(f, opts) for f in trace.frames]
