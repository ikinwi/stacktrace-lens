"""Tests for stacktrace_lens.merger_cmd."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from stacktrace_lens.merger_cmd import merger_command

_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: something went wrong
""")


def _write(tmp_path: Path, name: str, content: str = _TRACE) -> str:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


def _args(**kwargs) -> SimpleNamespace:
    defaults = dict(files=[], no_colour=True, as_json=False)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_merger_command_returns_zero_on_valid_files(tmp_path):
    f1 = _write(tmp_path, "t1.txt")
    f2 = _write(tmp_path, "t2.txt")
    rc = merger_command(_args(files=[f1, f2]))
    assert rc == 0


def test_merger_command_returns_one_on_missing_file(tmp_path):
    rc = merger_command(_args(files=[str(tmp_path / "ghost.txt")]))
    assert rc == 1


def test_merger_command_returns_one_on_empty_file_list():
    rc = merger_command(_args(files=[]))
    assert rc == 1


def test_merger_command_json_output(tmp_path, capsys):
    f1 = _write(tmp_path, "a.txt")
    f2 = _write(tmp_path, "b.txt")
    rc = merger_command(_args(files=[f1, f2], as_json=True))
    assert rc == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["total_traces"] == 2


def test_merger_command_json_has_exception_counts(tmp_path, capsys):
    f = _write(tmp_path, "c.txt")
    merger_command(_args(files=[f], as_json=True))
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert "exception_counts" in data


def test_merger_command_text_output_contains_report(tmp_path, capsys):
    f = _write(tmp_path, "d.txt")
    merger_command(_args(files=[f]))
    captured = capsys.readouterr().out
    assert "Merge Report" in captured


def test_merger_command_multiple_files_combined_frames(tmp_path, capsys):
    f1 = _write(tmp_path, "e1.txt")
    f2 = _write(tmp_path, "e2.txt")
    merger_command(_args(files=[f1, f2], as_json=True))
    data = json.loads(capsys.readouterr().out)
    assert data["combined_frames"] >= 2
