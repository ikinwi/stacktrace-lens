"""CLI sub-command: classify — categorise a stack trace by exception type."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from stacktrace_lens.classifier import classify_trace, format_classification
from stacktrace_lens.parser import parse_stacktrace


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "classify",
        help="Classify a stack trace into a broad error category.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit result as JSON instead of plain text.",
    )
    return p


def classifier_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Entry point for the classify sub-command. Returns an exit code."""
    raw: Optional[str] = None

    if args.file:
        try:
            with open(args.file) as fh:
                raw = fh.read()
        except OSError as exc:
            err.write(f"error: {exc}\n")
            return 1
    else:
        raw = sys.stdin.read()

    if not raw or not raw.strip():
        err.write("error: no input provided\n")
        return 1

    trace = parse_stacktrace(raw)
    result = classify_trace(trace)

    if getattr(args, "json", False):
        import json
        payload = {
            "exception_type": result.exception_type,
            "category": result.category,
            "confidence": result.confidence,
            "note": result.note,
        }
        out.write(json.dumps(payload, indent=2) + "\n")
    else:
        out.write(format_classification(result) + "\n")

    return 0
