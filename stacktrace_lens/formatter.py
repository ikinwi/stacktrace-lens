"""Color-coded formatter for parsed stack traces."""

from dataclasses import dataclass
from typing import Optional

from stacktrace_lens.parser import StackTrace, Frame

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
GREEN = "\033[32m"
DIM = "\033[2m"
MAGENTA = "\033[35m"


@dataclass
class FormatOptions:
    color: bool = True
    show_locals: bool = False
    max_frames: Optional[int] = None
    indent: int = 2


class StackTraceFormatter:
    def __init__(self, options: Optional[FormatOptions] = None):
        self.options = options or FormatOptions()

    def _c(self, code: str, text: str) -> str:
        """Apply color code if color is enabled."""
        if not self.options.color:
            return text
        return f"{code}{text}{RESET}"

    def format_frame(self, frame: Frame, index: int) -> str:
        indent = " " * self.options.indent
        lines = []

        location = f"{frame.filename}:{frame.lineno}"
        header = (
            f"{indent}{self._c(DIM, f'[{index}]')} "
            f"{self._c(CYAN, location)} "
            f"in {self._c(GREEN, frame.function)}"
        )
        lines.append(header)

        if frame.code_line:
            code = frame.code_line.strip()
            lines.append(f"{indent}    {self._c(YELLOW, code)}")

        return "\n".join(lines)

    def format(self, stacktrace: StackTrace) -> str:
        lines = []

        lines.append(self._c(BOLD + RED, "Traceback (most recent call last):"))

        frames = stacktrace.frames
        if self.options.max_frames is not None:
            frames = frames[: self.options.max_frames]

        for i, frame in enumerate(frames):
            lines.append(self.format_frame(frame, i))

        exception_line = f"{self._c(BOLD + RED, stacktrace.exception_type)}"
        if stacktrace.exception_message:
            exception_line += f": {self._c(RED, stacktrace.exception_message)}"
        lines.append(exception_line)

        return "\n".join(lines)


def format_stacktrace(
    stacktrace: StackTrace, options: Optional[FormatOptions] = None
) -> str:
    """Convenience function to format a StackTrace object."""
    formatter = StackTraceFormatter(options)
    return formatter.format(stacktrace)
