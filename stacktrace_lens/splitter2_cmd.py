"""CLI sub-command: segment — split a stack trace into package segments."""
from __future__ import annotations

import argparse
import sys

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.splitter2 import segment_trace


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("segment", help="Split a stack trace into package segments")
    p.add_argument(
        "file",
        nargs="?",
        help="Path to a file containing a stack trace (default: stdin)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colour output",
    )
    return p


def splitter2_command(args: argparse.Namespace) -> int:
    """Entry point for the *segment* sub-command."""
    if getattr(args, "file", None):
        try:
            text = open(args.file).read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("error: no input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(text)
    report = segment_trace(trace)

    use_color = not getattr(args, "no_color", False)

    def _c(code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if use_color else s

    print(_c("1;34", report.summary_line()))
    for seg in report.segments:
        header = _c("1;33", f"  [{seg.label}]  {seg.count} frame(s)")
        print(header)
        for frame in seg.frames:
            fn = frame.function or "<module>"
            print(f"    {frame.filename}:{frame.lineno}  {fn}")
    return 0
