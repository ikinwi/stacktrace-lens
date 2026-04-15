"""CLI sub-command: route traces to named destinations."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.router import RouteRule, route_traces


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("route", help="Route stack traces by exception or file pattern")
    p.add_argument("files", nargs="*", help="Trace files (stdin if omitted)")
    p.add_argument("--exception", metavar="PATTERN", help="Exception type regex")
    p.add_argument("--file", metavar="PATTERN", help="Filename regex")
    p.add_argument("--name", metavar="NAME", default="default", help="Rule name")
    p.add_argument("--no-color", action="store_true", help="Disable color output")
    return p


def router_command(args: argparse.Namespace) -> int:
    raw_texts: List[str] = []
    if getattr(args, "files", None):
        for path in args.files:
            try:
                with open(path) as fh:
                    raw_texts.append(fh.read())
            except FileNotFoundError:
                print(f"error: file not found: {path}", file=sys.stderr)
                return 1
    else:
        raw_texts.append(sys.stdin.read())

    traces = []
    for raw in raw_texts:
        t = parse_stacktrace(raw)
        if t is not None:
            traces.append(t)

    if not traces:
        print("error: no valid traces found", file=sys.stderr)
        return 1

    rule = RouteRule(
        name=args.name,
        exception_pattern=getattr(args, "exception", None),
        file_pattern=getattr(args, "file", None),
    )
    results = route_traces(traces, [rule])
    for res in results:
        print(str(res))
    return 0
