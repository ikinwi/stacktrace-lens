"""CLI sub-command: resolve file paths inside a stack trace."""

from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.resolver import ResolveOptions, format_resolve_report, resolve_frames


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("resolve", help="Resolve relative file paths in a stack trace")
    p.add_argument("file", nargs="?", help="Path to stack trace file (default: stdin)")
    p.add_argument(
        "-s",
        "--search-path",
        dest="search_paths",
        action="append",
        default=[],
        metavar="DIR",
        help="Directory to search for source files (repeatable)",
    )
    p.add_argument(
        "--symlinks",
        dest="resolve_symlinks",
        action="store_true",
        default=False,
        help="Resolve symbolic links to their real path",
    )
    return p


def resolver_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if getattr(args, "file", None):
            try:
                text = open(args.file).read()
            except FileNotFoundError:
                err.write(f"error: file not found: {args.file}\n")
                return 1
        else:
            text = sys.stdin.read()

        if not text.strip():
            err.write("error: no input\n")
            return 1

        trace = parse_stacktrace(text)
        options = ResolveOptions(
            search_paths=args.search_paths or [],
            resolve_symlinks=args.resolve_symlinks,
        )
        report = resolve_frames(trace, options)
        out.write(format_resolve_report(report))
        out.write("\n")
        return 0
    except Exception as exc:  # pragma: no cover
        err.write(f"error: {exc}\n")
        return 1
