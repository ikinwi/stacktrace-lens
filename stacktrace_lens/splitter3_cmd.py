"""CLI sub-command: partition – split a trace into package-boundary partitions."""
from __future__ import annotations

import argparse
import sys

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.splitter3 import partition_trace

_COLOURS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "green": "\033[32m",
}


def _c(text: str, colour: str, use_colour: bool) -> str:
    if not use_colour:
        return text
    code = _COLOURS.get(colour, "")
    return f"{code}{text}{_COLOURS['reset']}"


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "partition",
        help="Split a stack trace into package-boundary partitions.",
    )
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")


def partition_command(args: argparse.Namespace) -> int:
    use_colour = not getattr(args, "no_colour", False)
    try:
        if getattr(args, "file", None):
            with open(args.file) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not raw.strip():
        print("Error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = partition_trace(trace)

    print(_c(report.summary_line, "bold", use_colour))
    for idx, part in enumerate(report.partitions, 1):
        header = _c(f"  [{idx}] {part.package} ({part.count} frame(s))", "cyan", use_colour)
        print(header)
        for frame in part.frames:
            fname = _c(frame.filename or "<unknown>", "yellow", use_colour)
            func = _c(frame.function or "<module>", "green", use_colour)
            lineno = frame.lineno or "?"
            print(f"      {fname}:{lineno} in {func}")
    return 0
