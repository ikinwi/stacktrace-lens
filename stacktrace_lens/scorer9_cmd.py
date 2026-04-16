"""CLI sub-command: score9 — composite frame scorer."""
from __future__ import annotations

import argparse
import sys

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.scorer9 import score_frames9


def _c(code: str, text: str, use_colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if use_colour else text


def _render(report, use_colour: bool) -> str:
    lines = []
    exc = report.exception_type
    msg = report.exception_message
    lines.append(_c("1;31", f"{exc}: {msg}", use_colour))
    lines.append("")
    for sf in report.ranked:
        fn = sf.frame.function or "<module>"
        fname = sf.frame.filename or "<unknown>"
        lineno = sf.frame.lineno or 0
        bar_len = min(int(sf.score * 10), 40)
        bar = _c("32", "█" * bar_len, use_colour)
        label = _c("33", f"{sf.score:.3f}", use_colour)
        lines.append(f"  {label} {bar}")
        lines.append(f"         {_c('36', fn, use_colour)} @ {fname}:{lineno}")
    return "\n".join(lines)


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = sub.add_parser("score9", help="Composite frame scorer (scorer9)")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    return p


def scorer9_command(args: argparse.Namespace) -> int:
    file_arg = getattr(args, "file", None)
    try:
        if file_arg:
            with open(file_arg) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError:
        print(f"error: file not found: {file_arg}", file=sys.stderr)
        return 1

    if not raw.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = score_frames9(trace)
    use_colour = not getattr(args, "no_colour", False)
    print(_render(report, use_colour))
    return 0
