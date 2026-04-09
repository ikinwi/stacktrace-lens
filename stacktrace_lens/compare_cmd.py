"""CLI command: compare two stack trace files."""
import argparse
import sys
from pathlib import Path
from typing import List

from .parser import parse_stacktrace
from .comparator import compare_traces, format_diff


def compare_command(argv: List[str] | None = None) -> int:
    """Entry point for the 'compare' sub-command.

    Returns 0 on success, 1 on error.
    """
    ap = argparse.ArgumentParser(
        prog="stacktrace-lens compare",
        description="Compare two Python stack trace files and show differences.",
    )
    ap.add_argument("left", help="Path to the first (baseline) stack trace file.")
    ap.add_argument("right", help="Path to the second (new) stack trace file.")
    ap.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    ap.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 2 when differences are detected.",
    )

    args = ap.parse_args(argv)

    left_path = Path(args.left)
    right_path = Path(args.right)

    for p in (left_path, right_path):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 1

    left_trace = parse_stacktrace(left_path.read_text())
    right_trace = parse_stacktrace(right_path.read_text())

    if left_trace is None or right_trace is None:
        print("error: could not parse one or both stack traces.", file=sys.stderr)
        return 1

    diff = compare_traces(left_trace, right_trace)
    output = format_diff(diff, colour=not args.no_colour)
    print(output)

    if args.exit_code and diff.has_differences:
        return 2
    return 0
