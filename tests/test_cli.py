"""Tests for the CLI entry point."""

import textwrap
import pytest
from unittest.mock import patch, mock_open

from stacktrace_lens.cli import main, build_parser, read_input


SAMPLE_TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in main
        result = 1 / 0
    ZeroDivisionError: division by zero
""")


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser.prog == "stacktrace-lens"


def test_main_returns_zero_on_valid_input(tmp_path):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(SAMPLE_TRACEBACK)
    result = main([str(trace_file), "--no-color"])
    assert result == 0


def test_main_returns_one_on_empty_input(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   ")
    result = main([str(empty_file)])
    assert result == 1


def test_main_no_suggestions_flag(tmp_path, capsys):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(SAMPLE_TRACEBACK)
    main([str(trace_file), "--no-color", "--no-suggestions"])
    captured = capsys.readouterr()
    assert "Suggestions" not in captured.out


def test_main_compact_flag_does_not_crash(tmp_path):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(SAMPLE_TRACEBACK)
    result = main([str(trace_file), "--no-color", "--compact"])
    assert result == 0


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "nonexistent.txt")])
    assert exc_info.value.code == 1


def test_read_input_from_file(tmp_path):
    f = tmp_path / "tb.txt"
    f.write_text("hello")
    assert read_input(str(f)) == "hello"


def test_read_input_stdin():
    with patch("stacktrace_lens.cli.sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = False
        mock_stdin.read.return_value = "traceback text"
        result = read_input(None)
    assert result == "traceback text"


def test_main_outputs_exception_type(tmp_path, capsys):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(SAMPLE_TRACEBACK)
    main([str(trace_file), "--no-color"])
    captured = capsys.readouterr()
    assert "ZeroDivisionError" in captured.out


def test_main_outputs_suggestions_for_known_error(tmp_path, capsys):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text(SAMPLE_TRACEBACK)
    main([str(trace_file), "--no-color"])
    captured = capsys.readouterr()
    assert "Suggestions" in captured.out or "division" in captured.out.lower()
