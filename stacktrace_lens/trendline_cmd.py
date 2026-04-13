"""CLI sub-command: trendline — show frequency trends across trace files."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.timeline import TimestampedTrace
from stacktrace_lens.trendline import build_trendline, format_trendline


def _build_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("trendline", help="Show exception frequency trends")
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="JSON files containing {timestamp, text} objects (one per file)",
    )
    p.add_argument(
        "--bucket",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket size in seconds (default: 60)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable colour output")


def _load_entry(path: Path) -> TimestampedTrace:
    data = json.loads(path.read_text())
    ts = datetime.fromisoformat(data["timestamp"]).replace(tzinfo=timezone.utc)
    trace = parse_stacktrace(data["text"])
    label = data.get("label")
    return TimestampedTrace(trace=trace, timestamp=ts, label=label)


def trendline_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if not args.files:
        err.write("trendline: no input files provided\n")
        return 1

    entries = []
    for f in args.files:
        p = Path(f)
        if not p.exists():
            err.write(f"trendline: file not found: {f}\n")
            return 1
        try:
            entries.append(_load_entry(p))
        except Exception as exc:  # noqa: BLE001
            err.write(f"trendline: failed to load {f}: {exc}\n")
            return 1

    report = build_trendline(entries, bucket_size=args.bucket)
    out.write(format_trendline(report))
    out.write("\n")
    return 0
