"""Steering-content tests for ``module-completion-track.md``.

Feature: track-completion-pdf-transcript

Task 3.2 delivers the always-generate behavior in steering text, so these
structural assertions keep the shipped ``module-completion-track.md`` in
agreement with the reference model (design "Steering-content tests"): the
always-run render subsection exists, invokes both ``generate_recap_pdf.py`` and
``generate_transcript.py`` after the recap and transcript reconciliation passes,
states it runs independent of graduation acceptance and regardless of
``skip_graduation``, is marked non-blocking, the stale "produced later, in the
graduation flow" note has been updated, and no external URLs were introduced.

Validates: Requirement 4.1
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve the steering file relative to this test file (python-conventions.md)
# ---------------------------------------------------------------------------

_STEERING_FILE: Path = (
    Path(__file__).resolve().parent.parent / "steering" / "module-completion-track.md"
)

_CONTENT: str = _STEERING_FILE.read_text(encoding="utf-8")

# Headings for the two reconciliation passes and the render subsection.
_RECAP_RECONCILE_HEADING = "### Recap Reconciliation & Backfill (Path A final safety net)"
_TRANSCRIPT_RECONCILE_HEADING = "### Q&A Transcript Reconciliation (Path A final safety net)"
_RENDER_HEADING = "### Shareable Deliverables: Recap PDF & Q&A Transcript"


def _heading_index(content: str, heading: str) -> int:
    """Return the offset of *heading* where it appears as its own line.

    The render-subsection title is also referenced inline (inside backticks)
    elsewhere in the file, so a bare ``str.find`` would match the prose mention
    rather than the actual heading. This matches the heading only when it starts
    a line, ignoring inline references.

    Args:
        content: The full steering-file text.
        heading: The exact ``### `` heading line to locate.

    Returns:
        The offset of the heading line, or ``-1`` if it is not present as a line.
    """
    if content.startswith(heading):
        return 0
    marker = "\n" + heading
    found = content.find(marker)
    return -1 if found == -1 else found + 1


def _subsection(content: str, heading: str) -> str:
    """Return the text of the ``### `` subsection that starts at *heading*.

    The subsection spans from *heading* (matched as its own line) up to (but not
    including) the next ``### `` heading or end of file.

    Args:
        content: The full steering-file text.
        heading: The exact ``### `` heading that begins the subsection.

    Returns:
        The subsection body (including its heading line).

    Raises:
        AssertionError: If *heading* is not present as a line in *content*.
    """
    start = _heading_index(content, heading)
    assert start != -1, f"Heading not found: {heading!r}"
    rest = content[start + len(heading):]
    next_heading = rest.find("\n### ")
    end = len(content) if next_heading == -1 else start + len(heading) + next_heading
    return content[start:end]


class TestModuleCompletionRenderSubsection:
    """Feature: track-completion-pdf-transcript — steering-content assertions.

    Asserts ``module-completion-track.md`` carries the always-run render
    subsection with the required invocations, ordering, independence, and
    non-blocking wording.

    Validates: Requirement 4.1
    """

    def test_render_subsection_heading_exists(self) -> None:
        """The always-run render subsection heading is present."""
        assert _RENDER_HEADING in _CONTENT, (
            f"Missing render subsection heading: {_RENDER_HEADING!r}"
        )

    def test_render_subsection_invokes_both_generators(self) -> None:
        """The render subsection invokes both PDF and transcript generators."""
        subsection = _subsection(_CONTENT, _RENDER_HEADING)
        assert "generate_recap_pdf.py" in subsection, (
            "Render subsection must invoke generate_recap_pdf.py"
        )
        assert "generate_transcript.py" in subsection, (
            "Render subsection must invoke generate_transcript.py"
        )

    def test_render_runs_after_both_reconciliation_passes(self) -> None:
        """Render subsection appears after both reconciliation passes.

        The recap reconciliation (``completion_artifacts.py ... --backfill``)
        and the transcript reconciliation (``reconcile_transcript.py``) must
        both precede the render subsection, preserving the reconcile-then-render
        ordering (design Property 2).
        """
        recap_idx = _heading_index(_CONTENT, _RECAP_RECONCILE_HEADING)
        transcript_idx = _heading_index(_CONTENT, _TRANSCRIPT_RECONCILE_HEADING)
        render_idx = _heading_index(_CONTENT, _RENDER_HEADING)

        assert recap_idx != -1, "Missing recap reconciliation heading"
        assert transcript_idx != -1, "Missing transcript reconciliation heading"
        assert render_idx != -1, "Missing render subsection heading"

        assert recap_idx < render_idx, (
            "Recap reconciliation must appear before the render subsection"
        )
        assert transcript_idx < render_idx, (
            "Transcript reconciliation must appear before the render subsection"
        )
        # The transcript reconciliation pass itself must invoke reconcile_transcript.py.
        transcript_section = _subsection(_CONTENT, _TRANSCRIPT_RECONCILE_HEADING)
        assert "reconcile_transcript.py" in transcript_section, (
            "Transcript reconciliation pass must invoke reconcile_transcript.py"
        )
        # The reconcile invocation must precede the render subsection.
        reconcile_call_idx = _CONTENT.find("reconcile_transcript.py")
        assert reconcile_call_idx != -1, "Missing reconcile_transcript.py invocation"
        assert reconcile_call_idx < render_idx, (
            "reconcile_transcript.py must be invoked before the render subsection"
        )

    def test_render_independent_of_graduation_acceptance(self) -> None:
        """The render subsection states independence from graduation acceptance."""
        subsection = _subsection(_CONTENT, _RENDER_HEADING).lower()
        assert "independent of whether the bootcamper accepts graduation" in subsection, (
            "Render subsection must state it runs independent of graduation acceptance"
        )

    def test_render_independent_of_skip_graduation(self) -> None:
        """The render subsection states it runs regardless of skip_graduation."""
        subsection = _subsection(_CONTENT, _RENDER_HEADING)
        assert "regardless of `skip_graduation`" in subsection, (
            "Render subsection must state it runs regardless of skip_graduation"
        )
        assert "skip_graduation" in subsection, (
            "Render subsection must reference the skip_graduation preference"
        )

    def test_render_subsection_marked_non_blocking(self) -> None:
        """The render subsection is marked non-blocking."""
        subsection = _subsection(_CONTENT, _RENDER_HEADING).lower()
        assert "non-blocking" in subsection, (
            "Render subsection must be marked non-blocking"
        )

    def test_stale_graduation_flow_note_updated(self) -> None:
        """The stale 'produced later, in the graduation flow' note is gone."""
        assert "produced later, in the graduation flow" not in _CONTENT, (
            "Stale note 'produced later, in the graduation flow' must be updated"
        )
        # The updated wording states the deliverables are produced at track completion.
        assert "produced **here at track completion**" in _CONTENT, (
            "Updated note must state the PDF/transcript are produced at track completion"
        )

    def test_no_external_urls_introduced(self) -> None:
        """No external http(s) URLs were introduced (power-distribution safety)."""
        urls = re.findall(r"https?://\S+", _CONTENT)
        assert urls == [], f"External URLs must not be introduced: {urls}"
