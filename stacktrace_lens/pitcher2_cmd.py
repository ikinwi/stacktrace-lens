"""CLI sub-command: pitcher2 — batch-pitch traces to a webhook."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .parser import parse_stacktrace, StackTrace
from .pitcher2 import BatchPitchOptions, batch_pitch_to_webhook


def _build_subparser(sub: argparse.Action) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "pitcher2",
        help="Batch-send multiple stack trace files to a webhook URL",
    )
    p.add_argument("url", help="Webhook URL to POST to")
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Stack trace text files to send",
    )
    p.add_argument(
        "--no-frames",
        dest="no_frames",
        action="store_true",
        default=False,
        help="Omit frame details from payload",
    )
    p.add_argument(
        "--max-frames",
        dest="max_frames",
        type=int,
        default=10,
        metavar="N",
        help="Maximum frames per trace (default: 10)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        metavar="SEC",
        help="HTTP timeout in seconds (default: 5.0)",
    )
    p.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra tag to include (repeatable)",
    )
    return p


def _load_traces(paths: List[str]) -> List[StackTrace]:
    traces: List[StackTrace] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[pitcher2] file not found: {p}", file=sys.stderr)
            continue
        text = path.read_text()
        trace = parse_stacktrace(text)
        if trace:
            traces.append(trace)
    return traces


def pitcher2_command(args: argparse.Namespace) -> int:
    traces = _load_traces(args.files)
    if not traces:
        print("[pitcher2] no valid traces found", file=sys.stderr)
        return 1

    tags = {}
    for tag in args.tags:
        if "=" in tag:
            k, v = tag.split("=", 1)
            tags[k.strip()] = v.strip()

    opts = BatchPitchOptions(
        include_frames=not args.no_frames,
        max_frames=args.max_frames,
        timeout=args.timeout,
        extra_tags=tags,
    )

    result = batch_pitch_to_webhook(traces, args.url, opts)
    print(result)
    return 0 if result.success else 1
