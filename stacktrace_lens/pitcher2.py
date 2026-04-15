"""pitcher2: batch-send multiple stack traces to a webhook endpoint."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.error

from .parser import StackTrace


@dataclass
class BatchPitchOptions:
    include_frames: bool = True
    max_frames: int = 10
    timeout: float = 5.0
    extra_tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class BatchPitchResult:
    success: bool
    status_code: Optional[int]
    trace_count: int
    error: Optional[str] = None

    def __str__(self) -> str:
        status = "OK" if self.success else "FAILED"
        return (
            f"BatchPitchResult({status}, traces={self.trace_count}, "
            f"http={self.status_code}, error={self.error!r})"
        )


def _trace_to_payload(trace: StackTrace, opts: BatchPitchOptions) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "exception_type": trace.exception_type,
        "exception_message": trace.exception_message,
    }
    if opts.include_frames:
        frames = trace.frames[: opts.max_frames]
        payload["frames"] = [
            {
                "filename": f.filename,
                "lineno": f.lineno,
                "function": f.function,
            }
            for f in frames
        ]
    if opts.extra_tags:
        payload["tags"] = opts.extra_tags
    return payload


def batch_pitch_to_webhook(
    traces: List[StackTrace],
    url: str,
    opts: Optional[BatchPitchOptions] = None,
) -> BatchPitchResult:
    """POST a batch of stack traces as a JSON array to *url*."""
    if opts is None:
        opts = BatchPitchOptions()

    body = json.dumps(
        {"traces": [_trace_to_payload(t, opts) for t in traces]}
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=opts.timeout) as resp:
            return BatchPitchResult(
                success=True,
                status_code=resp.status,
                trace_count=len(traces),
            )
    except urllib.error.HTTPError as exc:
        return BatchPitchResult(
            success=False,
            status_code=exc.code,
            trace_count=len(traces),
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        return BatchPitchResult(
            success=False,
            status_code=None,
            trace_count=len(traces),
            error=str(exc),
        )
