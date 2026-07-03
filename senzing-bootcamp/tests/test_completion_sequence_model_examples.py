"""Unit / example tests for the track-completion / graduation reference model.

These are concrete example tests (not Hypothesis property tests) exercising the
pure reference model in ``completion_sequence_model.py`` (co-located in this tests
directory, not shipped as a power script). They pin down the specific,
human-readable scenarios from the design's "Unit / example tests" section:

* exact executed order at track completion with graduation declined;
* ``skip_graduation=True`` still produces both renders while the graduation
  workflow is skipped;
* ``fpdf2`` absent skips the recap PDF, retains the Markdown recap, and still
  renders the transcript (graceful degradation);
* idempotent reuse — completion then graduation yields a single overwritten copy
  of each deliverable with no conflicting duplicate paths.

Requirements: 1.1, 1.2, 1.3, 2.1, 3.2
"""

from __future__ import annotations

import sys
from pathlib import Path

# The reference model is co-located in this tests directory. Ensure the tests
# directory is importable so ``completion_sequence_model`` resolves regardless of
# the pytest import mode / invocation cwd.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from completion_sequence_model import (  # noqa: E402
    ARTIFACT_RECAP_MD,
    ARTIFACT_RECAP_PDF,
    ARTIFACT_SESSION_LOG,
    ARTIFACT_TRANSCRIPT_MD,
    GRADUATION_OFFER,
    RECAP_PDF,
    RECAP_RECONCILE,
    TRANSCRIPT_RECONCILE,
    TRANSCRIPT_RENDER,
    SequenceInput,
    run_completion_sequence,
    run_graduation_sequence,
)


class TestCompletionSequenceExamples:
    """Concrete example scenarios for the track-completion flow."""

    def test_exact_order_when_graduation_declined(self) -> None:
        """Graduation declined: exact recap->transcript reconcile->renders order.

        The executed order must be recap_reconcile -> transcript_reconcile ->
        recap_pdf -> transcript_render -> graduation_offer, and both deliverables
        are produced. Renders do not depend on the graduation offer being accepted.

        Requirements: 1.1, 1.2
        """
        inp = SequenceInput(
            graduation_accepted=False,
            skip_graduation=False,
            failing_steps=frozenset(),
            fpdf2_available=True,
        )

        result = run_completion_sequence(inp)

        # Exact ordering at track completion (Requirement 1.2).
        assert result.executed == [
            RECAP_RECONCILE,
            TRANSCRIPT_RECONCILE,
            RECAP_PDF,
            TRANSCRIPT_RENDER,
            GRADUATION_OFFER,
        ]

        # Both shareable deliverables exist even though graduation was declined
        # (Requirement 1.1).
        assert ARTIFACT_RECAP_PDF in result.artifacts
        assert ARTIFACT_TRANSCRIPT_MD in result.artifacts

    def test_skip_graduation_still_renders_both(self) -> None:
        """skip_graduation=True still produces both renders at track completion.

        The skip_graduation preference gates only the graduation workflow, not the
        track-completion deliverables — both renders are still attempted and both
        artifacts are produced.

        Requirements: 1.3
        """
        inp = SequenceInput(
            graduation_accepted=False,
            skip_graduation=True,
            failing_steps=frozenset(),
            fpdf2_available=True,
        )

        result = run_completion_sequence(inp)

        # Both render steps are still attempted regardless of skip_graduation.
        assert RECAP_PDF in result.executed
        assert TRANSCRIPT_RENDER in result.executed

        # Both deliverables are produced (Requirement 1.3).
        assert ARTIFACT_RECAP_PDF in result.artifacts
        assert ARTIFACT_TRANSCRIPT_MD in result.artifacts

        # The track-completion sequence still reaches the graduation offer; the
        # skip applies to the graduation workflow that follows, not to the renders.
        assert GRADUATION_OFFER in result.executed

    def test_fpdf2_absent_skips_pdf_keeps_recap_and_renders_transcript(self) -> None:
        """fpdf2 absent: skip recap PDF, keep the Markdown recap, render transcript.

        Graceful degradation — when fpdf2 is unavailable the recap PDF artifact is
        suppressed while the recap_pdf step is still attempted and the ordering is
        unchanged; the Markdown recap is retained and the transcript still renders.

        Requirements: 3.2
        """
        inp = SequenceInput(
            graduation_accepted=False,
            skip_graduation=False,
            failing_steps=frozenset(),
            fpdf2_available=False,
        )

        result = run_completion_sequence(inp)

        # The recap PDF step is still attempted (ordering unaffected) ...
        assert RECAP_PDF in result.executed
        # ... but the PDF artifact is not produced when fpdf2 is absent.
        assert ARTIFACT_RECAP_PDF not in result.artifacts

        # The Markdown recap is retained.
        assert ARTIFACT_RECAP_MD in result.artifacts

        # The transcript still renders (its render is independent of fpdf2).
        assert ARTIFACT_TRANSCRIPT_MD in result.artifacts

    def test_idempotent_reuse_no_conflicting_duplicates(self) -> None:
        """Completion then graduation yields a single overwritten copy of each.

        Running the completion sequence then the graduation sequence produces the
        same final artifact set as track completion alone — the renderers overwrite
        in place and the reconciliation steps are no-ops on consistent inputs, so no
        conflicting duplicate paths appear.

        Requirements: 2.1
        """
        inp = SequenceInput(
            graduation_accepted=True,
            skip_graduation=False,
            failing_steps=frozenset(),
            fpdf2_available=True,
        )

        completion = run_completion_sequence(inp)
        graduation = run_graduation_sequence(inp)

        # Graduation reuses the exact same artifact paths track completion produced;
        # the union adds nothing new (single, overwritten copy of each deliverable).
        assert graduation.artifacts <= completion.artifacts
        assert (completion.artifacts | graduation.artifacts) == completion.artifacts

        # Each deliverable exists exactly once (as a distinct path). Comparing the
        # frozenset against the sorted list of both runs' paths confirms there are no
        # conflicting duplicate paths introduced by graduation.
        combined_paths = sorted(completion.artifacts) + sorted(graduation.artifacts)
        assert len(set(combined_paths)) == len(completion.artifacts)

        # All four canonical deliverables are present as single overwritten copies.
        assert completion.artifacts == frozenset(
            {
                ARTIFACT_RECAP_MD,
                ARTIFACT_SESSION_LOG,
                ARTIFACT_RECAP_PDF,
                ARTIFACT_TRANSCRIPT_MD,
            }
        )
