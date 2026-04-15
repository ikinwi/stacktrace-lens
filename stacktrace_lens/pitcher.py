"""pitcher.py – forward stack traces to external endpoints (webhooks, files)."""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_lens.parser import StackTrace


@dataclass
class PitchOptions:
    webhook_url: Optional[str] = None
    output_file: Optional[str] = None
    include_frames: bool = True
    timeout: int = 5


@dataclass
class PitchResult:
    success: bool
    destination: str
    status_code: Optional[int] = None
    error: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover
        status = "OK" if self.success else "FAILED"
        detail = f" [{self.status_code}]" if self.status_code is not None else ""
        err = f" – {self.error}" if self.error else ""
        return f"{status}{detail} → {self.destination}{err}"


def _trace_to_payload(trace: StackTrace, include_frames: bool) -> dict:
    payload: dict = {
        "exception_type": trace.exception_type,
        "exception_message": trace.exception_message,
    }
    if include_frames:
        payload["frames"] = [
            {
                "filename": f.filename,
                "lineno": f.lineno,
                "function": f.function,
                "source": f.source,
            }
            for f in trace.frames
        ]
    return payload


def pitch_to_webhook(trace: StackTrace, options: PitchOptions) -> PitchResult:
    """POST the trace as JSON to a webhook URL."""
    if not options.webhook_url:
        return PitchResult(success=False, destination="", error="No webhook URL provided")
    payload = _trace_to_payload(trace, options.include_frames)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        options.webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=options.timeout) as resp:
            return PitchResult(success=True, destination=options.webhook_url, status_code=resp.status)
    except Exception as exc:  # noqa: BLE001
        return PitchResult(success=False, destination=options.webhook_url, error=str(exc))


def pitch_to_file(trace: StackTrace, options: PitchOptions) -> PitchResult:
    """Write the trace as a JSON line to a local file."""
    if not options.output_file:
        return PitchResult(success=False, destination="", error="No output file provided")
    payload = _trace_to_payload(trace, options.include_frames)
    try:
        with open(options.output_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")
        return PitchResult(success=True, destination=options.output_file)
    except OSError as exc:
        return PitchResult(success=False, destination=options.output_file, error=str(exc))


def pitch_trace(trace: StackTrace, options: PitchOptions) -> List[PitchResult]:
    """Dispatch the trace to all configured destinations."""
    results: List[PitchResult] = []
    if options.webhook_url:
        results.append(pitch_to_webhook(trace, options))
    if options.output_file:
        results.append(pitch_to_file(trace, options))
    return results
