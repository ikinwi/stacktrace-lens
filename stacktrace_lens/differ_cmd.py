"""CLI sub-command: differ — render a unified diff between two trace files."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.comparator import compare_traces
from stacktrace_lens.differ import DiffRenderOptions, render_diff, summary_line


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("differ", help="Render a unified diff between two stack-trace files")
    p.add_argument("left", help="Path to the baseline trace file")
    p.add_argument("right", help="Path to the new trace file")
    p.add_argument("--no-colour", action="store_true", default=False, help="Disable colour output")
    p.add_argument("--hide-unchanged", action="store_true", default=False, help="Hide unchanged frames")
    p.add_argument("--summary", action="store_true", default=False, help="Print a one-line summary only")
    return p


def _read_trace(path: str):
    try:
        with open(path) as fh:
            raw = fh.read().strip()
    except FileNotFoundError:
        print(f"differ: file not found: {path}", file=sys.stderr)
        return None
    if not raw:
        print(f"differ: file is empty: {path}", file=sys.stderr)
        return None
    return parse_stacktrace(raw)


def differ_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    left_trace = _read_trace(args.left)
    if left_trace is None:
        return 1
    right_trace = _read_trace(args.right)
    if right_trace is None:
        return 1

    diff = compare_traces(left_trace, right_trace)

    if args.summary:
        print(summary_line(diff), file=out)
        return 0

    opts = DiffRenderOptions(
        colour=not args.no_colour,
        show_unchanged=not args.hide_unchanged,
    )
    print(render_diff(diff, opts), file=out)
    return 0
