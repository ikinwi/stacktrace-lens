"""CLI sub-command: print statistics about a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.stats import compute_stats, format_stats


def stats_command(
    argv: Optional[List[str]] = None,
    stdin_text: Optional[str] = None,
) -> int:
    """Entry-point for the *stats* sub-command.

    Parameters
    ----------
    argv:
        Argument list (defaults to ``sys.argv[1:]``).
    stdin_text:
        Pre-supplied stdin content, used during testing.

    Returns
    -------
    int
        Exit code – 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        prog="stacktrace-lens stats",
        description="Show statistics for a Python stack trace.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a file containing the stack trace (reads stdin if omitted).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit statistics as JSON instead of plain text.",
    )
    args = parser.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    elif stdin_text is not None:
        raw = stdin_text
    else:
        raw = sys.stdin.read()

    raw = raw.strip()
    if not raw:
        print("error: no input provided", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    stats = compute_stats(trace)

    if args.json:
        import json

        payload = {
            "exception_type": stats.exception_type,
            "total_frames": stats.total_frames,
            "unique_files": stats.unique_files,
            "unique_functions": stats.unique_functions,
            "top_file": stats.top_file,
            "top_function": stats.top_function,
            "packages": stats.packages,
            "file_counts": stats.file_counts,
            "function_counts": stats.function_counts,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_stats(stats))

    return 0
