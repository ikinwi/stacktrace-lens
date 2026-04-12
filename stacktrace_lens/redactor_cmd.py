"""CLI sub-command: redact sensitive values from a stack trace."""
from __future__ import annotations

import argparse
import re
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.redactor import RedactOptions, redact_trace
from stacktrace_lens.formatter import StackTraceFormatter, FormatOptions


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("redact", help="Redact sensitive values from a stack trace")
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing the stack trace (default: stdin)",
    )
    p.add_argument(
        "--redact-ips",
        action="store_true",
        default=False,
        help="Also redact IPv4 addresses",
    )
    p.add_argument(
        "--pattern",
        metavar="REGEX",
        action="append",
        default=[],
        dest="patterns",
        help="Extra regex pattern to redact (may be repeated)",
    )
    p.add_argument(
        "--placeholder",
        default="<REDACTED>",
        help="Replacement string for redacted values",
    )
    p.add_argument("--no-color", action="store_true", default=False)
    return p


def redactor_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
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

    extra: List[re.Pattern[str]] = []
    for p in args.patterns:
        try:
            extra.append(re.compile(p))
        except re.error as exc:
            print(f"error: invalid pattern {p!r}: {exc}", file=err)
            return 1

    opts = RedactOptions(
        redact_ips=args.redact_ips,
        extra_patterns=extra,
        placeholder=args.placeholder,
    )
    report = redact_trace(trace, opts)

    fmt = StackTraceFormatter(FormatOptions(color=not args.no_color))
    print(fmt.format(report.trace), file=out)
    print(report.summary_line(), file=out)
    return 0
