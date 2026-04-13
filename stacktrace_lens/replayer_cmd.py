"""CLI sub-command: replay — play back a collection of JSON trace files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from stacktrace_lens.parser import StackTrace, Frame
from stacktrace_lens.replayer import ReplayOptions, replay_traces


def _build_subparser(subparsers) -> argparse.ArgumentParser:
    p = subparsers.add_parser("replay", help="Replay recorded stack traces")
    p.add_argument("files", nargs="*", metavar="FILE", help="JSON trace files")
    p.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier")
    p.add_argument("--max", type=int, default=None, dest="max_entries", help="Max events")
    p.add_argument("--loop", action="store_true", help="Loop through entries")
    return p


def _load_trace(path: str) -> Optional[Tuple[StackTrace, str]]:
    try:
        data = json.loads(Path(path).read_text())
        frames = [
            Frame(
                filename=f.get("filename", "<unknown>"),
                lineno=f.get("lineno", 0),
                function=f.get("function", ""),
                source_line=f.get("source_line"),
            )
            for f in data.get("frames", [])
        ]
        trace = StackTrace(
            exception_type=data.get("exception_type", "Exception"),
            exception_message=data.get("exception_message", ""),
            frames=frames,
        )
        return trace, data.get("label", Path(path).stem)
    except Exception:
        return None


def replayer_command(args: argparse.Namespace, out=sys.stdout) -> int:
    if not args.files:
        out.write("replay: no files provided\n")
        return 1

    entries = []
    for path in args.files:
        result = _load_trace(path)
        if result is None:
            out.write(f"replay: cannot load {path}\n")
            return 1
        entries.append(result)

    options = ReplayOptions(
        speed=args.speed,
        max_entries=args.max_entries,
        loop=args.loop,
    )
    report = replay_traces(entries, options)
    for event in report.events:
        out.write(str(event) + "\n")
    out.write(report.summary_line() + "\n")
    return 0
