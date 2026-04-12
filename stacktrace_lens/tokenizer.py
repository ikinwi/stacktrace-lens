"""Tokenizer: break a stack trace into labelled tokens for downstream processing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List

from stacktrace_lens.parser import StackTrace


class TokenKind(Enum):
    EXCEPTION_TYPE = auto()
    EXCEPTION_MESSAGE = auto()
    FILENAME = auto()
    LINE_NUMBER = auto()
    FUNCTION_NAME = auto()
    PACKAGE = auto()


@dataclass
class Token:
    kind: TokenKind
    value: str
    frame_index: int = -1  # -1 means the token belongs to the header, not a frame

    def __str__(self) -> str:  # pragma: no cover
        return f"[{self.kind.name}] {self.value!r}"


@dataclass
class TokenReport:
    tokens: List[Token] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.tokens)

    def by_kind(self, kind: TokenKind) -> List[Token]:
        return [t for t in self.tokens if t.kind == kind]

    def for_frame(self, index: int) -> List[Token]:
        return [t for t in self.tokens if t.frame_index == index]


def _package_of(filename: str) -> str:
    """Return a best-effort top-level package name from a filename."""
    parts = filename.replace("\\", "/").split("/")
    for part in parts:
        if part and not part.startswith(".") and part != "site-packages":
            return part.split(".")[0]
    return "<unknown>"


def tokenize_trace(trace: StackTrace) -> TokenReport:
    """Convert a *StackTrace* into a flat list of typed tokens."""
    tokens: List[Token] = []

    tokens.append(Token(kind=TokenKind.EXCEPTION_TYPE, value=trace.exception_type))
    tokens.append(Token(kind=TokenKind.EXCEPTION_MESSAGE, value=trace.exception_message))

    for idx, frame in enumerate(trace.frames):
        tokens.append(Token(kind=TokenKind.FILENAME, value=frame.filename, frame_index=idx))
        tokens.append(Token(kind=TokenKind.LINE_NUMBER, value=str(frame.lineno), frame_index=idx))
        tokens.append(Token(kind=TokenKind.FUNCTION_NAME, value=frame.function, frame_index=idx))
        pkg = _package_of(frame.filename)
        tokens.append(Token(kind=TokenKind.PACKAGE, value=pkg, frame_index=idx))

    return TokenReport(tokens=tokens)
