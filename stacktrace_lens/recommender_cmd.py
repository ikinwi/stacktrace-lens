"""CLI sub-command: recommend — print actionable fix suggestions for a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.recommender import format_recommendations, recommend


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "recommend",
        help="Show actionable fix recommendations for a stack trace.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin).",
    )
    p.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable colour output.",
    )
    p.add_argument(
        "--top",
        action="store_true",
        default=False,
        help="Print only the single highest-priority recommendation.",
    )
    return p


def recommender_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Entry point for the *recommend* sub-command.  Returns an exit code."""
    raw: Optional[str] = None

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except FileNotFoundError:
            err.write(f"recommender: file not found: {args.file}\n")
            return 1
    else:
        if sys.stdin.isatty():
            err.write("recommender: no input provided (pass a file or pipe a stack trace).\n")
            return 1
        raw = sys.stdin.read()

    if not raw or not raw.strip():
        err.write("recommender: empty input.\n")
        return 1

    trace = parse_stacktrace(raw)
    report = recommend(trace)
    colour = not args.no_colour

    if args.top:
        top = report.top()
        if top is None:
            out.write("No recommendations.\n")
        else:
            col_map = {1: "\033[31m", 2: "\033[33m", 3: "\033[36m"} if colour else {}
            reset = "\033[0m" if colour else ""
            col = col_map.get(top.priority, "")
            badge = ["HIGH", "MED", "LOW"][min(top.priority - 1, 2)]
            out.write(f"{col}[{badge}]{reset} {top.title}: {top.detail}\n")
    else:
        out.write(format_recommendations(report, colour=colour) + "\n")

    return 0
