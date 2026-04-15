"""CLI sub-command: score6 — rank frames using the scorer6 algorithm."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer6 import ScoreReport6, score_frames6

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"


def _c(code: str, text: str, colour: bool) -> str:
    return f"{code}{text}{_RESET}" if colour else text


def _render(report: ScoreReport6, colour: bool, top_n: int) -> str:
    lines = []
    header = _c(_BOLD, f"Score6 Report — {report.exception_type}", colour)
    lines.append(header)
    lines.append(_c(_CYAN, f"  Frames scored : {report.count}", colour))
    ranked = report.ranked()[:top_n]
    lines.append(_c(_BOLD, "  Ranked frames:", colour))
    for sf in ranked:
        fn = sf.frame.function or "<module>"
        fname = sf.frame.filename or "<unknown>"
        bar = "#" * max(1, int(sf.score * 10))
        score_str = _c(_GREEN, f"{sf.score:.3f}", colour)
        lines.append(f"    {score_str}  {_c(_YELLOW, fn, colour)}  {fname}:{sf.frame.lineno}  {bar}")
    return "\n".join(lines)


def _build_subparser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:
    p = sub.add_parser("score6", help="Score frames using the scorer6 algorithm")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--top", type=int, default=10, help="Number of top frames to display")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    return p


def scorer6_command(args: argparse.Namespace) -> int:
    file_path: Optional[str] = getattr(args, "file", None)
    top_n: int = getattr(args, "top", 10)
    colour: bool = not getattr(args, "no_colour", False)

    if file_path:
        try:
            text = open(file_path).read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(text)
    report = score_frames6(trace)
    print(_render(report, colour=colour, top_n=top_n))
    return 0
