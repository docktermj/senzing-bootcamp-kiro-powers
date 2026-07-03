"""Steering-content tests for ``graduation.md``.

Feature: track-completion-pdf-transcript (Task 4.2)

Task 4.1 added an idempotent-reuse note to ``graduation.md`` Step 0b while
preserving the Step 0a / Step 0b reconcile-then-render safety nets. These tests
keep the shipped steering file in agreement with that design:

- Step 0a (recap reconcile-then-render) and Step 0b (PDF + transcript
  reconcile-then-render) sections are still present.
- The new idempotent-reuse note is present, stating the renderers **overwrite in
  place** and produce **no conflicting duplicates** rather than appending.
- No external URLs were introduced (power-distribution safety).

Validates: Requirement 4.2
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve the steering file relative to this test file (scripts/steering are
# not packages; mirror the project sys.path/path-resolution convention).
# ---------------------------------------------------------------------------

_GRADUATION_PATH: Path = (
    Path(__file__).resolve().parent.parent / "steering" / "graduation.md"
)
_GRADUATION_TEXT: str = _GRADUATION_PATH.read_text(encoding="utf-8")
_GRADUATION_LOWER: str = _GRADUATION_TEXT.lower()


class TestGraduationReconcileThenRenderPreserved:
    """The Step 0a / Step 0b reconcile-then-render safety nets are preserved.

    Validates: Requirement 4.2
    """

    def test_step_0a_recap_reconciliation_section_present(self) -> None:
        """Step 0a (recap reconciliation & backfill) heading is present."""
        assert "## Step 0a: Recap Reconciliation & Backfill" in _GRADUATION_TEXT

    def test_step_0b_recap_pdf_section_present(self) -> None:
        """Step 0b (recap PDF generation) heading is present."""
        assert "## Step 0b: Recap PDF Generation" in _GRADUATION_TEXT

    def test_step_0b3_pdf_render_present(self) -> None:
        """Step 0b.3 (recap PDF render) sub-section is preserved."""
        assert "### Step 0b.3: PDF Generation" in _GRADUATION_TEXT

    def test_step_0b4_transcript_reconcile_then_render_present(self) -> None:
        """Step 0b.4 (transcript reconcile-then-render) sub-section is preserved."""
        assert (
            "### Step 0b.4: Q&A Transcript Reconciliation & Generation"
            in _GRADUATION_TEXT
        )

    def test_recap_reconcile_before_render_ordering_stated(self) -> None:
        """Step 0a states the recap is reconciled *then* the PDF is rendered."""
        assert (
            "reconcile/backfill the recap (this step) **then** render the PDF"
            in _GRADUATION_TEXT
        )

    def test_transcript_reconcile_before_render_ordering_stated(self) -> None:
        """Step 0b.4 states the transcript is reconciled *then* rendered."""
        assert (
            "reconcile the transcript (sub-step 1) **then** render it (sub-step 2)"
            in _GRADUATION_TEXT
        )


class TestGraduationIdempotentReuseNote:
    """The idempotent-reuse note added by Task 4.1 is present.

    The note clarifies that track completion now renders these deliverables,
    that Steps 0a/0b remain graduation-time safety nets, that reconciliation is
    idempotent, and that the renderers overwrite in place (no conflicting
    duplicates).

    Validates: Requirement 4.2
    """

    def test_idempotent_reuse_note_heading_present(self) -> None:
        """The dedicated idempotent-reuse note is present at Step 0b."""
        assert (
            "Note — idempotent reuse when track completion already generated "
            "these deliverables" in _GRADUATION_TEXT
        )

    def test_note_mentions_track_completion_renders_deliverables(self) -> None:
        """The note explains track completion renders the PDF and transcript."""
        assert "module-completion-track.md" in _GRADUATION_TEXT
        assert "docs/bootcamp_recap.pdf" in _GRADUATION_TEXT
        assert "docs/bootcamp_transcript.md" in _GRADUATION_TEXT

    def test_note_states_overwrite_in_place(self) -> None:
        """The note states renderers overwrite their output in place."""
        assert "overwrite" in _GRADUATION_LOWER
        assert "overwrite their output in place" in _GRADUATION_TEXT

    def test_note_states_no_conflicting_duplicates(self) -> None:
        """The note states re-running refreshes, without conflicting duplicates."""
        assert "conflicting duplicates" in _GRADUATION_LOWER
        # Refresh-not-duplicate framing is retained.
        assert "not creating conflicting duplicates" in _GRADUATION_TEXT

    def test_note_states_reconciliation_is_idempotent(self) -> None:
        """The note describes the reconciliation passes as idempotent no-ops."""
        assert "idempotent" in _GRADUATION_LOWER
        assert "no-op" in _GRADUATION_LOWER

    def test_note_preserves_safety_net_framing(self) -> None:
        """The note affirms Steps 0a/0b remain graduation-time safety nets."""
        assert "safety net" in _GRADUATION_LOWER
        assert (
            "does **not** remove or skip these graduation-time reconciliation "
            "safety nets" in _GRADUATION_TEXT
        )


class TestGraduationNoExternalUrls:
    """No external URLs were introduced (power-distribution safety).

    Validates: Requirement 4.2
    """

    def test_no_http_urls_present(self) -> None:
        """The steering file contains no ``http://`` or ``https://`` URLs."""
        urls = re.findall(r"https?://\S+", _GRADUATION_TEXT)
        assert urls == [], f"Unexpected external URL(s) in graduation.md: {urls}"
