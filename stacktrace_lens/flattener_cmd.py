"""CLI sub-command: flatten multiple trace files into one frame list."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import parse_stacktrace, StackTrace
from stacktrace_lens.flattener import flatten_traces, format_flatten


def _build_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("flatten", help="Flatten chained traces into one frame list")
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="JSON trace files to flatten (reads stdin if omitted)",
    )
    p.add_argument(
        "--no-colour",
        dest="no_colour",
        action="store_true",
        help="Disable ANSI colour output",
    )
    p.set_defaults(func=flattener_command)


def _load_trace(path: str) -> StackTrace:
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    raw = data.get("raw", "")
    return parse_stacktrace(raw)


def flattener_command(args: argparse.Namespace) -> int:
    traces: List[StackTrace] = []

    if args.files:
        for f in args.files:
            p = Path(f)
            if not p.exists():
                print(f"error: file not found: {f}", file=sys.stderr)
                return 1
            try:
                traces.append(_load_trace(f))
            except Exception as exc:  # noqa: BLE001
                print(f"error: could not parse {f}: {exc}", file=sys.stderr)
                return 1
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            print("error: no input", file=sys.stderr)
            return 1
        traces.append(parse_stacktrace(raw))

    if not traces:
        print("error: no traces to flatten", file=sys.stderr)
        return 1

    report = flatten_traces(traces)
    colour = not getattr(args, "no_colour", False)
    print(format_flatten(report, colour=colour))
    return 0
