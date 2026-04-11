"""Tests for stacktrace_lens.tracer_cmd."""
import argparse
import json
import os
import textwrap
import tempfile

import pytest

from stacktrace_lens.tracer_cmd import tracer_command, _build_subparser


SAMPLE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: something went wrong
""")


def _write(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    f.write(content)
    f.close()
    return f.name


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "labels": [], "as_json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_subparser_registers_tracer():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _build_subparser(sub)
    args = parser.parse_args(["tracer"])
    assert hasattr(args, "files")


def test_tracer_command_returns_one_on_no_files():
    assert tracer_command(_args(files=[])) == 1


def test_tracer_command_returns_one_on_missing_file():
    assert tracer_command(_args(files=["/no/such/file.txt"])) == 1


def test_tracer_command_returns_zero_on_valid_files():
    path = _write(SAMPLE)
    try:
        assert tracer_command(_args(files=[path])) == 0
    finally:
        os.unlink(path)


def test_tracer_command_json_output(capsys):
    path = _write(SAMPLE)
    try:
        ret = tracer_command(_args(files=[path], as_json=True))
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert ret == 0
        assert isinstance(payload, list)
        assert payload[0]["exception"] == "ValueError"
    finally:
        os.unlink(path)


def test_tracer_command_two_files_chain(capsys):
    p1 = _write(SAMPLE)
    p2 = _write(SAMPLE.replace("ValueError", "RuntimeError"))
    try:
        ret = tracer_command(_args(files=[p1, p2], as_json=True))
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert ret == 0
        assert len(payload) == 2
        ids = {n["id"]: n for n in payload}
        child = next(n for n in payload if n["parent"] is not None)
        assert child["parent"] in ids
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_tracer_command_label_stored(capsys):
    path = _write(SAMPLE)
    try:
        tracer_command(_args(files=[path], labels=["start"], as_json=True))
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload[0]["label"] == "start"
    finally:
        os.unlink(path)


def test_tracer_command_tree_output_contains_exception(capsys):
    path = _write(SAMPLE)
    try:
        tracer_command(_args(files=[path]))
        captured = capsys.readouterr()
        assert "ValueError" in captured.out
    finally:
        os.unlink(path)
