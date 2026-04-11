"""CLI sub-command: reduce — noise-reduce a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .parser import parse_stacktrace
from .reducer import ReduceOptions, reduce_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("reduce", help="Noise-reduce a stack trace")
    p.add_argument("file", nargs="?", help="Path to stack trace file (default: stdin)")
    p.add_argument(
        "--max-stdlib",
        type=int,
        default=3,
        metavar="N",
        help="Max consecutive stdlib frames to keep (default: 3)",
    )
    p.add_argument(
        "--no-collapse",
        action="store_true",
        help="Disable collapsing of duplicate consecutive frames",
    )
    p.add_argument(
        "--keep-top",
        type=int,
        default=None,
        metavar="N",
        help="Keep only the N innermost frames before reducing",
    )
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    return p


def reducer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if getattr(args, "file", None):
            try:
                text = open(args.file).read()
            except FileNotFoundError:
                err.write(f"error: file not found: {args.file}\n")
                return 1
        else:
            text = sys.stdin.read()
    except Exception as exc:  # pragma: no cover
        err.write(f"error: {exc}\n")
        return 1

    trace = parse_stacktrace(text)
    if trace is None:
        err.write("error: no stack trace found in input\n")
        return 1

    opts = ReduceOptions(
        max_consecutive_stdlib=args.max_stdlib,
        collapse_duplicates=not args.no_collapse,
        keep_top=args.keep_top,
    )
    report = reduce_trace(trace, opts)

    use_color = not getattr(args, "no_color", False)

    def _c(code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if use_color else text

    out.write(_c("1", f"Exception: {trace.exception_type}") + "\n")
    if trace.exception_message:
        out.write(f"  {trace.exception_message}\n")
    out.write(_c("90", f"Frames: {report.original_count} → {report.reduced_count} (removed {report.removed_count})") + "\n\n")

    for rf in report.reduced_frames:
        repeat = _c("33", f" ×{rf.repeat_count}") if rf.repeat_count > 1 else ""
        location = _c("36", rf.frame.filename) + ":" + _c("33", str(rf.frame.lineno))
        func = _c("32", rf.frame.function)
        out.write(f"  {location} in {func}{repeat}\n")
        if rf.frame.code:
            out.write(_c("90", f"    {rf.frame.code.strip()}") + "\n")

    return 0
