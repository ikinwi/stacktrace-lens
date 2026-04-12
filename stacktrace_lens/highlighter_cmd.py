"""CLI sub-command: highlight frames in a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.highlighter import HighlightOptions, highlight_frames, format_highlight


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("highlight", help="Highlight notable frames in a stack trace")
    p.add_argument("file", nargs="?", default=None, help="Path to stack trace file (default: stdin)")
    p.add_argument(
        "--pattern", "-p",
        dest="patterns",
        action="append",
        default=[],
        metavar="REGEX",
        help="Regex pattern to highlight matching frames (repeatable)",
    )
    p.add_argument(
        "--user-code",
        action="store_true",
        default=False,
        help="Highlight frames that appear to be user code",
    )
    p.add_argument(
        "--no-origin",
        action="store_true",
        default=False,
        help="Do not auto-highlight the exception-origin frame",
    )
    p.add_argument("--colour", "--color", action="store_true", default=False, help="Enable colour output")
    return p


def highlighter_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if args.file:
        try:
            raw = open(args.file).read()
        except OSError as exc:
            err.write(f"error: {exc}\n")
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        err.write("error: empty input\n")
        return 1

    trace = parse_stacktrace(raw)
    options = HighlightOptions(
        patterns=args.patterns,
        highlight_user_code=args.user_code,
        highlight_exception_origin=not args.no_origin,
    )
    report = highlight_frames(trace, options)
    out.write(format_highlight(report, colour=args.colour))
    out.write("\n")
    return 0
