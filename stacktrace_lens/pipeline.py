"""pipeline.py – Composable processing pipeline for stack traces.

Allows chaining multiple transformation steps (filter, normalize, deduplicate,
enrich, tag, score, etc.) into a single reusable pipeline object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from stacktrace_lens.parser import StackTrace

# A step is any callable that accepts a StackTrace and returns a StackTrace.
PipelineStep = Callable[[StackTrace], StackTrace]


@dataclass
class PipelineResult:
    """Holds the final trace and a log of which steps were applied."""

    trace: StackTrace
    steps_applied: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True when no errors were recorded during processing."""
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = [f"Steps applied ({len(self.steps_applied)}):"]
        for name in self.steps_applied:
            lines.append(f"  ✓ {name}")
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  ✗ {err}")
        return "\n".join(lines)


class Pipeline:
    """Ordered sequence of StackTrace transformation steps.

    Example usage::

        from stacktrace_lens.filters import filter_frames, FilterOptions
        from stacktrace_lens.normalizer import normalize_trace, NormalizeOptions

        pipeline = (
            Pipeline()
            .add("filter", lambda t: filter_frames(t, FilterOptions(exclude_stdlib=True)))
            .add("normalize", lambda t: normalize_trace(t, NormalizeOptions()))
        )
        result = pipeline.run(my_trace)
        print(result.summary())
    """

    def __init__(self) -> None:
        self._steps: List[tuple[str, PipelineStep]] = []

    # ------------------------------------------------------------------
    # Builder API
    # ------------------------------------------------------------------

    def add(self, name: str, step: PipelineStep) -> "Pipeline":
        """Append a named step and return *self* for chaining."""
        if not callable(step):
            raise TypeError(f"Step '{name}' must be callable, got {type(step).__name__}")
        self._steps.append((name, step))
        return self

    def remove(self, name: str) -> "Pipeline":
        """Remove the first step with the given name (no-op if not found)."""
        self._steps = [(n, s) for n, s in self._steps if n != name]
        return self

    @property
    def step_names(self) -> List[str]:
        """Return ordered list of registered step names."""
        return [n for n, _ in self._steps]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, trace: StackTrace, *, stop_on_error: bool = False) -> PipelineResult:
        """Execute all steps in order against *trace*.

        Args:
            trace: The initial :class:`StackTrace` to process.
            stop_on_error: When *True*, abort the pipeline on the first
                step that raises an exception.  When *False* (default),
                the offending step is skipped and the previous trace is
                forwarded to the next step.

        Returns:
            A :class:`PipelineResult` with the final trace and audit log.
        """
        current = trace
        applied: List[str] = []
        errors: List[str] = []

        for name, step in self._steps:
            try:
                current = step(current)
                applied.append(name)
            except Exception as exc:  # noqa: BLE001
                msg = f"{name}: {type(exc).__name__}: {exc}"
                errors.append(msg)
                if stop_on_error:
                    break

        return PipelineResult(trace=current, steps_applied=applied, errors=errors)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._steps)

    def __repr__(self) -> str:  # pragma: no cover
        names = ", ".join(self.step_names)
        return f"Pipeline([{names}])"


def build_default_pipeline(
    *,
    exclude_stdlib: bool = True,
    strip_cwd: bool = True,
    deduplicate: bool = True,
) -> Pipeline:
    """Return a sensible default pipeline for common use-cases.

    Importing here avoids circular dependencies; each import is deferred
    until this factory is actually called.
    """
    from stacktrace_lens.filters import FilterOptions, filter_frames
    from stacktrace_lens.normalizer import NormalizeOptions, normalize_trace
    from stacktrace_lens.deduplicator import DeduplicateOptions, deduplicate_frames

    pipeline = Pipeline()

    if exclude_stdlib:
        opts = FilterOptions(exclude_stdlib=True)
        pipeline.add("filter_stdlib", lambda t, _o=opts: filter_frames(t, _o))

    if strip_cwd:
        opts = NormalizeOptions(strip_cwd=True)  # type: ignore[assignment]
        pipeline.add("normalize", lambda t, _o=opts: normalize_trace(t, _o))

    if deduplicate:
        opts = DeduplicateOptions()  # type: ignore[assignment]
        pipeline.add(
            "deduplicate",
            lambda t, _o=opts: _dedup_adapter(t, _o),
        )

    return pipeline


def _dedup_adapter(trace: StackTrace, opts) -> StackTrace:  # type: ignore[type-arg]
    """Wrap deduplicate_frames so it returns a StackTrace."""
    from stacktrace_lens.deduplicator import deduplicate_frames
    from stacktrace_lens.parser import StackTrace as ST

    deduped = deduplicate_frames(trace.frames, opts)
    frames = [d.frame for d in deduped]
    return ST(
        exception_type=trace.exception_type,
        exception_message=trace.exception_message,
        frames=frames,
    )
