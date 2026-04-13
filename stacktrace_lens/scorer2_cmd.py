"""CLI sub-command: score2 — relevance-score every frame in a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import IO

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer2 import ScoreReport2, score_frames


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("score2", help="Relevance-score frames in a stack trace")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("-n", "--top", type=int, default=0, help="Show only top N frames (0 = all)")
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    return p


def _render(report: ScoreReport2, top_n: int, color: bool, out: IO[str]) -> None:
    def _c(code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if color else text

    frames = report.top(top_n) if top_n > 0 else report.frames
    out.write(_c("1", f"Scored {report.count} frame(s)\n"))
    for sf in frames:
        bar_len = int(sf.score * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        score_str = _c("32", f"{sf.score:.2f}") if sf.score >= 0.6 else _c("33", f"{sf.score:.2f}")
        fn = sf.frame.filename or "<unknown>"
        func = sf.frame.function or "<unknown>"
        lineno = sf.frame.lineno or 0
        out.write(f"  [{bar}] {score_str}  {fn}:{lineno} in {func}\n")


def scorer2_command(args: argparse.Namespace, out: IO[str] = sys.stdout) -> int:
    raw: str
    if args.file:
        try:
            with open(args.file) as fh:
                raw = fh.read()
        except FileNotFoundError:
            out.write(f"error: file not found: {args.file}\n")
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        out.write("error: no input provided\n")
        return 1

    trace = parse_stacktrace(raw)
    report = score_frames(trace)
    _render(report, top_n=args.top, color=not args.no_color, out=out)
    return 0
