"""CLI sub-command: merge multiple trace files into a report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import parse_stacktrace, StackTrace
from stacktrace_lens.merger import merge_traces, format_merge


def _build_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("merge", help="Merge multiple stack-trace files into one report")
    p.add_argument("files", nargs="+", metavar="FILE", help="Trace files to merge")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")


def _load_trace(path: str) -> StackTrace | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read '{path}': {exc}", file=sys.stderr)
        return None
    return parse_stacktrace(text)


def merger_command(args: argparse.Namespace) -> int:
    traces: List[StackTrace] = []
    for fpath in args.files:
        trace = _load_trace(fpath)
        if trace is None:
            return 1
        traces.append(trace)

    if not traces:
        print("error: no traces loaded", file=sys.stderr)
        return 1

    report = merge_traces(traces)

    if args.as_json:
        data = {
            "total_traces": report.total_traces,
            "combined_frames": len(report.merged_frames),
            "unique_exceptions": report.unique_exceptions,
            "unique_files": report.unique_files,
            "common_exception": report.common_exception,
            "common_file": report.common_file,
            "exception_counts": dict(report.exception_counts),
        }
        print(json.dumps(data, indent=2))
    else:
        colour = not getattr(args, "no_colour", False)
        print(format_merge(report, colour=colour))

    return 0
