"""CLI sub-command: fuse two stack traces."""
from __future__ import annotations
import argparse
import sys
from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.fuser import fuse_traces, FuseReport


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("fuse", help="Fuse two stack traces into a unified report")
    p.add_argument("left", help="Path to first (left) stack trace file")
    p.add_argument("right", help="Path to second (right) stack trace file")
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    return p


def _read_trace(path: str):
    try:
        with open(path) as fh:
            return parse_stacktrace(fh.read())
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return None


def fuser_command(args: argparse.Namespace) -> int:
    left = _read_trace(args.left)
    if left is None:
        return 1
    right = _read_trace(args.right)
    if right is None:
        return 1

    report = fuse_traces(left, right)
    color = not getattr(args, "no_color", False)

    def c(code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if color else text

    print(c("1", report.summary_line()))
    print(f"  Left : {report.left_exception}")
    print(f"  Right: {report.right_exception}")
    print()
    for ff in report.frames:
        if ff.source == "both":
            line = c("32", str(ff))
        elif ff.source == "left":
            line = c("33", str(ff))
        else:
            line = c("36", str(ff))
        print(line)
    return 0
