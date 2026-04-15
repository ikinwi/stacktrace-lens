"""collapser_cmd.py – CLI sub-command: collapse stdlib/third-party frames."""
from __future__ import annotations

import argparse
import sys

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.collapser import CollapseOptions, collapse_frames


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("collapse", help="Collapse consecutive stdlib/third-party frames")
    p.add_argument("--no-stdlib", action="store_true", help="Do not collapse stdlib frames")
    p.add_argument("--third-party", action="store_true", help="Also collapse third-party frames")
    p.add_argument("--min-run", type=int, default=2, metavar="N",
                   help="Minimum consecutive frames to trigger collapse (default: 2)")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    return p


def collapser_command(args: argparse.Namespace) -> int:
    try:
        if getattr(args, "file", None):
            try:
                text = open(args.file).read()
            except FileNotFoundError:
                print(f"error: file not found: {args.file}", file=sys.stderr)
                return 1
        else:
            text = sys.stdin.read()
    except Exception as exc:  # pragma: no cover
        print(f"error reading input: {exc}", file=sys.stderr)
        return 1

    if not text.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    trace = parse_stacktrace(text)
    opts = CollapseOptions(
        collapse_stdlib=not args.no_stdlib,
        collapse_third_party=args.third_party,
        min_run=args.min_run,
    )
    report = collapse_frames(trace, opts)

    print(f"Exception : {trace.exception_type}: {trace.exception_message}")
    print(report.summary_line())
    print()
    for cf in report.frames:
        if cf.is_collapsed:
            print(f"  ... {cf}")
        else:
            f = cf.frame
            print(f"  {f.filename}:{f.lineno} in {f.function or '<module>'}")

    return 0
