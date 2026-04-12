"""CLI sub-command: summarize one or more trace files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .parser import parse_stacktrace, StackTrace
from .summarizer import summarize_traces, format_summary


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("summarize", help="Summarize one or more stack-trace files")
    p.add_argument("files", nargs="*", metavar="FILE", help="Trace files (default: stdin)")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    p.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")


def _load_traces(files: List[str]) -> List[StackTrace]:
    traces: List[StackTrace] = []
    for path in files:
        try = Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return []
        trace = parse_stacktrace(text)
        if trace is not None:
            traces.append(trace)
    return traces


def summarizer_command(args: argparse.Namespace) -> int:
    if args.files:
        traces = _load_traces(args.files)
        if not traces and args.files:
            return 1
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            print("error: no input provided", file=sys.stderr)
            return 1
        trace = parse_stacktrace(raw)
        traces = [trace] if trace is not None else []

    if not traces:
        print("error: no valid traces found", file=sys.stderr)
        return 1

    report = summarize_traces(traces)

    if args.as_json:
        data = {
            "total_traces": report.total_traces,
            "total_frames": report.total_frames,
            "avg_depth": report.avg_depth,
            "most_common_exception": report.most_common_exception,
            "most_common_file": report.most_common_file,
            "most_common_function": report.most_common_function,
        }
        print(json.dumps(data, indent=2))
    else:
        print(format_summary(report, colour=not args.no_colour))

    return 0
