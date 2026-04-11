"""CLI sub-command: aggregate multiple stack-trace files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .parser import parse_stacktrace, StackTrace
from .aggregator import aggregate_traces, format_aggregation


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "aggregate",
        help="Aggregate multiple stack-trace files into a summary report.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Stack-trace files to aggregate.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top entries to display (default: 5).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )


def _load_traces(paths: List[str]) -> List[StackTrace]:
    traces: List[StackTrace] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"aggregator: file not found: {p}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        trace = parse_stacktrace(text)
        if trace is not None:
            traces.append(trace)
    return traces


def aggregator_command(args: argparse.Namespace) -> int:
    traces = _load_traces(args.files)
    if not traces:
        print("aggregator: no valid stack traces found.", file=sys.stderr)
        return 1
    report = aggregate_traces(traces)
    top_n = getattr(args, "top", 5)
    print(format_aggregation(report, top_n=top_n))
    return 0
