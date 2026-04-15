"""CLI sub-command: score8 – composite frame scorer (scorer8)."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .parser import parse_stacktrace
from .scorer8 import ScoreReport8, score_frames8


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def _render(report: ScoreReport8, *, colour: bool, top_n: int) -> str:
    lines: List[str] = []
    exc_label = _c(report.exception_type, "1;31", colour)
    lines.append(f"Exception : {exc_label}")
    lines.append(f"Frames    : {report.count}")
    lines.append("")
    ranked = report.ranked()[:top_n] if top_n > 0 else report.ranked()
    for sf in ranked:
        score_str = _c(f"{sf.score:.3f}", "1;33", colour)
        fn = sf.frame.function or "<module>"
        file_str = _c(sf.frame.filename or "<unknown>", "36", colour)
        fn_str = _c(fn, "32", colour)
        lines.append(f"  {score_str}  {file_str}:{sf.frame.lineno}  {fn_str}")
    top = report.top()
    if top:
        lines.append("")
        lines.append(_c(f"Best frame: {top.frame.filename}:{top.frame.lineno}  {top.frame.function or '<module>'}", "1;32", colour))
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("score8", help="composite frame scorer (v8)")
    p.add_argument("file", nargs="?", help="stack-trace file (default: stdin)")
    p.add_argument("--no-colour", action="store_true", help="disable colour output")
    p.add_argument("--top", type=int, default=0, help="show top N frames (0 = all)")
    return p


def scorer8_command(args: argparse.Namespace) -> int:
    colour = not getattr(args, "no_colour", False)
    top_n = getattr(args, "top", 0)
    try:
        if args.file:
            with open(args.file) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not raw.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = score_frames8(trace)
    print(_render(report, colour=colour, top_n=top_n))
    return 0
