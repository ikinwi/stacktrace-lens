"""CLI sub-command: dispatch — route a trace to the best handler and print output."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.dispatcher import build_default_dispatcher


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "dispatch",
        help="Route a stack trace to the most relevant handler and print its output.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin).",
    )
    p.add_argument(
        "--rule",
        dest="show_rule",
        action="store_true",
        default=False,
        help="Print the matched rule name before the output.",
    )
    return p


def dispatcher_command(args: argparse.Namespace, argv: Optional[List[str]] = None) -> int:
    """Entry point for the dispatch sub-command. Returns exit code."""
    try:
        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as fh:
                    raw = fh.read()
            except FileNotFoundError:
                print(f"error: file not found: {args.file}", file=sys.stderr)
                return 1
        else:
            raw = sys.stdin.read()

        if not raw.strip():
            print("error: no input provided", file=sys.stderr)
            return 1

        trace = parse_stacktrace(raw)
        dispatcher = build_default_dispatcher()
        result = dispatcher.dispatch(trace)

        if args.show_rule:
            print(f"rule: {result.rule_name}")
        print(result.output)
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        print(f"error: {exc}", file=sys.stderr)
        return 1
