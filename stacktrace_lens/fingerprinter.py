"""Fingerprint stack traces for deduplication and identity tracking."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Optional

from .parser import StackTrace, Frame


@dataclass
class FingerprintResult:
    """Holds the computed fingerprint and contributing components."""
    fingerprint: str
    exception_type: str
    exception_message_normalized: str
    frame_signatures: List[str] = field(default_factory=list)

    def short(self, length: int = 8) -> str:
        """Return a shortened fingerprint prefix."""
        return self.fingerprint[:length]


def _normalize_message(message: str) -> str:
    """Strip memory addresses and numeric literals to improve match stability."""
    message = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", message)
    message = re.sub(r"\b\d+\b", "N", message)
    return message.strip()


def _frame_signature(frame: Frame) -> str:
    """Produce a stable string key for a single frame."""
    return f"{frame.filename}:{frame.function}"


def fingerprint_trace(
    trace: StackTrace,
    include_message: bool = True,
    max_frames: Optional[int] = None,
) -> FingerprintResult:
    """Compute a SHA-256 fingerprint for *trace*.

    Parameters
    ----------
    trace:
        The parsed stack trace to fingerprint.
    include_message:
        When *True* the normalised exception message is mixed into the hash.
    max_frames:
        If given, only the last *max_frames* frames contribute to the hash.
    """
    frames = trace.frames
    if max_frames is not None:
        frames = frames[-max_frames:]

    sigs = [_frame_signature(f) for f in frames]
    norm_msg = _normalize_message(trace.exception_message)

    parts = [trace.exception_type] + sigs
    if include_message:
        parts.append(norm_msg)

    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return FingerprintResult(
        fingerprint=digest,
        exception_type=trace.exception_type,
        exception_message_normalized=norm_msg,
        frame_signatures=sigs,
    )


def format_fingerprint(result: FingerprintResult, short: bool = False) -> str:
    """Return a human-readable string describing the fingerprint."""
    fp = result.short() if short else result.fingerprint
    lines = [
        f"Fingerprint : {fp}",
        f"Exception   : {result.exception_type}",
        f"Message     : {result.exception_message_normalized}",
        f"Frames      : {len(result.frame_signatures)}",
    ]
    return "\n".join(lines)
