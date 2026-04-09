"""Parser module for extracting structured data from Python stack traces."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Frame:
    """Represents a single frame in a Python stack trace."""
    file_path: str
    line_number: int
    function_name: str
    source_line: Optional[str] = None


@dataclass
class StackTrace:
    """Represents a parsed Python stack trace."""
    exception_type: str
    exception_message: str
    frames: list[Frame] = field(default_factory=list)


# Regex patterns for parsing stack trace components
_FRAME_HEADER_RE = re.compile(
    r'^\s*File "(?P<file>.+?)", line (?P<line>\d+), in (?P<func>.+)$'
)
_EXCEPTION_RE = re.compile(
    r'^(?P<type>[\w\.]+(?:Error|Exception|Warning|KeyboardInterrupt|SystemExit|GeneratorExit|StopIteration|StopAsyncIteration|BaseException|\w+)):\s*(?P<msg>.*)$'
)


def parse_stacktrace(text: str) -> Optional[StackTrace]:
    """Parse a raw Python stack trace string into a StackTrace object.

    Args:
        text: Raw stack trace text (e.g. from stderr or a log file).

    Returns:
        A StackTrace instance, or None if no valid trace was detected.
    """
    lines = text.strip().splitlines()
    frames: list[Frame] = []
    exception_type = ""
    exception_message = ""

    i = 0
    while i < len(lines):
        frame_match = _FRAME_HEADER_RE.match(lines[i])
        if frame_match:
            file_path = frame_match.group("file")
            line_number = int(frame_match.group("line"))
            function_name = frame_match.group("func")
            source_line = None
            if i + 1 < len(lines) and not _FRAME_HEADER_RE.match(lines[i + 1]):
                candidate = lines[i + 1].strip()
                if candidate and not _EXCEPTION_RE.match(candidate):
                    source_line = candidate
                    i += 1
            frames.append(Frame(file_path, line_number, function_name, source_line))
        else:
            exc_match = _EXCEPTION_RE.match(lines[i])
            if exc_match:
                exception_type = exc_match.group("type")
                exception_message = exc_match.group("msg").strip()
        i += 1

    if not exception_type:
        return None

    return StackTrace(
        exception_type=exception_type,
        exception_message=exception_message,
        frames=frames,
    )
