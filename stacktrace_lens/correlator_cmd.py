"""CLI sub-command: correlate — analyse multiple trace files for common patterns."""

from __future__ import annotations

import argparse
import sys
from typing import List

from .parser import parse_stacktrace, StackTrace
from .correlator import correlate_traces, format_correlation


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "correlate",
        help="Correlate multiple stack-trace files and report common patterns.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more files containing Python stack traces (use - for stdin).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit a JSON summary instead of plain text.",
    )


def _read_trace(path: str) -> StackTrace | None:
    """Read and parse a stack trace from *path* (or stdin when path is ``-``).

    Returns ``None`` and prints a warning to stderr if the file cannot be read
    or the content cannot be parsed as a valid stack trace.
    """
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        return parse_stacktrace(text)
    except OSError as exc:
        print(f"[warn] could not read file '{path}': {exc}", file=sys.stderr)
        return None
    except ValueError as exc:
        print(f"[warn] could not parse trace from '{path}': {exc}", file=sys.stderr)
        return None


def correlator_command(args: argparse.Namespace) -> int:
    traces: List[StackTrace] = []
    for path in args.files:
        trace = _read_trace(path)
        if trace is not None:
            traces.append(trace)

    if not traces:
        print("[error] no valid traces found.", file=sys.stderr)
        return 1

    report = correlate_traces(traces)

    if getattr(args, "json", False):
        import json

        payload = {
            "total_traces": report.total_traces,
            "by_exception": {k: v.count for k, v in report.by_exception.items()},
            "by_file": {k: v.count for k, v in report.by_file.items()},
            "by_function": {k: v.count for k, v in report.by_function.items()},
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_correlation(report))

    return 0
