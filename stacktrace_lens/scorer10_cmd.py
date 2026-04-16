"""CLI sub-command: score10 – rank frames with scorer10."""
from __future__ import annotations
import argparse
import sys
from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer10 import score_frames


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def _render(report) -> str:
    lines = [
        _c(f"Exception: {report.exception_type}", "1;31"),
        _c(f"Frames scored: {report.count}", "33"),
        "",
    ]
    for sf in report.ranked():
        fn = sf.frame.function or "<module>"
        bar_len = int(sf.score * 20)
        bar = _c("█" * bar_len, "32") + _c("░" * (20 - bar_len), "90")
        lines.append(
            f"  {bar} {_c(f'{sf.score:.3f}', '1;32')}  "
            f"{_c(sf.frame.filename, '36')}:{sf.frame.lineno} "
            f"in {_c(fn, '35')}"
        )
    top = report.top()
    if top:
        lines += ["", _c("Top frame:", "1;33"), f"  {top}"]
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("score10", help="Rank frames using entropy+depth composite scorer")
    p.add_argument("file", nargs="?", help="Stacktrace file (default: stdin)")


def scorer10_command(args: argparse.Namespace) -> int:
    path = getattr(args, "file", None)
    if path:
        try:
            text = open(path).read()
        except OSError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("Error: no input", file=sys.stderr)
        return 1
    trace = parse_stacktrace(text)
    report = score_frames(trace)
    print(_render(report))
    return 0
