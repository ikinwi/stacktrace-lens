"""streaker_cmd.py – CLI sub-command for streak detection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import StackTrace, parse_stacktrace
from stacktrace_lens.streaker import detect_streaks, format_streaks


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "streak",
        help="Detect consecutive exception streaks across multiple trace files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="JSON files each containing a single serialised stack trace (text).",
    )
    p.add_argument(
        "--min-length",
        type=int,
        default=2,
        metavar="N",
        help="Minimum run length to report as a streak (default: 2).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour output.",
    )


def _load_trace(path: str) -> StackTrace:
    text = Path(path).read_text(encoding="utf-8")
    return parse_stacktrace(text)


def streaker_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    traces: List[StackTrace] = []
    for f in args.files:
        try:
            traces.append(_load_trace(f))
        except FileNotFoundError:
            err.write(f"error: file not found: {f}\n")
            return 1
        except Exception as exc:  # noqa: BLE001
            err.write(f"error: could not parse {f}: {exc}\n")
            return 1

    if not traces:
        err.write("error: no traces loaded\n")
        return 1

    report = detect_streaks(traces, min_length=args.min_length)
    out.write(format_streaks(report))
    out.write("\n")
    return 0
