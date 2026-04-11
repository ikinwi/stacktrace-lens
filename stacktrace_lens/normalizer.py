"""Normalize stack traces for consistent comparison and storage."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class NormalizeOptions:
    """Options controlling how normalization is applied."""

    strip_cwd: bool = True
    """Replace the current working directory prefix with '<cwd>'."""

    collapse_site_packages: bool = True
    """Replace site-packages path prefix with '<site-packages>'."""

    anonymize_line_numbers: bool = False
    """Replace all line numbers with 0 (useful for fuzzy matching)."""

    lowercase_exception_type: bool = False
    """Lowercase the exception type string."""


_SITE_PKG_RE = re.compile(r".*site-packages[\\/]")


def _normalize_filename(filename: str, opts: NormalizeOptions) -> str:
    if opts.strip_cwd:
        cwd = os.getcwd()
        if filename.startswith(cwd):
            filename = "<cwd>" + filename[len(cwd):]
    if opts.collapse_site_packages:
        filename = _SITE_PKG_RE.sub("<site-packages>/", filename)
    return filename


def normalize_frame(frame: Frame, opts: NormalizeOptions) -> Frame:
    """Return a new Frame with normalized fields."""
    new_filename = _normalize_filename(frame.filename, opts)
    new_lineno = 0 if opts.anonymize_line_numbers else frame.lineno
    return Frame(
        filename=new_filename,
        lineno=new_lineno,
        function=frame.function,
        source_line=frame.source_line,
    )


def normalize_trace(trace: StackTrace, opts: Optional[NormalizeOptions] = None) -> StackTrace:
    """Return a new StackTrace with all frames and metadata normalized."""
    if opts is None:
        opts = NormalizeOptions()

    normalized_frames: List[Frame] = [
        normalize_frame(f, opts) for f in trace.frames
    ]

    exc_type = trace.exception_type
    if opts.lowercase_exception_type and exc_type:
        exc_type = exc_type.lower()

    return StackTrace(
        frames=normalized_frames,
        exception_type=exc_type,
        exception_message=trace.exception_message,
    )
