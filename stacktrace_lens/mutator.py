"""Mutator: apply in-place transformations to stack trace frames."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from stacktrace_lens.parser import Frame, StackTrace


Transform = Callable[[Frame], Frame]


@dataclass
class MutateOptions:
    strip_line_numbers: bool = False
    uppercase_filenames: bool = False
    custom_transforms: List[Transform] = field(default_factory=list)


@dataclass
class MutatedFrame:
    original: Frame
    result: Frame
    changed: bool

    def __str__(self) -> str:
        tag = "[changed]" if self.changed else "[unchanged]"
        return f"{tag} {self.result.filename}:{self.result.lineno} in {self.result.function}"


@dataclass
class MutateReport:
    frames: List[MutatedFrame]
    trace: StackTrace

    @property
    def count(self) -> int:
        return len(self.frames)

    @property
    def changed_count(self) -> int:
        return sum(1 for f in self.frames if f.changed)

    def summary_line(self) -> str:
        return (
            f"{self.changed_count}/{self.count} frame(s) mutated "
            f"({self.trace.exception_type})"
        )


def _apply_options(frame: Frame, opts: MutateOptions) -> Frame:
    filename = frame.filename
    lineno = frame.lineno
    function = frame.function
    context = frame.context

    if opts.strip_line_numbers:
        lineno = 0
    if opts.uppercase_filenames:
        filename = filename.upper()

    return Frame(filename=filename, lineno=lineno, function=function, context=context)


def mutate_trace(trace: StackTrace, opts: Optional[MutateOptions] = None) -> MutateReport:
    if opts is None:
        opts = MutateOptions()

    mutated_frames: List[MutatedFrame] = []
    new_frames: List[Frame] = []

    for frame in trace.frames:
        result = _apply_options(frame, opts)
        for transform in opts.custom_transforms:
            result = transform(result)
        changed = (
            result.filename != frame.filename
            or result.lineno != frame.lineno
            or result.function != frame.function
            or result.context != frame.context
        )
        mutated_frames.append(MutatedFrame(original=frame, result=result, changed=changed))
        new_frames.append(result)

    new_trace = StackTrace(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        frames=new_frames,
    )
    return MutateReport(frames=mutated_frames, trace=new_trace)
