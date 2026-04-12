"""CLI sub-command: validate a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.validator import ValidateOptions, format_validation, validate_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("validate", help="Validate a stack trace against configurable rules")
    p.add_argument("file", nargs="?", help="Path to file containing stack trace (default: stdin)")
    p.add_argument("--max-depth", type=int, default=None, metavar="N",
                   help="Fail if the trace has more than N frames")
    p.add_argument("--require-message", action="store_true",
                   help="Fail if the exception message is empty")
    p.add_argument("--allow-empty-frames", action="store_true",
                   help="Do not fail on frames with empty filename/function")
    p.add_argument("--known-types", nargs="*", metavar="TYPE",
                   help="Whitelist of allowed exception type names")
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    return p


def validator_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if getattr(args, "file", None):
        try:
            text = open(args.file).read()
        except OSError as exc:
            print(f"error: {exc}", file=err)
            return 1
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("error: no input", file=err)
        return 1

    trace = parse_stacktrace(text)

    options = ValidateOptions(
        max_depth=getattr(args, "max_depth", None),
        require_message=getattr(args, "require_message", False),
        disallow_empty_frames=not getattr(args, "allow_empty_frames", False),
        known_exception_types=getattr(args, "known_types", None),
    )

    report = validate_trace(trace, options)
    colour = not getattr(args, "no_colour", False)
    print(format_validation(report, colour=colour), file=out)
    return 0 if report.is_valid else 2
