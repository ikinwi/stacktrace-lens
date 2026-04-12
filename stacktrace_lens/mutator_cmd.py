"""CLI sub-command: mutate — apply transformations to a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.mutator import MutateOptions, mutate_trace
from stacktrace_lens.parser import parse_stacktrace


def _build_subparser(subparsers) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "mutate",
        help="Apply in-place transformations to stack trace frames.",
    )
    p.add_argument(
        "--strip-line-numbers",
        action="store_true",
        default=False,
        help="Set all line numbers to 0.",
    )
    p.add_argument(
        "--uppercase-filenames",
        action="store_true",
        default=False,
        help="Convert all filenames to uppercase.",
    )
    p.add_argument(
        "--file",
        metavar="PATH",
        default=None,
        help="Read stack trace from file instead of stdin.",
    )
    return p


def mutator_command(args: argparse.Namespace, argv: List[str] | None = None) -> int:
    if args.file:
        try:
            raw = open(args.file).read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print("Error: empty input.", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    opts = MutateOptions(
        strip_line_numbers=args.strip_line_numbers,
        uppercase_filenames=args.uppercase_filenames,
    )
    report = mutate_trace(trace, opts)

    print(report.summary_line())
    for mf in report.frames:
        print(f"  {mf}")

    return 0
