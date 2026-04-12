"""CLI sub-command: scope  — show scope classification for each frame."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scoper import format_scope_report, scope_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "scope",
        help="Classify each frame as user / test / stdlib / third-party",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin)",
    )
    p.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable colour output",
    )
    p.add_argument(
        "--user-only",
        action="store_true",
        default=False,
        help="Print only user-scope frames",
    )
    return p


def scoper_command(args: argparse.Namespace) -> int:
    """Entry-point for the *scope* sub-command.  Returns an exit code."""
    try:
        if args.file:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    if not raw.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = scope_trace(trace)

    if args.user_only:
        from stacktrace_lens.scoper import ScopeReport

        filtered = ScopeReport(frames=report.user_frames)
        print(format_scope_report(filtered, colour=not args.no_colour))
    else:
        print(format_scope_report(report, colour=not args.no_colour))

    return 0
