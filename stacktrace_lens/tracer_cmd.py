"""CLI sub-command: tracer — build and display a trace lineage tree."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from stacktrace_lens.parser import parse_stacktrace
from stacktrace_lens.tracer import Lineage


def _build_subparser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("tracer", help="Build a lineage tree from multiple trace files")
    p.add_argument("files", nargs="*", help="Stack trace files (in lineage order)")
    p.add_argument("--labels", nargs="*", default=[], help="Labels for each trace")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Output lineage as JSON")
    return p


def _render_tree(lineage: Lineage) -> str:
    lines: List[str] = []

    def _walk(node_id: str, indent: int) -> None:
        node = lineage.get(node_id)
        if node is None:
            return
        prefix = "  " * indent + ("└─ " if indent else "")
        lbl = f" [{node.label}]" if node.label else ""
        exc = node.trace.exception_type or "?"
        lines.append(f"{prefix}{exc}{lbl} (id={node.trace_id[:8]})")
        for child_id in node.children:
            _walk(child_id, indent + 1)

    for root in lineage.roots():
        _walk(root.trace_id, 0)
    return "\n".join(lines)


def tracer_command(args: argparse.Namespace) -> int:
    files: List[str] = args.files
    labels: List[str] = list(args.labels)

    if not files:
        print("tracer: no files provided", file=sys.stderr)
        return 1

    lineage = Lineage()
    prev_id = None
    for i, path in enumerate(files):
        try:
            text = open(path).read()
        except OSError as exc:
            print(f"tracer: cannot open {path}: {exc}", file=sys.stderr)
            return 1
        trace = parse_stacktrace(text)
        if trace is None:
            print(f"tracer: no stack trace found in {path}", file=sys.stderr)
            return 1
        label = labels[i] if i < len(labels) else None
        node = lineage.add(trace, parent_id=prev_id, label=label)
        prev_id = node.trace_id

    if args.as_json:
        payload = [
            {"id": n.trace_id, "parent": n.parent_id,
             "exception": n.trace.exception_type, "label": n.label}
            for n in lineage.nodes.values()
        ]
        print(json.dumps(payload, indent=2))
    else:
        print(_render_tree(lineage))
    return 0
