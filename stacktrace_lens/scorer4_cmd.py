"""CLI sub-command: score4 — rank frames by composite score."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from .parser import parse_stacktrace
from .scorer4 import score_frames4


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("score4", help="Rank frames using composite scoring (v4)")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--top", type=int, default=0, help="Show only top N frames")
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    return p


def _c(text: str, code: str, no_color: bool) -> str:
    if no_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def _render(report, top: int, no_color: bool) -> str:
    lines = []
    header = _c(f"Exception: {report.exception_type}", "1;31", no_color)
    weight_str = _c(f"weight={report.exception_weight:.2f}", "33", no_color)
    lines.append(f"{header}  {weight_str}")
    frames = report.ranked()
    if top > 0:
        frames = frames[:top]
    for sf in frames:
        fn = _c(sf.frame.function or "<module>", "36", no_color)
        loc = _c(f"{sf.frame.filename}:{sf.frame.lineno}", "90", no_color)
        score = _c(f"{sf.score:.4f}", "32", no_color)
        lines.append(f"  {fn}  {loc}  score={score}")
    return "\n".join(lines)


def scorer4_command(args: argparse.Namespace) -> int:
    raw: Optional[str] = None
    if getattr(args, "file", None):
        try:
            with open(args.file) as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        raw = sys.stdin.read()

    if not raw or not raw.strip():
        print("error: no input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = score_frames4(trace)
    no_color = getattr(args, "no_color", False)
    top = getattr(args, "top", 0)
    print(_render(report, top, no_color))
    return 0
