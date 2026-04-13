"""CLI sub-command: patch — apply frame corrections to a stack trace."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.patcher import PatchRule, patch_trace


def _build_subparser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("patch", help="Apply line-number/filename patches to frames")
    p.add_argument(
        "--rules",
        metavar="FILE",
        help="JSON file containing a list of patch rules",
    )
    p.add_argument(
        "--line-offset",
        type=int,
        default=0,
        metavar="N",
        help="Global line-number offset applied to every frame",
    )
    p.add_argument(
        "input",
        nargs="?",
        metavar="FILE",
        help="Stack trace file (default: stdin)",
    )


def _load_rules(path: str) -> List[PatchRule]:
    with open(path) as fh:
        raw = json.load(fh)
    rules = []
    for item in raw:
        rules.append(
            PatchRule(
                filename_contains=item.get("filename_contains"),
                function_name=item.get("function_name"),
                replace_filename=item.get("replace_filename"),
                replace_function=item.get("replace_function"),
                line_offset=int(item.get("line_offset", 0)),
            )
        )
    return rules


def patcher_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        if args.input:
            with open(args.input) as fh:
                text = fh.read()
        else:
            text = sys.stdin.read()
    except OSError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if not text.strip():
        err.write("error: empty input\n")
        return 1

    trace = parse_stacktrace(text)

    rules: List[PatchRule] = []
    if getattr(args, "rules", None):
        try:
            rules = _load_rules(args.rules)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            err.write(f"error loading rules: {exc}\n")
            return 1

    if getattr(args, "line_offset", 0):
        rules.append(PatchRule(line_offset=args.line_offset))

    report = patch_trace(trace, rules)
    out.write(report.summary_line() + "\n")
    for pf in report.patched_frames:
        out.write(f"  {pf}\n")
    return 0
