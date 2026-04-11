"""CLI sub-command: score — rank frames by root-cause relevance."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer import ScoreReport, score_frames


def _build_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "score",
        help="Rank stack frames by root-cause relevance.",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="Path to a file containing a Python traceback (default: stdin).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top N frames (0 = all).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )


def _render(report: ScoreReport, top: int, color: bool) -> str:
    GREEN = "\033[32m" if color else ""
    YELLOW = "\033[33m" if color else ""
    RED = "\033[31m" if color else ""
    RESET = "\033[0m" if color else ""
    BOLD = "\033[1m" if color else ""

    lines: List[str] = [f"{BOLD}Frame Relevance Scores{RESET}"]
    ranked = report.ranked
    if top:
        ranked = ranked[:top]
    for sf in ranked:
        if sf.score >= 0.6:
            colour = GREEN
        elif sf.score >= 0.2:
            colour = YELLOW
        else:
            colour = RED
        lines.append(
            f"  {colour}{sf.score:+.3f}{RESET}  "
            f"{sf.frame.filename}:{sf.frame.lineno}  "
            f"in {sf.frame.function}  [{sf.reason}]"
        )
    return "\n".join(lines)


def scorer_command(args: argparse.Namespace) -> int:
    try:
        if getattr(args, "file", None):
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
    report = score_frames(trace)
    color = not getattr(args, "no_color", False)
    print(_render(report, top=getattr(args, "top", 0), color=color))
    return 0
