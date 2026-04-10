"""Tests for stacktrace_lens.annotation_renderer."""
from __future__ import annotations

from unittest.mock import patch

from stacktrace_lens.annotator import AnnotatedFrame, AnnotatedLine, AnnotationOptions, annotate_frame
from stacktrace_lens.annotation_renderer import AnnotationRenderer
from stacktrace_lens.formatter import FormatOptions
from stacktrace_lens.parser import Frame


def _frame(lineno: int = 5) -> Frame:
    return Frame(filename="/app/mod.py", lineno=lineno, function="do_thing", source_line="pass")


def _renderer(colour: bool = False) -> AnnotationRenderer:
    return AnnotationRenderer(
        format_opts=FormatOptions(colour=colour),
        annotation_opts=AnnotationOptions(context_lines=2),
    )


_LINES = {
    3: "line3\n", 4: "line4\n", 5: "error_line\n", 6: "line6\n", 7: "line7\n",
}


def _fake_getline(filename, lineno, *_):
    return _LINES.get(lineno, "")


@patch("linecache.getline", side_effect=_fake_getline)
def test_render_returns_string(mock_gl):
    af = annotate_frame(_frame(), AnnotationOptions(context_lines=2))
    result = _renderer().render(af)
    assert isinstance(result, str)


@patch("linecache.getline", side_effect=_fake_getline)
def test_render_contains_filename(mock_gl):
    af = annotate_frame(_frame(), AnnotationOptions(context_lines=2))
    result = _renderer().render(af)
    assert "/app/mod.py" in result


@patch("linecache.getline", side_effect=_fake_getline)
def test_render_contains_function_name(mock_gl):
    af = annotate_frame(_frame(), AnnotationOptions(context_lines=2))
    result = _renderer().render(af)
    assert "do_thing" in result


@patch("linecache.getline", side_effect=_fake_getline)
def test_render_marks_error_line(mock_gl):
    af = annotate_frame(_frame(), AnnotationOptions(context_lines=2))
    result = _renderer().render(af)
    assert "<--" in result


def test_render_no_source_shows_placeholder():
    af = AnnotatedFrame(frame=_frame(), lines=[], source_available=False)
    result = _renderer().render(af)
    assert "source not available" in result


@patch("linecache.getline", side_effect=_fake_getline)
def test_render_all_returns_combined(mock_gl):
    opts = AnnotationOptions(context_lines=2)
    frames = [annotate_frame(_frame(5), opts), annotate_frame(_frame(6), opts)]
    result = _renderer().render_all(frames)
    assert result.count("do_thing") == 2


@patch("linecache.getline", side_effect=_fake_getline)
def test_colour_output_contains_escape_codes(mock_gl):
    af = annotate_frame(_frame(), AnnotationOptions(context_lines=2))
    result = _renderer(colour=True).render(af)
    assert "\033[" in result


@patch("linecache.getline", side_effect=_fake_getline)
def test_render_contains_line_numbers(mock_gl):
    """Each rendered context line should include its line number."""
    af = annotate_frame(_frame(), AnnotationOptions(context_lines=2))
    result = _renderer().render(af)
    # Lines 3-7 are in context; their line numbers should appear in the output.
    for lineno in (3, 4, 5, 6, 7):
        assert str(lineno) in result, f"Expected line number {lineno} in rendered output"
