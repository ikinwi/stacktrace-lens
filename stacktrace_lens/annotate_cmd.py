"""CLI helper: annotate a stack trace with inline source context."""
from __future__ import annotations

import sys
from typing import List, Optional

from stacktrace_lens.annotator import AnnotationOptions, annotate_trace
from stacktrace_lens.annotation_renderer import AnnotationRenderer
from stacktrace_lens.formatter import FormatOptions
from stacktrace_lens.parser import StackTrace, parse_stacktrace


def annotate_command(
    raw: str,
    context_lines: int = 3,
    colour: bool = True,
    out=None,
) -> int:
    """Parse *raw* trace text, annotate it, write to *out*, return exit code."""
    if out is None:
        out = sys.stdout

    trace: Optional[StackTrace] = parse_stacktrace(raw)
    if trace is None:
        out.write("error: could not parse stack trace\n")
        return 1

    ann_opts = AnnotationOptions(context_lines=context_lines)
    fmt_opts = FormatOptions(colour=colour)
    renderer = AnnotationRenderer(format_opts=fmt_opts, annotation_opts=ann_opts)

    annotated = annotate_trace(trace, ann_opts)

    header = f"Traceback ({len(trace.frames)} frame(s)):"
    out.write(header + "\n")
    out.write(renderer.render_all(annotated) + "\n")
    out.write(f"{trace.exception_type}: {trace.exception_message}\n")
    return 0
