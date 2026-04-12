"""CLI sub-command: categorize a stack trace."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.categorizer import categorize_trace, format_categorization


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "categorize",
        help="Categorize a stack trace into a domain bucket.",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing the stack trace (default: stdin).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit output as JSON.",
    )
    return p


def categorizer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Entry point for the *categorize* sub-command."""
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
    result = categorize_trace(trace)

    if args.json:
        import json
        payload = {
            "exception_type": result.exception_type,
            "category": result.category,
            "confidence": result.confidence,
            "notes": result.notes,
        }
        out.write(json.dumps(payload) + "\n")
    else:
        out.write(format_categorization(result) + "\n")

    return 0
