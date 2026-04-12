"""CLI sub-command: mask – apply sensitive-data masking to a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .parser import parse_stacktrace
from .masker import MaskOptions, mask_trace


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("mask", help="Mask sensitive values inside a stack trace.")
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing the stack trace (reads stdin if omitted).",
    )
    p.add_argument(
        "--placeholder",
        default="***",
        help="Replacement string for masked values (default: ***).",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        metavar="REGEX",
        help="Additional regex pattern to mask (can be repeated).",
    )
    p.add_argument(
        "--mask-line-numbers",
        action="store_true",
        default=False,
        help="Replace line numbers with None.",
    )
    p.add_argument(
        "--no-default-patterns",
        action="store_true",
        default=False,
        help="Disable built-in sensitive-data patterns.",
    )
    return p


def masker_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Entry point for the *mask* sub-command.  Returns an exit code."""
    try:
        if args.file:
            try:
                raw = open(args.file).read()
            except OSError as exc:
                print(f"error: {exc}", file=err)
                return 1
        else:
            raw = sys.stdin.read()

        if not raw.strip():
            print("error: empty input", file=err)
            return 1

        trace = parse_stacktrace(raw)

        from .masker import _DEFAULT_PATTERNS  # local import to avoid circular
        patterns: List[str] = [] if args.no_default_patterns else list(_DEFAULT_PATTERNS)
        if args.patterns:
            patterns.extend(args.patterns)

        opts = MaskOptions(
            patterns=patterns,
            placeholder=args.placeholder,
            mask_line_numbers=args.mask_line_numbers,
        )
        report = mask_trace(trace, opts)

        print(f"{report.exception_type}: {report.exception_message}", file=out)
        for mf in report.frames:
            lineno = mf.masked_lineno if mf.masked_lineno is not None else "?"
            print(f'  File "{mf.masked_filename}", line {lineno}, in {mf.masked_function}', file=out)
            if mf.masked_context:
                print(f"    {mf.masked_context}", file=out)
        print(f"\n# {report.summary_line()}", file=out)
        return 0

    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=err)
        return 1
