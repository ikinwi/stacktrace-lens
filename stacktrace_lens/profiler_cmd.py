"""CLI sub-command: profile  — aggregate hotspots from multiple stack traces."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parser import parse_stacktrace
from .profiler import format_profile, profile_traces


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "profile",
        help="Aggregate frame hotspots across one or more stack-trace files.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Stack-trace files to analyse (reads stdin if omitted).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of hotspots to display (default: 10).",
    )
    p.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output.",
    )
    p.set_defaults(func=profiler_command)


def profiler_command(args: argparse.Namespace) -> int:
    raw_blocks: list[str] = []

    if args.files:
        for path_str in args.files:
            p = Path(path_str)
            if not p.exists():
                print(f"error: file not found: {path_str}", file=sys.stderr)
                return 1
            raw_blocks.append(p.read_text(encoding="utf-8"))
    else:
        data = sys.stdin.read().strip()
        if not data:
            print("error: no input provided", file=sys.stderr)
            return 1
        raw_blocks.append(data)

    traces = []
    for block in raw_blocks:
        try:
            traces.append(parse_stacktrace(block))
        except Exception as exc:  # noqa: BLE001
            print(f"warning: could not parse a block — {exc}", file=sys.stderr)

    if not traces:
        print("error: no valid stack traces found", file=sys.stderr)
        return 1

    report = profile_traces(traces, top_n=args.top)
    print(format_profile(report, colour=not args.no_colour))
    return 0
