"""Tests for stacktrace_lens.censor."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.censor import (
    CensorOptions,
    CensorReport,
    CensoredFrame,
    censor_trace,
    PLACEHOLDER,
)


def _frame(
    filename: str = "/app/main.py",
    lineno: int = 10,
    function: str = "run",
    line: str = "result = do_thing()",
) -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, line=line)


def _trace(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "bad") -> StackTrace:
    return StackTrace(
        exception_type=exc_type,
        exception_message=exc_msg,
        frames=list(frames) if frames else [_frame()],
    )


def test_censor_returns_report():
    report = censor_trace(_trace())
    assert isinstance(report, CensorReport)


def test_censor_report_frame_count_matches_trace():
    trace = _trace(_frame(), _frame())
    report = censor_trace(trace)
    assert report.count == 2


def test_no_sensitive_data_zero_replacements():
    trace = _trace(_frame(line="x = 1 + 2"))
    report = censor_trace(trace)
    assert report.total_replacements == 0


def test_password_in_line_is_censored():
    trace = _trace(_frame(line="connect(password=s3cr3t)"))
    report = censor_trace(trace)
    assert report.total_replacements >= 1
    assert PLACEHOLDER in report.frames[0].censored_line


def test_token_in_line_is_censored():
    trace = _trace(_frame(line="headers = {'token=abc123'}"))
    report = censor_trace(trace)
    assert PLACEHOLDER in report.frames[0].censored_line


def test_api_key_in_line_is_censored():
    trace = _trace(_frame(line="call(api_key=XYZ987)"))
    report = censor_trace(trace)
    assert PLACEHOLDER in report.frames[0].censored_line


def test_original_frame_preserved():
    frame = _frame(line="password=hunter2")
    trace = _trace(frame)
    report = censor_trace(trace)
    assert report.frames[0].original is frame


def test_custom_placeholder():
    opts = CensorOptions(placeholder="***")
    trace = _trace(_frame(line="secret=mysecret"))
    report = censor_trace(trace, opts)
    assert "***" in report.frames[0].censored_line


def test_custom_pattern_matches():
    opts = CensorOptions(patterns=[r"ssn=\S+"])
    trace = _trace(_frame(line="ssn=123-45-6789"))
    report = censor_trace(trace, opts)
    assert PLACEHOLDER in report.frames[0].censored_line


def test_custom_pattern_does_not_affect_unrelated():
    opts = CensorOptions(patterns=[r"ssn=\S+"])
    trace = _trace(_frame(line="password=oops"))
    report = censor_trace(trace, opts)
    # default patterns not active, so password should remain
    assert report.total_replacements == 0


def test_summary_line_format():
    trace = _trace(_frame(line="token=abc"))
    report = censor_trace(trace)
    summary = report.summary_line()
    assert "Censored" in summary
    assert "sensitive" in summary


def test_censored_frame_str_contains_function():
    trace = _trace(_frame(function="authenticate", line="token=abc"))
    report = censor_trace(trace)
    assert "authenticate" in str(report.frames[0])


def test_none_line_handled_gracefully():
    frame = Frame(filename="/app/x.py", lineno=1, function="f", line=None)
    trace = StackTrace(exception_type="E", exception_message="m", frames=[frame])
    report = censor_trace(trace)
    assert report.frames[0].censored_line is None
    assert report.total_replacements == 0
