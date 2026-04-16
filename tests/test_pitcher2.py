"""Tests for stacktrace_lens.pitcher2."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.pitcher2 import (
    BatchPitchOptions,
    BatchPitchResult,
    _trace_to_payload,
    batch_pitch_to_webhook,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "run") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function)


def _trace(
    exc_type: str = "ValueError",
    exc_msg: str = "bad value",
    frames=None,
) -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=frames or [_frame()],
    )


# --- _trace_to_payload ---

def test_payload_has_exception_type():
    t = _trace(exc_type="RuntimeError")
    p = _trace_to_payload(t, BatchPitchOptions())
    assert p["exception_type"] == "RuntimeError"


def test_payload_has_exception_message():
    t = _trace(exc_msg="oops")
    p = _trace_to_payload(t, BatchPitchOptions())
    assert p["exception_message"] == "oops"


def test_payload_includes_frames_by_default():
    t = _trace(frames=[_frame("a.py"), _frame("b.py")])
    p = _trace_to_payload(t, BatchPitchOptions())
    assert "frames" in p
    assert len(p["frames"]) == 2


def test_payload_excludes_frames_when_disabled():
    t = _trace()
    opts = BatchPitchOptions(include_frames=False)
    p = _trace_to_payload(t, opts)
    assert "frames" not in p


def test_payload_respects_max_frames():
    frames = [_frame(f"f{i}.py", i) for i in range(20)]
    t = _trace(frames=frames)
    opts = BatchPitchOptions(max_frames=5)
    p = _trace_to_payload(t, opts)
    assert len(p["frames"]) == 5


def test_payload_includes_extra_tags():
    t = _trace()
    opts = BatchPitchOptions(extra_tags={"env": "prod"})
    p = _trace_to_payload(t, opts)
    assert p["tags"] == {"env": "prod"}


def test_payload_no_tags_key_when_empty():
    t = _trace()
    opts = BatchPitchOptions(extra_tags={})
    p = _trace_to_payload(t, opts)
    assert "tags" not in p


# --- batch_pitch_to_webhook ---

def _make_mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_batch_pitch_success():
    traces = [_trace(), _trace(exc_type="KeyError")]
    mock_resp = _make_mock_response(200)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = batch_pitch_to_webhook(traces, "http://example.com/hook")
    assert result.success is True
    assert result.status_code == 200
    assert result.trace_count == 2
    assert result.error is None


def test_batch_pitch_http_error():
    import urllib.error
    traces = [_trace()]
    exc = urllib.error.HTTPError("http://x", 500, "Server Error", {}, None)
    with patch("urllib.request.urlopen", side_effect=exc):
        result = batch_pitch_to_webhook(traces, "http://example.com/hook")
    assert result.success is False
    assert result.status_code == 500
    assert result.error is not None


def test_batch_pitch_url_error():
    """A network-level failure (e.g. DNS error) should return a failed result."""
    import urllib.error
    traces = [_trace()]
    exc = urllib.error.URLError("Name or service not known")
    with patch("urllib.request.urlopen", side_effect=exc):
        result = batch_pitch_to_webhook(traces, "http://example.com/hook")
    assert result.success is False
    assert result.status_code is None
    assert "Name or service not known" in result.error
