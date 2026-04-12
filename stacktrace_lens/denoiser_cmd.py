"""CLI sub-command: denoise  – strip low-signal frames from a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.denoiser import DenoiseOptions, denoise_trace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "denoise",
        help="Remove test-runner / import-machinery noise frames from a trace.",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="Path to a file containing the stack trace (default: stdin).",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Extra regex pattern to treat as noise (repeatable).",
    )
    p.add_argument(
        "--no-fallback",
        dest="no_fallback",
        action="store_true",
        help="Do NOT keep all frames when every frame is noisy.",
    )
    return p


def denoiser_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Entry-point for the *denoise* sub-command.  Returns an exit code."""
    if getattr(args, "file", None):
        try:
            with open(args.file) as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=err)
            return 1
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        print("error: no input provided", file=err)
        return 1

    trace = parse_stacktrace(raw)
    options = DenoiseOptions(
        extra_patterns=list(args.patterns),
        keep_if_only_noise=not args.no_fallback,
    )
    report = denoise_trace(trace, options)

    print(report.summary_line(), file=out)
    print(f"Exception : {report.trace.exception_type}", file=out)
    print(f"Message   : {report.trace.exception_message}", file=out)
    if report.removed_count:
        print("\nRemoved frames:", file=out)
        for frame in report.removed_frames:
            print(f"  {frame.filename}:{frame.lineno} in {frame.function}", file=out)
    print("\nKept frames:", file=out)
    for frame in report.trace.frames:
        print(f"  {frame.filename}:{frame.lineno} in {frame.function}", file=out)
    return 0
