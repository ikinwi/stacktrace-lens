"""CLI sub-command: score7 – context-aware frame scoring (scorer7)."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from .parser import parse_stacktrace
from .scorer7 import score_frames7


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def _render(report, *, colour: bool, top_only: bool) -> str:
    lines = []
    header = f"Exception : {report.exception_type}  |  frames: {report.count}"
    lines.append(_c(header, "1", colour))
    frames = [report.top()] if top_only and report.top() else report.ranked()
    for sf in frames:
        fn = sf.frame.function or "<module>"
        loc = f"{sf.frame.filename}:{sf.frame.lineno}"
        score_str = _c(f"{sf.score:.3f}", "33", colour)
        lines.append(f"  {_c(fn, '36', colour)}  {_c(loc, '90', colour)}  {score_str}")
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("score7", help="Context-aware frame scoring (v7)")
    p.add_argument("file", nargs="?", help="Stacktrace file (default: stdin)")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    p.add_argument("--top", action="store_true", help="Show only the top-scored frame")
    return p


def scorer7_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if getattr(args, "file", None):
            with open(args.file) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if not raw.strip():
        err.write("error: empty input\n")
        return 1

    trace = parse_stacktrace(raw)
    report = score_frames7(trace)
    colour = not getattr(args, "no_colour", False)
    out.write(_render(report, colour=colour, top_only=getattr(args, "top", False)))
    out.write("\n")
    return 0
