"""CLI sub-command: timeline — accumulate traces from multiple files and
render a chronological summary."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.timeline import Timeline, render_timeline


def _parse_ts(value: str) -> datetime.datetime:
    """Parse an ISO-8601 datetime string (best-effort)."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Cannot parse datetime: {value!r}")


def timeline_command(argv: List[str] | None = None) -> int:
    """Entry point for the ``stacktrace-lens timeline`` sub-command."""
    ap = argparse.ArgumentParser(
        prog="stacktrace-lens timeline",
        description="Show a chronological summary of multiple stack-trace files.",
    )
    ap.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Stack-trace text files to include in the timeline.",
    )
    ap.add_argument(
        "--timestamps",
        nargs="*",
        metavar="TS",
        default=None,
        type=_parse_ts,
        help="Optional ISO-8601 timestamps, one per file.",
    )
    ap.add_argument(
        "--labels",
        nargs="*",
        metavar="LABEL",
        default=None,
        help="Optional labels, one per file.",
    )
    ap.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colour output.",
    )

    args = ap.parse_args(argv)
    timeline = Timeline()

    timestamps = args.timestamps or []
    labels = args.labels or []

    for idx, filepath in enumerate(args.files):
        path = Path(filepath)
        if not path.exists():
            print(f"error: file not found: {filepath}", file=sys.stderr)
            return 1
        raw = path.read_text(encoding="utf-8", errors="replace")
        trace = parse_stacktrace(raw)
        ts = timestamps[idx] if idx < len(timestamps) else None
        label = labels[idx] if idx < len(labels) else path.name
        timeline.add(trace, label=label, captured_at=ts)

    output = render_timeline(timeline, use_colour=not args.no_color)
    print(output)
    return 0
