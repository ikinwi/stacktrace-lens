"""CLI sub-command: prune frames from a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.pruner import PruneOptions, prune_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("prune", help="Remove frames from a stack trace.")
    p.add_argument("file", nargs="?", default=None, help="Path to stack trace file (default: stdin).")
    p.add_argument("--max-frames", type=int, default=None, metavar="N", help="Keep at most N frames.")
    p.add_argument("--drop", dest="drop_patterns", action="append", default=[], metavar="PATTERN",
                   help="Drop frames whose filename or function matches PATTERN (regex). Repeatable.")
    p.add_argument("--keep-first", type=int, default=0, metavar="N", help="Always keep the first N frames.")
    p.add_argument("--keep-last", type=int, default=0, metavar="N", help="Always keep the last N frames.")
    return p


def pruner_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Entry point for the *prune* sub-command. Returns exit code."""
    try:
        if args.file:
            with open(args.file) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError:
        err.write(f"pruner: file not found: {args.file}\n")
        return 1

    if not raw.strip():
        err.write("pruner: empty input\n")
        return 1

    trace = parse_stacktrace(raw)
    options = PruneOptions(
        max_frames=args.max_frames,
        drop_patterns=args.drop_patterns,
        keep_first=args.keep_first,
        keep_last=args.keep_last,
    )
    report = prune_trace(trace, options)

    out.write(report.summary_line() + "\n")
    for frame in report.trace.frames:
        out.write(f"  {frame.filename}:{frame.lineno} in {frame.function}\n")
    out.write(f"Exception: {report.trace.exception_type}: {report.trace.exception_message}\n")
    return 0
