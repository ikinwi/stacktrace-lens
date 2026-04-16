"""CLI sub-command: score11 – rank frames with scorer11 algorithm."""
from __future__ import annotations
import argparse
import sys
from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer11 import score_frames11


def _c(code: str, text: str, *, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def _render(report, *, colour: bool, top_n: int) -> str:
    lines = []
    header = f"score11 | {report.exception_type}: {report.exception_message}"
    lines.append(_c("1;31", header, colour=colour))
    for sf in report.ranked()[:top_n]:
        fn = sf.frame.filename or "<unknown>"
        func = sf.frame.function or "<module>"
        lineno = sf.frame.lineno or "?"
        bar = "█" * min(int(sf.score * 10), 20)
        line = f"  {_c('33', f'{fn}:{lineno}', colour=colour)} {_c('36', func, colour=colour)}  {bar} {sf.score:.3f}"
        lines.append(line)
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("score11", help="Rank frames using scorer11 algorithm")
    p.add_argument("file", nargs="?", help="Stack trace file (default: stdin)")
    p.add_argument("--top", type=int, default=10, help="Number of frames to show")
    p.add_argument("--no-colour", action="store_true")


def scorer11_command(args: argparse.Namespace) -> int:
    try:
        if getattr(args, "file", None):
            try:
                text = open(args.file).read()
            except FileNotFoundError:
                print(f"error: file not found: {args.file}", file=sys.stderr)
                return 1
        else:
            text = sys.stdin.read()
        if not text.strip():
            print("error: empty input", file=sys.stderr)
            return 1
        trace = parse_stacktrace(text)
        report = score_frames11(trace)
        colour = not getattr(args, "no_colour", False)
        print(_render(report, colour=colour, top_n=args.top))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
