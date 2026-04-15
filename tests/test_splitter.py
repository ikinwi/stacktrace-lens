import textwrap
import pytest

from stacktrace_lens.splitter import SplitReport, split_trace, _split_raw, is_chained
from stacktrace_lens.parser import StackTrace


SINGLE_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in main
        result = divide(1, 0)
      File "math_utils.py", line 5, in divide
        return a / b
    ZeroDivisionError: division by zero
""")

CHAINED_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 3, in load
        open("missing.txt")
    FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
      File "app.py", line 8, in run
        load()
    RuntimeError: failed to load
""")

CAUSED_BY_TRACE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "db.py", line 4, in connect
        raise ConnectionError("timeout")
    ConnectionError: timeout

    Caused by

    Traceback (most recent call last):
      File "net.py", line 2, in dial
        raise OSError("unreachable")
    OSError: unreachable
""")


def test_split_single_returns_one_trace():
    report = split_trace(SINGLE_TRACE)
    assert report.count == 1


def test_split_chained_returns_two_traces():
    report = split_trace(CHAINED_TRACE)
    assert report.count == 2


def test_split_caused_by_returns_two_traces():
    report = split_trace(CAUSED_BY_TRACE)
    assert report.count == 2


def test_is_chained_false_for_single():
    report = split_trace(SINGLE_TRACE)
    assert report.is_chained is False


def test_is_chained_true_for_chained():
    report = split_trace(CHAINED_TRACE)
    assert report.is_chained is True


def test_traces_are_stacktrace_instances():
    report = split_trace(CHAINED_TRACE)
    for trace in report.traces:
        assert isinstance(trace, StackTrace)


def test_split_raw_single_produces_one_part():
    parts = _split_raw(SINGLE_TRACE)
    assert len(parts) == 1


def test_split_raw_chained_produces_two_parts():
    parts = _split_raw(CHAINED_TRACE)
    assert len(parts) == 2


def test_split_report_count_property():
    report = SplitReport(traces=[])
    assert report.count == 0


def test_split_report_is_chained_false_when_empty():
    report = SplitReport(traces=[])
    assert report.is_chained is False


def test_first_trace_exception_type_preserved():
    report = split_trace(SINGLE_TRACE)
    assert report.traces[0].exception_type == "ZeroDivisionError"
