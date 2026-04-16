"""bouncer.py – rate-limit / reject traces that exceed configurable thresholds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class BounceOptions:
    max_depth: Optional[int] = None          # reject if frame count exceeds this
    allowed_exceptions: Optional[List[str]] = None  # whitelist; None = allow all
    blocked_exceptions: Optional[List[str]] = None  # blacklist
    max_message_length: Optional[int] = None


@dataclass
class BounceResult:
    trace: StackTrace
    accepted: bool
    reason: Optional[str] = None

    def __str__(self) -> str:
        status = "ACCEPTED" if self.accepted else f"REJECTED ({self.reason})"
        return f"[Bouncer] {self.trace.exception_type}: {status}"


def bounce_trace(trace: StackTrace, options: Optional[BounceOptions] = None) -> BounceResult:
    """Evaluate *trace* against *options* and return a BounceResult."""
    if options is None:
        options = BounceOptions()

    exc = trace.exception_type or ""

    if options.max_depth is not None and len(trace.frames) > options.max_depth:
        return BounceResult(trace, accepted=False,
                            reason=f"depth {len(trace.frames)} exceeds max {options.max_depth}")

    if options.blocked_exceptions:
        for pattern in options.blocked_exceptions:
            if pattern.lower() in exc.lower():
                return BounceResult(trace, accepted=False,
                                    reason=f"exception '{exc}' matches blocked pattern '{pattern}'")

    if options.allowed_exceptions is not None:
        matched = any(p.lower() in exc.lower() for p in options.allowed_exceptions)
        if not matched:
            return BounceResult(trace, accepted=False,
                                reason=f"exception '{exc}' not in allowed list")

    if options.max_message_length is not None:
        msg = trace.exception_message or ""
        if len(msg) > options.max_message_length:
            return BounceResult(trace, accepted=False,
                                reason=f"message length {len(msg)} exceeds max {options.max_message_length}")

    return BounceResult(trace, accepted=True)


def format_bounce(result: BounceResult) -> str:
    lines: List[str] = [str(result)]
    lines.append(f"  Exception : {result.trace.exception_type}")
    lines.append(f"  Frames    : {len(result.trace.frames)}")
    if result.reason:
        lines.append(f"  Reason    : {result.reason}")
    return "\n".join(lines)
