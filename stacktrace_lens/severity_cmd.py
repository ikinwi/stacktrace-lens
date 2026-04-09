"""CLI sub-command: severity — score a stack trace and display its severity."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.severity import format_severity, score_trace


def _build_subparser(sub: ArgumentParser) -> None:
    sub.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin)",
    )
    sub.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable colour output",
    )
    sub.add_argument(
        "--min-severity",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default=None,
        help="Exit with code 2 if severity is below this threshold",
    )


_SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def severity_command(args: Namespace) -> int:
    """Entry point for the severity sub-command. Returns an exit code."""
    if args.file:
        try:
            text = open(args.file).read()
        except OSError as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("No input provided.", file=sys.stderr)
        return 1

    trace = parse_stacktrace(text)
    result = score_trace(trace)
    colour = not getattr(args, "no_colour", False)
    print(format_severity(result, colour=colour))

    if args.min_severity:
        threshold = _SEVERITY_ORDER.index(args.min_severity)
        actual = _SEVERITY_ORDER.index(result.label)
        if actual < threshold:
            return 2

    return 0
