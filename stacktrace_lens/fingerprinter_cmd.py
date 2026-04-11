"""CLI sub-command: fingerprint a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .parser import parse_stacktrace
from .fingerprinter import fingerprint_trace, format_fingerprint


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = subparsers.add_parser(
        "fingerprint",
        help="Compute a stable fingerprint for a stack trace.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing the stack trace (default: stdin).",
    )
    p.add_argument(
        "--short",
        action="store_true",
        help="Print only the first 8 hex characters of the fingerprint.",
    )
    p.add_argument(
        "--no-message",
        dest="include_message",
        action="store_false",
        default=True,
        help="Exclude the exception message from the fingerprint hash.",
    )
    p.add_argument(
        "--max-frames",
        type=int,
        default=None,
        metavar="N",
        help="Use only the last N frames when hashing.",
    )
    return p


def fingerprinter_command(args: argparse.Namespace, argv: Optional[List[str]] = None) -> int:
    """Entry point for the *fingerprint* sub-command."""
    if args.file:
        try:
            raw = open(args.file).read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print("error: no input provided", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    result = fingerprint_trace(
        trace,
        include_message=args.include_message,
        max_frames=args.max_frames,
    )
    print(format_fingerprint(result, short=args.short))
    return 0
