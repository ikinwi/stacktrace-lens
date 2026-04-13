"""chainer_cmd.py – CLI sub-command: chain  (detect exception chains)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from stacktrace_lens.parser import parse_stacktrace, StackTrace
from stacktrace_lens.chainer import chain_traces, format_chain


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("chain", help="Detect and display exception chains.")
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="JSON files produced by the splitter command (one trace per file). "
             "Reads from stdin when no files are given.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour output.",
    )
    return p


def _load_trace(path: str) -> StackTrace:
    data = json.loads(Path(path).read_text())
    raw = data.get("raw", "")
    return parse_stacktrace(raw)


def chainer_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    traces: List[StackTrace] = []

    if args.files:
        for fpath in args.files:
            p = Path(fpath)
            if not p.exists():
                err.write(f"error: file not found: {fpath}\n")
                return 1
            try:
                traces.append(_load_trace(fpath))
            except Exception as exc:  # noqa: BLE001
                err.write(f"error: could not load {fpath}: {exc}\n")
                return 1
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            err.write("error: no input provided\n")
            return 1
        traces.append(parse_stacktrace(raw))

    if not traces:
        err.write("error: no traces loaded\n")
        return 1

    report = chain_traces(traces)
    out.write(format_chain(report) + "\n")
    return 0
