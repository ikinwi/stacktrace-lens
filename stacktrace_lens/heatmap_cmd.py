"""CLI sub-command: heatmap — show file/function hotspots across trace files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.heatmap import build_heatmap, format_heatmap
from stacktrace_lens.parser import parse_stacktrace, StackTrace


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("heatmap", help="Show file/function hotspots across multiple traces")
    p.add_argument("files", nargs="*", metavar="FILE", help="Trace files (JSON or raw text)")
    p.add_argument("--top", type=int, default=10, metavar="N", help="Number of entries to show (default: 10)")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output raw JSON report")
    return p


def _load_trace(path: str) -> StackTrace | None:
    text = Path(path).read_text(encoding="utf-8")
    # Support JSON replay format: extract 'raw' field if present
    try:
        obj = json.loads(text)
        raw = obj.get("raw") or obj.get("text", "")
        return parse_stacktrace(raw) if raw else None
    except (json.JSONDecodeError, AttributeError):
        return parse_stacktrace(text)


def heatmap_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    traces: List[StackTrace] = []

    if not args.files:
        err.write("heatmap: no input files provided\n")
        return 1

    for path in args.files:
        if not Path(path).exists():
            err.write(f"heatmap: file not found: {path}\n")
            return 1
        trace = _load_trace(path)
        if trace is not None:
            traces.append(trace)

    if not traces:
        err.write("heatmap: no valid traces found\n")
        return 1

    report = build_heatmap(traces)

    if args.as_json:
        import dataclasses
        out.write(json.dumps(dataclasses.asdict(report), indent=2))
        out.write("\n")
    else:
        out.write(format_heatmap(report, top_n=args.top))
        out.write("\n")

    return 0
