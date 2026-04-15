"""Tests for stacktrace_lens.pitcher."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.pitcher import (
    PitchOptions,
    PitchResult,
    _trace_to_payload,
    pitch_to_file,
    pitch_to_webhook,
    pitch_trace,
)


def _make_trace() -> StackTrace:
    frames = [
        Frame(filename="app/main.py", lineno=10, function="run", source="run()"),
        Frame(filename="app/utils.py", lineno=42, function="helper", source="helper()"),
    ]
    return StackTrace(exception_type="RuntimeError", exception_message="boom", frames=frames)


# ---------------------------------------------------------------------------
# _trace_to_payload
# ---------------------------------------------------------------------------

def test_payload_has_exception_type():
    trace = _make_trace()
    payload = _trace_to_payload(trace, include_frames=True)
    assert payload["exception_type"] == "RuntimeError"


def test_payload_has_exception_message():
    trace = _make_trace()
    payload = _trace_to_payload(trace, include_frames=True)
    assert payload["exception_message"] == "boom"


def test_payload_includes_frames_when_requested():
    trace = _make_trace()
    payload = _trace_to_payload(trace, include_frames=True)
    assert "frames" in payload
    assert len(payload["frames"]) == 2


def test_payload_excludes_frames_when_not_requested():
    trace = _make_trace()
    payload = _trace_to_payload(trace, include_frames=False)
    assert "frames" not in payload


# ---------------------------------------------------------------------------
# pitch_to_file
# ---------------------------------------------------------------------------

def test_pitch_to_file_returns_pitch_result():
    trace = _make_trace()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        opts = PitchOptions(output_file=path)
        result = pitch_to_file(trace, opts)
        assert isinstance(result, PitchResult)
    finally:
        os.unlink(path)


def test_pitch_to_file_success_flag():
    trace = _make_trace()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        opts = PitchOptions(output_file=path)
        result = pitch_to_file(trace, opts)
        assert result.success is True
    finally:
        os.unlink(path)


def test_pitch_to_file_writes_json_line():
    trace = _make_trace()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        opts = PitchOptions(output_file=path)
        pitch_to_file(trace, opts)
        with open(path) as fh:
            data = json.loads(fh.readline())
        assert data["exception_type"] == "RuntimeError"
    finally:
        os.unlink(path)


def test_pitch_to_file_no_path_returns_failure():
    trace = _make_trace()
    opts = PitchOptions()
    result = pitch_to_file(trace, opts)
    assert result.success is False


def test_pitch_to_file_invalid_path_returns_failure():
    trace = _make_trace()
    opts = PitchOptions(output_file="/nonexistent_dir/out.jsonl")
    result = pitch_to_file(trace, opts)
    assert result.success is False
    assert result.error is not None


# ---------------------------------------------------------------------------
# pitch_to_webhook
# ---------------------------------------------------------------------------

def test_pitch_to_webhook_no_url_returns_failure():
    trace = _make_trace()
    opts = PitchOptions()
    result = pitch_to_webhook(trace, opts)
    assert result.success is False


def test_pitch_to_webhook_success(monkeypatch):
    trace = _make_trace()
    opts = PitchOptions(webhook_url="http://example.com/hook")
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = pitch_to_webhook(trace, opts)
    assert result.success is True
    assert result.status_code == 200


def test_pitch_to_webhook_failure_on_exception(monkeypatch):
    trace = _make_trace()
    opts = PitchOptions(webhook_url="http://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        result = pitch_to_webhook(trace, opts)
    assert result.success is False
    assert "connection refused" in (result.error or "")


# ---------------------------------------------------------------------------
# pitch_trace
# ---------------------------------------------------------------------------

def test_pitch_trace_returns_list():
    trace = _make_trace()
    opts = PitchOptions()
    results = pitch_trace(trace, opts)
    assert isinstance(results, list)


def test_pitch_trace_empty_options_returns_empty_list():
    trace = _make_trace()
    opts = PitchOptions()
    results = pitch_trace(trace, opts)
    assert results == []


def test_pitch_trace_file_destination_produces_one_result():
    trace = _make_trace()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        opts = PitchOptions(output_file=path)
        results = pitch_trace(trace, opts)
        assert len(results) == 1
    finally:
        os.unlink(path)


def test_pitch_trace_both_destinations_produce_two_results(monkeypatch):
    trace = _make_trace()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
        path = f.name
    try:
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 201
        with patch("urllib.request.urlopen", return_value=mock_resp):
            opts = PitchOptions(webhook_url="http://example.com/hook", output_file=path)
            results = pitch_trace(trace, opts)
        assert len(results) == 2
    finally:
        os.unlink(path)
