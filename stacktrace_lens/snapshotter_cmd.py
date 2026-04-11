"""CLI sub-command: snapshot — save a parsed stack trace as a JSON snapshot."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.snapshotter import Snapshot, dump_snapshot, load_snapshots


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("snapshot", help="Capture a stack trace as a JSON snapshot")
    p.add_argument("--input", "-i", default="-", help="Input file (default: stdin)")
    p.add_argument("--output", "-o", default="-", help="Output file (default: stdout)")
    p.add_argument("--label", "-l", default=None, help="Optional label for the snapshot")
    p.add_argument("--list", dest="list_snaps", default=None,
                   metavar="FILE", help="List snapshots stored in FILE")
    return p


def snapshotter_command(args: argparse.Namespace) -> int:
    # --list mode: read existing snapshot file and print summary
    if getattr(args, "list_snaps", None):
        path = Path(args.list_snaps)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        snaps = load_snapshots(path.read_text())
        for i, s in enumerate(snaps):
            label = s.label or "(no label)"
            print(f"[{i}] {s.captured_at.isoformat()}  {label}  "
                  f"{s.trace.exception_type}: {s.trace.exception_message}")
        return 0

    # Capture mode
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        p = Path(args.input)
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 1
        raw = p.read_text()

    trace = parse_stacktrace(raw)
    if trace is None:
        print("error: no stack trace found in input", file=sys.stderr)
        return 1

    snap = Snapshot(trace=trace, label=args.label)
    output = dump_snapshot(snap)

    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output)

    return 0
