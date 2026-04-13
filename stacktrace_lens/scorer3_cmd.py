"""CLI sub-command: score3 — rank frames by recency."""
from __future__ import annotations

import argparse
import sys
from typing import List

from .parser import parse_stacktrace
from .scorer3 import ScoreReport3, score_frames3


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("score3", help="Rank frames by recency (proximity to exception).")
    p.add_argument("file", nargs="?", help="Stack-trace file (default: stdin).")
    p.add_argument("--top", type=int, default=0, metavar="N",
                   help="Show only the top N frames (0 = all).")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colour output.")
    return p


def _c(text: str, code: str, no_color: bool) -> str:
    if no_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def _render top: int, no_color: bool) -> str:
    frames = report.ranked()
    if top > 0:
        frames = frames[:top]
    lines:    lines.append(_c(report.summary_line(), "1", no_color))
    for sf in frames:
        score_str = _c(f"{sf.score:.4f}", "33", no_color)
        fn = _c(sf.frame.filename or "<unknown>", "36", no_color)
        func = _c(sf.frame.function or "<module>", "32", no_color)
        lineno = sf.frame.lineno if sf.frame.lineno is not None else "?"
        lines.append(f"  {score_str}  {fn}:{lineno} in {func}")
    return "\n".join(lines)


def scorer3_command(args: argparse.Namespace) -> int:
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
    report = score_frames3(trace)
    no_color = getattr(args, "no_color", False)
    top = getattr(args, "top", 0)
    print(_render(report, top, no_color))
    return 0
