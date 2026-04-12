"""CLI sub-command: split chained tracebacks."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .parser import parse_stacktrace
from .splitter import format_split, split_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "split",
        help="Split a chained traceback into individual exceptions.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a traceback file (default: stdin).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colour output.",
    )
    p.add_argument(
        "--count-only",
        action="store_true",
        default=False,
        help="Print only the number of chained exceptions found.",
    )
    return p


def splitter_command(args: argparse.Namespace) -> int:
    """Entry point for the *split* sub-command.  Returns an exit code."""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("error: no input provided.", file=sys.stderr)
        return 1

    report = split_trace(text)

    if not report.traces:
        print("error: could not parse any traceback from input.", file=sys.stderr)
        return 1

    if args.count_only:
        print(report.count)
        return 0

    colour = not args.no_color
    print(format_split(report, colour=colour))
    return 0
