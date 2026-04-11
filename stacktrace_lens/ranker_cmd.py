"""CLI sub-command: rank multiple stack-trace files by composite score."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional

from .parser import parse_stacktrace
from .ranker import format_rank, rank_traces


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rank",
        help="Rank stack traces by composite severity/depth/recurrence score.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Paths to files containing stack traces (one trace per file).",
    )
    p.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable colour output.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="as_json",
        help="Emit results as JSON.",
    )
    return p


def ranker_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    paths: List[Path] = [Path(f) for f in args.files]

    traces = []
    labels: List[Optional[str]] = []
    for path in paths:
        if not path.exists():
            err.write(f"error: file not found: {path}\n")
            return 1
        raw = path.read_text(encoding="utf-8")
        trace = parse_stacktrace(raw)
        if trace is None:
            err.write(f"warning: could not parse trace in {path}, skipping\n")
            continue
        traces.append(trace)
        labels.append(path.name)

    if not traces:
        err.write("error: no valid traces found\n")
        return 1

    recurrence: Counter = Counter(t.exception_type for t in traces)
    report = rank_traces(traces, recurrence_counts=dict(recurrence), labels=labels)

    if args.as_json:
        payload = [
            {
                "rank": i,
                "label": e.label,
                "exception_type": e.trace.exception_type,
                "composite": e.composite,
                "severity_score": e.severity_score,
                "depth_score": e.depth_score,
                "recurrence_score": e.recurrence_score,
            }
            for i, e in enumerate(report.ranked(), 1)
        ]
        out.write(json.dumps(payload, indent=2))
        out.write("\n")
    else:
        out.write(format_rank(report, colour=not args.no_colour))
        out.write("\n")

    return 0
