"""Tests for stacktrace_lens.archiver and archiver_cmd."""
from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from stacktrace_lens.archiver import (
    Archive,
    ArchiveEntry,
    add_to_archive,
    load_archive,
    save_archive,
)
from stacktrace_lens.archiver_cmd import archiver_command
from stacktrace_lens.parser import Frame, StackTrace


def _make_trace(exc_type="ValueError", msg="bad value") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=msg,
        frames=[Frame(filename="app.py", lineno=10, function="run", source="x = 1/0")],
    )


def _args(**kwargs):
    defaults = {"archive_file": "", "add": None, "label": None, "list": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# --- archiver core ---

def test_add_to_archive_returns_entry():
    arch = Archive()
    entry = add_to_archive(arch, _make_trace())
    assert isinstance(entry, ArchiveEntry)


def test_add_to_archive_increments_count():
    arch = Archive()
    add_to_archive(arch, _make_trace())
    add_to_archive(arch, _make_trace())
    assert arch.count == 2


def test_entry_stores_label():
    arch = Archive()
    entry = add_to_archive(arch, _make_trace(), label="prod")
    assert entry.label == "prod"


def test_entry_archived_at_is_recent():
    arch = Archive()
    before = time.time()
    entry = add_to_archive(arch, _make_trace())
    assert entry.archived_at >= before


def test_save_and_load_roundtrip(tmp_path):
    arch = Archive()
    add_to_archive(arch, _make_trace("TypeError", "oops"), label="test")
    p = tmp_path / "archive.json"
    save_archive(arch, p)
    loaded = load_archive(p)
    assert loaded.count == 1
    assert loaded.entries[0].trace.exception_type == "TypeError"
    assert loaded.entries[0].label == "test"


def test_save_produces_valid_json(tmp_path):
    arch = Archive()
    add_to_archive(arch, _make_trace())
    p = tmp_path / "archive.json"
    save_archive(arch, p)
    data = json.loads(p.read_text())
    assert "entries" in data


# --- archiver_cmd ---

def test_list_empty_archive(tmp_path, capsys):
    import io
    out = io.StringIO()
    p = tmp_path / "a.json"
    rc = archiver_command(_args(archive_file=str(p), list=True), out=out)
    assert rc == 0
    assert "empty" in out.getvalue()


def test_add_from_file(tmp_path):
    import io
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(
        "Traceback (most recent call last):\n"
        '  File \"app.py\", line 5, in run\n'
        "    x = 1/0\n"
        "ZeroDivisionError: division by zero\n"
    )
    arch_file = tmp_path / "arch.json"
    out = io.StringIO()
    rc = archiver_command(_args(archive_file=str(arch_file), add=str(trace_file)), out=out)
    assert rc == 0
    assert "Archived" in out.getvalue()


def test_add_missing_file_returns_one(tmp_path):
    import io
    out, err = io.StringIO(), io.StringIO()
    rc = archiver_command(
        _args(archive_file=str(tmp_path / "a.json"), add="/no/such/file.txt"),
        out=out, err=err,
    )
    assert rc == 1
