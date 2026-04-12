"""CLI sub-command: tokenize a stack trace and display the token stream."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.tokenizer import TokenKind, TokenReport, tokenize_trace

_KIND_COLOURS = {
    TokenKind.EXCEPTION_TYPE: "\033[91m",
    TokenKind.EXCEPTION_MESSAGE: "\033[93m",
    TokenKind.FILENAME: "\033[94m",
    TokenKind.LINE_NUMBER: "\033[96m",
    TokenKind.FUNCTION_NAME: "\033[92m",
    TokenKind.PACKAGE: "\033[95m",
}
_RESET = "\033[0m"


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("tokenize", help="Tokenize a stack trace into labelled tokens")
    p.add_argument("file", nargs="?", help="Path to stack trace file (default: stdin)")
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    p.add_argument("--kind", choices=[k.name.lower() for k in TokenKind], help="Filter by token kind")
    return p


def _render(report: TokenReport, no_color: bool = False, kind_filter: str | None = None) -> str:
    lines: List[str] = []
    for token in report.tokens:
        if kind_filter and token.kind.name.lower() != kind_filter:
            continue
        label = f"{token.kind.name:<20}  fi={token.frame_index:>2}  {token.value!r}"
        if no_color:
            lines.append(label)
        else:
            colour = _KIND_COLOURS.get(token.kind, "")
            lines.append(f"{colour}{label}{_RESET}")
    return "\n".join(lines)


def tokenizer_command(args: argparse.Namespace) -> int:
    try:
        if getattr(args, "file", None):
            with open(args.file) as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not raw.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(raw)
    report = tokenize_trace(trace)
    kind_filter = getattr(args, "kind", None)
    no_color = getattr(args, "no_color", False)
    print(_render(report, no_color=no_color, kind_filter=kind_filter))
    print(f"\n{report.count} token(s) produced.")
    return 0
