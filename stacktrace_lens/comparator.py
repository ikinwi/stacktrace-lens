"""Compare two stack traces and highlight differences."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .parser import Frame, StackTrace


@dataclass
class FrameDiff:
    """Represents a single frame-level difference between two traces."""
    kind: str          # 'added', 'removed', or 'changed'
    left: Optional[Frame]
    right: Optional[Frame]


@dataclass
class TraceDiff:
    """Result of comparing two StackTrace objects."""
    left_exception: str
    right_exception: str
    left_message: str
    right_message: str
    exception_changed: bool
    message_changed: bool
    frame_diffs: List[FrameDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return (
            self.exception_changed
            or self.message_changed
            or bool(self.frame_diffs)
        )

    @property
    def added_count(self) -> int:
        return sum(1 for d in self.frame_diffs if d.kind == "added")

    @property
    def removed_count(self) -> int:
        return sum(1 for d in self.frame_diffs if d.kind == "removed")


def _frame_key(frame: Frame) -> Tuple[str, str, int]:
    return (frame.filename, frame.function, frame.lineno)


def compare_traces(left: StackTrace, right: StackTrace) -> TraceDiff:
    """Compare two stack traces and return a TraceDiff describing changes."""
    exception_changed = left.exception_type != right.exception_type
    message_changed = left.exception_message != right.exception_message

    left_keys = [_frame_key(f) for f in left.frames]
    right_keys = [_frame_key(f) for f in right.frames]

    left_set = set(left_keys)
    right_set = set(right_keys)

    frame_diffs: List[FrameDiff] = []

    left_by_key = {_frame_key(f): f for f in left.frames}
    right_by_key = {_frame_key(f): f for f in right.frames}

    for key in left_keys:
        if key not in right_set:
            frame_diffs.append(FrameDiff(kind="removed", left=left_by_key[key], right=None))

    for key in right_keys:
        if key not in left_set:
            frame_diffs.append(FrameDiff(kind="added", left=None, right=right_by_key[key]))

    return TraceDiff(
        left_exception=left.exception_type,
        right_exception=right.exception_type,
        left_message=left.exception_message,
        right_message=right.exception_message,
        exception_changed=exception_changed,
        message_changed=message_changed,
        frame_diffs=frame_diffs,
    )


def format_diff(diff: TraceDiff, colour: bool = True) -> str:
    """Render a TraceDiff as a human-readable string."""
    RED = "\033[31m" if colour else ""
    GREEN = "\033[32m" if colour else ""
    YELLOW = "\033[33m" if colour else ""
    RESET = "\033[0m" if colour else ""

    lines: List[str] = []
    if not diff.has_differences:
        lines.append("No differences found between the two traces.")
        return "\n".join(lines)

    if diff.exception_changed:
        lines.append(f"{RED}- Exception: {diff.left_exception}{RESET}")
        lines.append(f"{GREEN}+ Exception: {diff.right_exception}{RESET}")
    else:
        lines.append(f"  Exception: {diff.left_exception}")

    if diff.message_changed:
        lines.append(f"{RED}- Message: {diff.left_message}{RESET}")
        lines.append(f"{GREEN}+ Message: {diff.right_message}{RESET}")

    if diff.frame_diffs:
        lines.append("")
        lines.append(f"{YELLOW}Frame differences:{RESET}")
        for fd in diff.frame_diffs:
            if fd.kind == "removed" and fd.left:
                lines.append(
                    f"  {RED}- {fd.left.filename}:{fd.left.lineno} in {fd.left.function}{RESET}"
                )
            elif fd.kind == "added" and fd.right:
                lines.append(
                    f"  {GREEN}+ {fd.right.filename}:{fd.right.lineno} in {fd.right.function}{RESET}"
                )

    return "\n".join(lines)
