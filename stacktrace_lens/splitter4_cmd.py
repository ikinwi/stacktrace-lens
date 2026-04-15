"""CLI sub-command: split4 — split a trace into depth-bucket layers."""
from __future__ import annotations

import argparse
import sys

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.splitter4 import split_by_depth


def _c(text: str, code: str, *, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "split4",
        help="Split a stack trace into depth-bucket layers.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin).",
    )
    p.add_argument(
        "--bucket-size",
        type=int,
        default=5,
        metavar="N",
        help="Number of frames per depth bucket (default: 5).",
    )
    p.add_argument("--no-colour", action="store_true", help="Disable colour output.")


def splitter4_command(args: argparse.Namespace) -> int:
    colour = not getattr(args, "no_colour", False)

    if args.file:
        try:
            raw = open(args.file).read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = split_by_depth(trace, bucket_size=args.bucket_size)

    header = _c(report.summary_line(), "1", colour=colour)
    print(header)

    for layer in report.layers:
        bucket_label = _c(f"  [{layer.bucket}]", "36", colour=colour)
        print(f"{bucket_label}  {layer.count} frame(s)")
        for frame in layer.frames:
            fn = frame.function or "<module>"
            fname = _c(frame.filename, "33", colour=colour)
            func = _c(fn, "32", colour=colour)
            print(f"    {fname}:{frame.lineno}  {func}")

    return 0
