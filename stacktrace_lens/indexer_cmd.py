"""CLI sub-command: index – index frames from one or more trace files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import StackTrace, parse_stacktrace
from stacktrace_lens.indexer import index_traces, format_index


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("index", help="Index frames from trace files for quick lookup")
    p.add_argument("files", nargs="*", metavar="FILE", help="Trace files (omit for stdin)")
    p.add_argument("--file", dest="query_file", default=None, metavar="FILENAME",
                   help="Show only entries matching this source filename")
    p.add_argument("--function", dest="query_fn", default=None, metavar="FUNCTION",
                   help="Show only entries matching this function name")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit results as JSON")
    return p


def _load_traces(paths: List[str]) -> List[StackTrace]:
    traces: List[StackTrace] = []
    for p in paths:
        text = Path(p).read_text(encoding="utf-8")
        t = parse_stacktrace(text)
        if t:
            traces.append(t)
    return traces


def indexer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if args.files:
        for path in args.files:
            if not Path(path).exists():
                err.write(f"error: file not found: {path}\n")
                return 1
        traces = _load_traces(args.files)
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            err.write("error: no input\n")
            return 1
        t = parse_stacktrace(raw)
        traces = [t] if t else []

    if not traces:
        err.write("error: no valid traces found\n")
        return 1

    report = index_traces(traces)

    if args.as_json:
        data = [
            {
                "filename": e.frame.filename,
                "lineno": e.frame.lineno,
                "function": e.frame.function,
                "trace_index": e.trace_index,
                "frame_index": e.frame_index,
            }
            for e in report.entries
        ]
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(format_index(report, query_file=args.query_file, query_fn=args.query_fn) + "\n")

    return 0
