"""CLI sub-command: score12 – rank frames using scorer12 algorithm."""
from __future__ import annotations
import argparse
import sys

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer12 import score_frames12


def _c(code: str, text: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def _render(report, colour: bool) -> str:
    lines = []
    header = f"{report.exception_type}: {report.exception_message}"
    lines.append(_c("1;31", header, colour))
    lines.append("")
    for sf in report.ranked():
        bar_len = min(int(sf.score * 20), 40)
        bar = "█" * bar_len
        fn = sf.frame.function or "<module>"
        loc = f"{sf.frame.filename}:{sf.frame.lineno}"
        lines.append(
            f"  {_c('33', f'{sf.score:.3f}', colour)} {_c('32', bar, colour)}"
            f"  {_c('36', fn, colour)}  {_c('90', loc, colour)}"
        )
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("score12", help="Rank frames with scorer12 algorithm")
    p.add_argument("file", nargs="?", help="Stacktrace file (default: stdin)")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")


def scorer12_command(args: argparse.Namespace) -> int:
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
    report = score_frames12(trace)
    colour = not getattr(args, "no_colour", False)
    print(_render(report, colour))
    return 0
