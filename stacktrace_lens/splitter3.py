"""Split a stack trace into logical segments based on package boundaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace


def _package_of(filename: str) -> str:
    """Return the top-level package name from a file path."""
    if not filename:
        return "<unknown>"
    parts = filename.replace("\\", "/").split("/")
    for part in parts:
        if part and part != "." and not part.startswith("<"):
            return part
    return "<unknown>"


@dataclass
class Partition:
    package: str
    frames: List[Frame] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.frames)

    def __str__(self) -> str:
        return f"Partition({self.package!r}, frames={self.count})"


@dataclass
class PartitionReport:
    trace: StackTrace
    partitions: List[Partition] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.partitions)

    @property
    def summary_line(self) -> str:
        return (
            f"{self.count} partition(s) from "
            f"{len(self.trace.frames)} frame(s) "
            f"[{self.trace.exception_type}]"
        )


def partition_trace(trace: StackTrace) -> PartitionReport:
    """Group consecutive frames by top-level package into Partition objects."""
    partitions: List[Partition] = []
    for frame in trace.frames:
        pkg = _package_of(frame.filename or "")
        if partitions and partitions[-1].package == pkg:
            partitions[-1].frames.append(frame)
        else:
            partitions.append(Partition(package=pkg, frames=[frame]))
    return PartitionReport(trace=trace, partitions=partitions)
