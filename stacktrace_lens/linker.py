"""linker.py – resolve stack frames to clickable file:// or editor URLs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import Frame, StackTrace


@dataclass
class LinkOptions:
    scheme: str = "file"          # 'file', 'vscode', 'pycharm', 'idea'
    base_path: Optional[str] = None  # strip this prefix before building URL


@dataclass
class LinkedFrame:
    frame: Frame
    url: Optional[str]

    def __str__(self) -> str:
        loc = f"{self.frame.filename}:{self.frame.lineno}"
        if self.url:
            return f"{loc} -> {self.url}"
        return loc


@dataclass
class LinkReport:
    frames: List[LinkedFrame] = field(default_factory=list)
    scheme: str = "file"

    @property
    def linked_count(self) -> int:
        return sum(1 for f in self.frames if f.url is not None)

    @property
    def total(self) -> int:
        return len(self.frames)

    def summary_line(self) -> str:
        return f"{self.linked_count}/{self.total} frames linked ({self.scheme})"


def _build_url(frame: Frame, opts: LinkOptions) -> Optional[str]:
    path = frame.filename
    if not path or path == "<unknown>":
        return None

    if opts.base_path and path.startswith(opts.base_path):
        path = path[len(opts.base_path):].lstrip("/")

    lineno = frame.lineno if frame.lineno is not None else 1

    if opts.scheme == "file":
        return f"file://{path}#{lineno}"
    if opts.scheme == "vscode":
        return f"vscode://file/{path}:{lineno}"
    if opts.scheme in ("pycharm", "idea"):
        return f"idea://open?file={path}&line={lineno}"
    return None


def link_frames(trace: StackTrace, opts: Optional[LinkOptions] = None) -> LinkReport:
    if opts is None:
        opts = LinkOptions()
    linked = [LinkedFrame(frame=f, url=_build_url(f, opts)) for f in trace.frames]
    return LinkReport(frames=linked, scheme=opts.scheme)


def format_links(report: LinkReport) -> str:
    lines = [report.summary_line()]
    for lf in report.frames:
        lines.append(f"  {lf}")
    return "\n".join(lines)
