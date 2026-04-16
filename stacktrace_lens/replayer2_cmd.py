"""CLI sub-command: replay2 — replay stack traces with filtering options."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import StackTrace, parse_stacktrace
from stacktrace_lens.replayer2 import ReplayOptions, replay_traces


def _build_subparser(sub: argparse.Action) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("replay2", help="Replay stack traces with filtering")
    p.add_argument("files", nargs="*", help="JSON trace files to replay")
    p.add_argument("--max-events", type=int, default=None, help="Limit number of events")
    p.add_argument("--skip-duplicates", action="store_true", help="Skip duplicate traces")
    p.add_argument("--reverse", action="store_true", help="Replay in reverse order")
    return p


def _load_trace(path: str) -> StackTrace:
    """Load a stack trace from a JSON file.

    The JSON file is expected to contain a ``raw`` key whose value is the
    raw stack trace string to be parsed.

    Raises:
        FileNotFoundError: If *path* does not exist.
        KeyError: If the JSON object has no ``raw`` key.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    data = json.loads(Path(path).read_text())
    raw = data.get("raw", "")
    return parse_stacktrace(raw)


def replayer2_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    if not args.files:
        err.write("replay2: no input files provided\n")
        return 1

    traces: List[StackTrace] = []
    for f in args.files:
        try:
            traces.append(_load_trace(f))
        except FileNotFoundError:
            err.write(f"replay2: file not found: {f}\n")
            return 1
        except json.JSONDecodeError as exc:
            err.write(f"replay2: invalid JSON in {f}: {exc}\n")
            return 1
        except Exception as exc:  # noqa: BLE001
            err.write(f"replay2: failed to load {f}: {exc}\n")
            return 1

    opts = ReplayOptions(
        max_events=args.max_events,
        skip_duplicates=args.skip_duplicates,
        reverse=args.reverse,
    )
    report = replay_traces(traces, opts)

    out.write(report.summary_line() + "\n")
    for event in report.events:
        out.write(str(event) + "\n")

    return 0
