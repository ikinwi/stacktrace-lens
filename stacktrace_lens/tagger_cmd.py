"""CLI sub-command: tag — display auto-tags for a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.tagger import format_tags, tag_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("tag", help="Auto-tag a stack trace by exception category")
    p.add_argument("file", nargs="?", help="Path to file containing the stack trace (default: stdin)")
    p.add_argument("-t", "--tag", dest="extra_tags", action="append", metavar="TAG",
                   help="Additional tag to attach (can be repeated)")
    p.add_argument("--note", default=None, help="Optional free-text note to attach")
    p.add_argument("--no-auto", dest="no_auto", action="store_true",
                   help="Disable automatic tag inference")
    p.add_argument("--no-colour", dest="no_colour", action="store_true",
                   help="Disable ANSI colour output")
    return p


def tagger_command(args: argparse.Namespace) -> int:
    """Entry point for the 'tag' sub-command. Returns exit code."""
    try:
        if getattr(args, "file", None):
            try:
                raw = open(args.file).read()
            except FileNotFoundError:
                print(f"error: file not found: {args.file}", file=sys.stderr)
                return 1
        else:
            raw = sys.stdin.read()
    except Exception as exc:  # pragma: no cover
        print(f"error reading input: {exc}", file=sys.stderr)
        return 1

    if not raw.strip():
        print("error: no input provided", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    extra: Optional[List[str]] = getattr(args, "extra_tags", None)
    result = tag_trace(
        trace,
        extra_tags=extra,
        note=getattr(args, "note", None),
        include_auto=not getattr(args, "no_auto", False),
    )
    colour = not getattr(args, "no_colour", False)
    print(format_tags(result, colour=colour))
    return 0
