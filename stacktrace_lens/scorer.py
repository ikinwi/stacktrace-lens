"""Frame-level relevance scorer: ranks frames by how likely they are
to be the root cause of an exception."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from stacktrace_lens.parser import Frame, StackTrace

# Patterns that indicate third-party / stdlib noise (lower relevance)
_NOISE_PATTERNS: List[re.Pattern] = [
    re.compile(r"[\\/]site-packages[\\/]"),
    re.compile(r"[\\/]dist-packages[\\/]"),
    re.compile(r"<frozen "),
    re.compile(r"[\\/]lib[\\/]python\d"),
]

# Patterns that boost relevance (user code signals)
_BOOST_PATTERNS: List[re.Pattern] = [
    re.compile(r"^(?!.*site-packages).*\.py$"),
]


@dataclass
class ScoredFrame:
    frame: Frame
    score: float
    reason: str

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.frame.filename}:{self.frame.lineno} ({self.score:.2f}) — {self.reason}"


@dataclass
class ScoreReport:
    frames: List[ScoredFrame] = field(default_factory=list)

    @property
    def top_frame(self) -> ScoredFrame | None:
        """Return the highest-scoring frame, or None if empty."""
        if not self.frames:
            return None
        return max(self.frames, key=lambda sf: sf.score)

    @property
    def ranked(self) -> List[ScoredFrame]:
        """Return frames sorted by score descending."""
        return sorted(self.frames, key=lambda sf: sf.score, reverse=True)


def _score_frame(frame: Frame, depth: int, total: int) -> ScoredFrame:
    """Compute a relevance score for a single frame."""
    score = 0.0
    reasons: List[str] = []

    # Frames near the bottom of the trace (innermost) are more relevant
    depth_bonus = depth / max(total - 1, 1)
    score += depth_bonus * 0.4
    reasons.append(f"depth={depth_bonus:.2f}")

    # Penalise noise paths
    is_noise = any(p.search(frame.filename) for p in _NOISE_PATTERNS)
    if is_noise:
        score -= 0.5
        reasons.append("stdlib/third-party")
    else:
        score += 0.4
        reasons.append("user-code")

    # Small bonus for short filenames (project-local files)
    if len(frame.filename) < 60 and not is_noise:
        score += 0.1
        reasons.append("local-path")

    return ScoredFrame(frame=frame, score=round(score, 4), reason=", ".join(reasons))


def score_frames(trace: StackTrace) -> ScoreReport:
    """Score every frame in *trace* and return a :class:`ScoreReport`."""
    total = len(trace.frames)
    scored = [
        _score_frame(frame, depth=i, total=total)
        for i, frame in enumerate(trace.frames)
    ]
    return ScoreReport(frames=scored)
