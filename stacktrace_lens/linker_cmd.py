"""linker_cmd.py – CLI sub-command for frame URL linking."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.linker import LinkOptions, link_frames, format_links


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("link", help="Resolve frames to editor / file URLs")
    p.add_argument(
        "--scheme",
        choices=["file", "vscode", "pycharm", "idea"],
        default="file",
        help="URL scheme to use (default: file)",
    )
    p.add_argument(
        "--base-path",
        default=None,
        metavar="PATH",
        help="Strip this prefix from file paths before building URLs",
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to a file containing a stack trace (default: stdin)",
    )
    return p


def _read_input(file_path: str | None, err) -> tuple[str | None, int]:
    """Read raw input from a file path or stdin.

    Returns a tuple of (content, exit_code). If reading fails, content is None
    and exit_code is non-zero.
    """
    if file_path:
        try:
            return open(file_path).read(), 0
        except OSError as exc:
            print(f"error: {exc}", file=err)
            return None, 1
    return sys.stdin.read(), 0


def linker_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Execute the 'link' sub-command: parse a stack trace and print frame URLs."""
    raw, exit_code = _read_input(args.file, err)
    if exit_code != 0:
        return exit_code

    if not raw.strip():
        print("error: no input", file=err)
        return 1

    trace = parse_stacktrace(raw)
    opts = LinkOptions(scheme=args.scheme, base_path=args.base_path)
    report = link_frames(trace, opts)
    print(format_links(report), file=out)
    return 0
