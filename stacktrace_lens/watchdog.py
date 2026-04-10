"""Watchdog: watch a log file for new stack traces and emit alerts."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, List, Optional

from .parser import StackTrace, parse_stacktrace
from .severity import SeverityResult, score_trace


@dataclass
class WatchOptions:
    poll_interval: float = 1.0          # seconds between file checks
    min_severity_score: int = 0         # ignore traces below this score
    max_alerts: Optional[int] = None    # stop after N alerts (None = infinite)


@dataclass
class WatchAlert:
    trace: StackTrace
    severity: SeverityResult
    byte_offset: int                    # position in file where trace started


def _iter_raw_traces(text: str) -> Iterator[str]:
    """Yield individual raw traceback blocks found in *text*."""
    marker = "Traceback (most recent call last):"
    start = 0
    while True:
        idx = text.find(marker, start)
        if idx == -1:
            break
        # find the blank line or EOF that ends the block
        end = text.find("\n\n", idx)
        block = text[idx:] if end == -1 else text[idx:end]
        yield block
        start = idx + len(marker)


def tail_file(
    path: Path,
    options: WatchOptions,
    callback: Callable[[WatchAlert], None],
) -> None:
    """Tail *path*, parse any new stack traces, and invoke *callback*.

    Blocks indefinitely (or until *max_alerts* is reached).
    """
    if not path.exists():
        raise FileNotFoundError(f"Watchdog target not found: {path}")

    seen_bytes = path.stat().st_size
    alerts_emitted = 0

    while True:
        current_size = path.stat().st_size
        if current_size > seen_bytes:
            with path.open("r", errors="replace") as fh:
                fh.seek(seen_bytes)
                new_text = fh.read()
            offset = seen_bytes
            seen_bytes = current_size

            for raw in _iter_raw_traces(new_text):
                try:
                    trace = parse_stacktrace(raw)
                except Exception:
                    continue
                severity = score_trace(trace)
                if severity.score < options.min_severity_score:
                    continue
                alert = WatchAlert(
                    trace=trace,
                    severity=severity,
                    byte_offset=offset,
                )
                callback(alert)
                alerts_emitted += 1
                if options.max_alerts is not None and alerts_emitted >= options.max_alerts:
                    return

        time.sleep(options.poll_interval)
