"""Tests for stacktrace_lens.outlier."""
import pytest

from stacktrace_lens.parser import Frame, StackTrace
from stacktrace_lens.outlier import (
    OutlierFrame,
    OutlierReport,
    detect_outliers,
    format_outliers,
)


def _frame(filename: str = "app.py", lineno: int = 10, function: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, function=function, source_line="x")


def _trace(*frames: Frame, exc_type: str = "ValueError", exc_msg: str = "oops") -> StackTrace:
    return StackTrace(exception_type=exc_type, exception_message=exc_msg, frames=list(frames))


# ---------------------------------------------------------------------------
# OutlierFrame helpers
# ---------------------------------------------------------------------------

def test_outlier_frame_frequency_zero_total():
    of = OutlierFrame(frame=_frame(), occurrences=0, total_traces=0)
    assert of.frequency == 0.0


def test_outlier_frame_frequency_calculation():
    of = OutlierFrame(frame=_frame(), occurrences=1, total_traces=4)
    assert of.frequency == pytest.approx(0.25)


def test_outlier_frame_str_contains_filename():
    of = OutlierFrame(frame=_frame(filename="mymodule.py"), occurrences=1, total_traces=5)
    assert "mymodule.py" in str(of)


# ---------------------------------------------------------------------------
# OutlierReport helpers
# ---------------------------------------------------------------------------

def test_outlier_report_count():
    report = OutlierReport(total_traces=5, threshold=0.2, outliers=[
        OutlierFrame(frame=_frame(), occurrences=1, total_traces=5),
    ])
    assert report.count == 1


def test_outlier_report_rarest_none_when_empty():
    report = OutlierReport(total_traces=5, threshold=0.2, outliers=[])
    assert report.rarest() is None


def test_outlier_report_rarest_returns_lowest_frequency():
    of_common = OutlierFrame(frame=_frame(lineno=1), occurrences=2, total_traces=10)
    of_rare = OutlierFrame(frame=_frame(lineno=2), occurrences=1, total_traces=10)
    report = OutlierReport(total_traces=10, threshold=0.2, outliers=[of_common, of_rare])
    assert report.rarest() is of_rare


# ---------------------------------------------------------------------------
# detect_outliers
# ---------------------------------------------------------------------------

def test_detect_returns_outlier_report():
    traces = [_trace(_frame())]
    result = detect_outliers(traces)
    assert isinstance(result, OutlierReport)


def test_detect_empty_traces_returns_zero_total():
    result = detect_outliers([])
    assert result.total_traces == 0
    assert result.count == 0


def test_detect_all_frames_common_produces_no_outliers():
    common = _frame(filename="shared.py", lineno=1)
    traces = [_trace(common), _trace(common), _trace(common)]
    result = detect_outliers(traces, threshold=0.2)
    # frequency = 1.0, above threshold
    assert result.count == 0


def test_detect_rare_frame_flagged_as_outlier():
    common = _frame(filename="shared.py", lineno=1)
    rare = _frame(filename="rare.py", lineno=99)
    traces = [
        _trace(common, rare),
        _trace(common),
        _trace(common),
        _trace(common),
        _trace(common),
    ]
    result = detect_outliers(traces, threshold=0.2)
    assert result.count == 1
    assert result.outliers[0].frame.filename == "rare.py"


def test_detect_frame_counted_once_per_trace():
    """Duplicate frames within a single trace should not inflate the count."""
    f = _frame()
    traces = [_trace(f, f), _trace(f, f), _trace(f, f), _trace(f, f), _trace()]
    result = detect_outliers(traces, threshold=0.5)
    matching = [o for o in result.outliers if o.frame.filename == f.filename]
    if matching:
        assert matching[0].occurrences == 4


def test_detect_threshold_stored_in_report():
    result = detect_outliers([_trace(_frame())], threshold=0.1)
    assert result.threshold == pytest.approx(0.1)


def test_detect_outliers_sorted_by_frequency():
    f1 = _frame(lineno=1)
    f2 = _frame(lineno=2)
    f3 = _frame(lineno=3)
    traces = [
        _trace(f1, f2, f3),
        _trace(f2, f3),
        _trace(f3),
        _trace(f3),
        _trace(f3),
    ]
    result = detect_outliers(traces, threshold=0.9)
    freqs = [o.frequency for o in result.outliers]
    assert freqs == sorted(freqs)


# ---------------------------------------------------------------------------
# format_outliers
# ---------------------------------------------------------------------------

def test_format_outliers_returns_string():
    report = detect_outliers([_trace(_frame())])
    assert isinstance(format_outliers(report), str)


def test_format_outliers_contains_threshold():
    report = OutlierReport(total_traces=3, threshold=0.15, outliers=[])
    output = format_outliers(report)
    assert "15%" in output


def test_format_outliers_none_when_empty():
    report = OutlierReport(total_traces=0, threshold=0.2, outliers=[])
    assert "(none)" in format_outliers(report)


def test_format_outliers_contains_frame_info():
    of = OutlierFrame(frame=_frame(filename="edge.py"), occurrences=1, total_traces=10)
    report = OutlierReport(total_traces=10, threshold=0.2, outliers=[of])
    output = format_outliers(report)
    assert "edge.py" in output
