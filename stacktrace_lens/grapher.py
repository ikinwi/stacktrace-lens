"""Build a simple call-graph from one or more stack traces."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class GraphNode:
    label: str
    call_count: int = 0
    children: Dict[str, "GraphNode"] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.label} (x{self.call_count})"


@dataclass
class GraphReport:
    roots: Dict[str, GraphNode] = field(default_factory=dict)
    total_traces: int = 0
    total_edges: int = 0

    @property
    def root_count(self) -> int:
        return len(self.roots)

    def summary_line(self) -> str:
        return (
            f"{self.total_traces} trace(s), "
            f"{self.root_count} root(s), "
            f"{self.total_edges} edge(s)"
        )


def _node_label(filename: str, function: Optional[str]) -> str:
    short = filename.split("/")[-1] if filename else "<unknown>"
    func = function or "<module>"
    return f"{short}:{func}"


def build_graph(traces: List[StackTrace]) -> GraphReport:
    """Build a call-graph from a list of StackTrace objects."""
    report = GraphReport(total_traces=len(traces))

    for trace in traces:
        frames = trace.frames
        if not frames:
            continue

        # Walk frames bottom-up (index 0 = outermost caller)
        root_label = _node_label(frames[0].filename, frames[0].function)
        if root_label not in report.roots:
            report.roots[root_label] = GraphNode(label=root_label)
        node = report.roots[root_label]
        node.call_count += 1

        for frame in frames[1:]:
            child_label = _node_label(frame.filename, frame.function)
            if child_label not in node.children:
                node.children[child_label] = GraphNode(label=child_label)
                report.total_edges += 1
            node = node.children[child_label]
            node.call_count += 1

    return report


def format_graph(report: GraphReport, colour: bool = False) -> str:
    lines: List[str] = [report.summary_line(), ""]

    def _walk(node: GraphNode, indent: int) -> None:
        prefix = "  " * indent + ("└─ " if indent else "")
        lines.append(f"{prefix}{node}")
        for child in node.children.values():
            _walk(child, indent + 1)

    for root in report.roots.values():
        _walk(root, 0)

    return "\n".join(lines)
