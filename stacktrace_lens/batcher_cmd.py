"""CLI sub-command: batch — batch-process multiple trace files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import StackTrace, parse_stacktrace
from stacktrace_lens.batcher import BatchOptions, batch_traces, format_batch


def _build_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("batch", help="Batch-process multiple stack trace files")
    p.add_argument("files", nargs="*", help="Trace files to process")
    p.add_argument(
        "--max-size", type=int, default=50, metavar="N",
        help="Maximum traces per batch (default: 50)",
    )
    p.add_argument(
        "--group-by-exception", action="store_true",
        help="Group traces by exception type",
    )
    p.add_argument("--label", default=None, help="Label for the batch")
    p.add_argument("--json", action="store_true", help="Emit JSON summary")


def _load_trace(path: str) -> StackTrace | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
        return parse_stacktrace(text)
    except (OSError, ValueError):
        return None


def batcher_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if not args.files:
        err.write("batch: no files provided\n")
        return 1

    traces: List[StackTrace] = []
    for path in args.files:
        t = _load_trace(path)
        if t is None:
            err.write(f"batch: could not load trace from '{path}'\n")
            return 1
        traces.append(t)

    opts = BatchOptions(
        max_batch_size=args.max_size,
        group_by_exception=args.group_by_exception,
        label=args.label,
    )
    report = batch_traces(traces, opts)

    if args.json:
        payload = {
            "label": report.label,
            "count": report.count,
            "groups": report.groups,
        }
        out.write(json.dumps(payload) + "\n")
    else:
        out.write(format_batch(report) + "\n")

    return 0
