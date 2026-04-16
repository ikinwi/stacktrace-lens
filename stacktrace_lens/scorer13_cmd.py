"""CLI sub-command for scorer13."""
from __future__ import annotations
import argparse
import sys
from .parser import parse_stacktrace
from .scorer13 import score_frames


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def _render(report) -> str:
    lines = [_c(f"scorer13 — {report.exception_type}", "1;33")]
    for sf in report.ranked():
        bar = "█" * min(int(sf.score * 10), 20)
        fn = sf.frame.function or "<module>"
        lines.append(
            f"  {_c(bar, '36')} {sf.score:.3f}  {_c(fn, '1')}  "
            f"{sf.frame.filename}:{sf.frame.lineno}"
        )
    top = report.top_frame
    if top:
        lines.append(_c(f"\nTop frame: {top}", "32"))
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("score13", help="Score frames (scorer13 algorithm)")
    p.add_argument("file", nargs="?", help="Stacktrace file (default: stdin)")


def scorer13_command(args: argparse.Namespace) -> int:
    path = getattr(args, "file", None)
    try:
        if path:
            with open(path) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    if not raw.strip():
        print("No input.", file=sys.stderr)
        return 1
    trace = parse_stacktrace(raw)
    report = score_frames(trace)
    print(_render(report))
    return 0
