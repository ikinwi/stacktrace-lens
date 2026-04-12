"""CLI sub-command: trim — remove noise frames from a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.trimmer import TrimOptions, trim_trace
from stacktrace_lens.formatter import StackTraceFormatter, FormatOptions


def _build_subparser(subparsers) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("trim", help="Trim noise frames from a stack trace")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    p.add_argument("--strip-top", type=int, default=0, metavar="N",
                   help="Remove N frames from the top (outermost)")
    p.add_argument("--strip-bottom", type=int, default=0, metavar="N",
                   help="Remove N frames from the bottom (innermost)")
    p.add_argument("--drop-prefix", default=None, metavar="PREFIX",
                   help="Drop frames whose filename starts with PREFIX")
    p.add_argument("--drop-suffix", default=None, metavar="SUFFIX",
                   help="Drop frames whose filename ends with SUFFIX")
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    p.add_argument("--summary", action="store_true", help="Print trim summary line")
    return p


def trimmer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Execute the trim sub-command. Returns exit code."""
    if args.file:
        try:
            raw = open(args.file).read()
        except OSError as exc:
            print(f"error: {exc}", file=err)
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print("error: no input", file=err)
        return 1

    trace = parse_stacktrace(raw)
    options = TrimOptions(
        strip_top=args.strip_top,
        strip_bottom=args.strip_bottom,
        drop_prefix=args.drop_prefix,
        drop_suffix=args.drop_suffix,
    )
    report = trim_trace(trace, options)

    if args.summary:
        print(report.summary_line(), file=out)

    fmt_opts = FormatOptions(color=not args.no_color)
    formatter = StackTraceFormatter(fmt_opts)
    print(formatter.format(report.trace), file=out)
    return 0
