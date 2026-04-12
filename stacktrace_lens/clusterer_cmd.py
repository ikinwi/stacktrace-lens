"""CLI sub-command: cluster — group traces by structural similarity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import StackTrace, parse_stacktrace
from stacktrace_lens.clusterer import cluster_traces, format_cluster_report


def _build_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("cluster", help="Group stack traces by structural similarity")
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Plain-text files each containing one stack trace",
    )
    p.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable ANSI colour codes",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="as_json",
        help="Emit result as JSON",
    )


def _load_traces(files: List[str]) -> List[StackTrace]:
    """Read and parse stack traces from the given file paths.

    Skips files whose content cannot be parsed as a valid stack trace and
    prints a warning to stderr so the caller is aware of the omission.
    Exits with status 1 if a file does not exist.
    """
    traces: List[StackTrace] = []
    for path_str in files:
        p = Path(path_str)
        if not p.exists():
            print(f"error: file not found: {path_str}", file=sys.stderr)
            sys.exit(1)
        text = p.read_text(encoding="utf-8")
        trace = parse_stacktrace(text)
        if trace is not None:
            traces.append(trace)
        else:
            print(f"warning: could not parse stack trace from '{path_str}', skipping", file=sys.stderr)
    return traces


def clusterer_command(args: argparse.Namespace) -> int:
    traces = _load_traces(args.files)
    if not traces:
        print("error: no valid stack traces found in provided files", file=sys.stderr)
        return 1

    report = cluster_traces(traces)

    if args.as_json:
        data = {
            "total_traces": report.total_traces,
            "total_clusters": report.total_clusters,
            "clusters": [
                {
                    "fingerprint": e.fingerprint,
                    "count": e.count,
                    "exception_type": e.representative.exception_type,
                    "exception_message": e.representative.exception_message,
                }
                for e in report.ranked()
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        colour = not args.no_colour
        print(format_cluster_report(report, colour=colour))

    return 0
