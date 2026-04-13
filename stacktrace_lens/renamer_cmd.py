"""CLI sub-command: rename – apply find/replace rules to frame filenames/functions."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.renamer import RenameRule, rename_frames


def _build_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("rename", help="Rename filenames/functions inside stack frames")
    p.add_argument(
        "--rule",
        metavar="FIND:REPLACE[:TARGET]",
        action="append",
        dest="rules",
        default=[],
        help="Substitution rule. TARGET is filename|function|both (default: filename)",
    )
    p.add_argument("--file", metavar="PATH", help="Read stack trace from file instead of stdin")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    return p


def _parse_rules(raw: List[str]) -> List[RenameRule]:
    rules: List[RenameRule] = []
    for token in raw:
        parts = token.split(":", 2)
        if len(parts) < 2:
            continue
        find, replace = parts[0], parts[1]
        target = parts[2] if len(parts) == 3 else "filename"
        rules.append(RenameRule(find=find, replace=replace, target=target))
    return rules


def renamer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if args.file:
        try:
            text = open(args.file).read()
        except OSError as exc:
            err.write(f"renamer: cannot open file: {exc}\n")
            return 1
    else:
        text = sys.stdin.read()

    trace = parse_stacktrace(text)
    if trace is None:
        err.write("renamer: no valid stack trace found in input\n")
        return 1

    rules = _parse_rules(args.rules)
    report = rename_frames(trace, rules)

    use_color = not getattr(args, "no_color", False)
    cyan = "\033[36m" if use_color else ""
    reset = "\033[0m" if use_color else ""

    for rf in report.frames:
        out.write(f"{cyan}{rf}{reset}\n")

    out.write(f"\n{report.summary_line()}\n")
    return 0
