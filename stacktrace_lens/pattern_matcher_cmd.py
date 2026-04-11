"""CLI sub-command: pattern-match — find frames matching user-supplied patterns."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.pattern_matcher import format_report, match_frames


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("pattern-match", help="Highlight frames that match regex patterns")
    p.add_argument("files", nargs="*", metavar="FILE", help="Stack-trace files (default: stdin)")
    p.add_argument(
        "-p",
        "--pattern",
        dest="patterns",
        metavar="LABEL=REGEX",
        action="append",
        default=[],
        help="Pattern in LABEL=REGEX form; may be repeated",
    )
    p.add_argument("--no-colour", action="store_true", help="Disable colour output")
    p.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON instead of text")
    return p


def _parse_patterns(raw: List[str]) -> dict:
    patterns: dict = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Pattern must be LABEL=REGEX, got: {item!r}")
        label, _, regex = item.partition("=")
        patterns[label.strip()] = regex.strip()
    return patterns


def pattern_match_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        patterns = _parse_patterns(args.patterns)
    except ValueError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if not patterns:
        err.write("error: supply at least one --pattern LABEL=REGEX\n")
        return 1

    sources = args.files if args.files else ["-"]
    colour = not args.no_colour

    for source in sources:
        try:
            raw = sys.stdin.read() if source == "-" else open(source).read()
        except OSError as exc:
            err.write(f"error: {exc}\n")
            return 1

        if not raw.strip():
            err.write("error: empty input\n")
            return 1

        trace = parse_stacktrace(raw)
        report = match_frames(trace, patterns)

        if args.as_json:
            payload = {
                "total_frames": report.total_frames,
                "matched_frames": report.matched_frames,
                "match_ratio": round(report.match_ratio, 4),
                "matches": [
                    {"label": m.label, "filename": m.frame.filename,
                     "lineno": m.frame.lineno, "function": m.frame.function}
                    for m in report.matches
                ],
            }
            out.write(json.dumps(payload, indent=2) + "\n")
        else:
            out.write(format_report(report, colour=colour) + "\n")

    return 0
