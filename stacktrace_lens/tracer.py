"""Trace lineage: track parent-child relationships between stack traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

from stacktrace_lens.parser import StackTrace


@dataclass
class TraceNode:
    """A single node in the trace lineage tree."""
    trace_id: str
    trace: StackTrace
    parent_id: Optional[str] = None
    label: Optional[str] = None
    children: List[str] = field(default_factory=list)

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    @property
    def depth(self) -> int:
        return 0 if self.is_root else -1  # resolved by Lineage


@dataclass
class Lineage:
    """A tree of related stack traces."""
    nodes: Dict[str, TraceNode] = field(default_factory=dict)

    def add(self, trace: StackTrace, parent_id: Optional[str] = None,
            label: Optional[str] = None) -> TraceNode:
        """Add a trace to the lineage and return its node."""
        trace_id = str(uuid.uuid4())
        node = TraceNode(trace_id=trace_id, trace=trace,
                         parent_id=parent_id, label=label)
        self.nodes[trace_id] = node
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(trace_id)
        return node

    def get(self, trace_id: str) -> Optional[TraceNode]:
        return self.nodes.get(trace_id)

    def roots(self) -> List[TraceNode]:
        return [n for n in self.nodes.values() if n.is_root]

    def ancestors(self, trace_id: str) -> List[TraceNode]:
        """Return ancestor nodes from root to parent."""
        result: List[TraceNode] = []
        node = self.nodes.get(trace_id)
        if node is None:
            return result
        current_id = node.parent_id
        while current_id:
            parent = self.nodes.get(current_id)
            if parent is None:
                break
            result.insert(0, parent)
            current_id = parent.parent_id
        return result

    def depth_of(self, trace_id: str) -> int:
        return len(self.ancestors(trace_id))

    def size(self) -> int:
        return len(self.nodes)
