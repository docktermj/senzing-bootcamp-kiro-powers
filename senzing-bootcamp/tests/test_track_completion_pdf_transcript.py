"""Property tests for the track-completion recap-PDF / Q&A-transcript sequence.

These tests quantify over the pure reference model in
``completion_sequence_model.py`` (co-located in this tests directory, not shipped
as a power script). They assert the always-generate, ordering, idempotence, and
non-blocking guarantees of the ``track-completion-pdf-transcript`` feature.

Example counts come from the active Hypothesis profile baseline (``fast`` locally,
``thorough`` in CI) — no hand-set ``@settings(max_examples=...)``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

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
    FAILABLE_STEPS,
    GRADUATION_OFFER,
    RECAP_PDF,
    RECAP_RECONCILE,
    TRANSCRIPT_RECONCILE,
    TRANSCRIPT_RENDER,
    SequenceInput,
    run_completion_sequence,
    run_graduation_sequence,
)

# Sorted list form of the failable steps for use as a strategy source.
_FAILABLE_STEPS = sorted(FAILABLE_STEPS)


@composite
def st_sequence_input(draw) -> SequenceInput:
    """Draw a :class:`SequenceInput` spanning the flow's varying dimensions.

    Draws random ``graduation_accepted``, ``skip_graduation``, and
    ``fpdf2_available`` booleans plus a random ``failing_steps`` subset of
    ``{recap_reconcile, transcript_reconcile, recap_pdf, transcript_render}``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`SequenceInput` with arbitrary flags and failing-step subset.
    """
    graduation_accepted = draw(st.booleans())
    skip_graduation = draw(st.booleans())
    fpdf2_available = draw(st.booleans())
    failing_steps = frozenset(
        draw(st.lists(st.sampled_from(_FAILABLE_STEPS), unique=True))
    )
    return SequenceInput(
        graduation_accepted=graduation_accepted,
        skip_graduation=skip_graduation,
        failing_steps=failing_steps,
        fpdf2_available=fpdf2_available,
    )


class TestTrackCompletionPdfTranscript:
    """Property tests over the completion/graduation reference model."""

    # Feature: track-completion-pdf-transcript, Property 1: Recap PDF and transcript
    # are always generated at track completion — over st_sequence_input(),
    # run_completion_sequence attempts both the recap_pdf and transcript_render steps
    # for every flag combination, and produces docs/bootcamp_recap.pdf /
    # docs/bootcamp_transcript.md when their steps do not fail (and fpdf2 is available
    # for the PDF).
    # Validates: Requirements 1.1, 1.3
    @given(inp=st_sequence_input())
    def test_recap_pdf_and_transcript_always_generated(self, inp: SequenceInput) -> None:
        """Both render steps are attempted regardless of graduation flags."""
        result = run_completion_sequence(inp)

        # Both render steps are attempted for every flag combination, independent
        # of graduation_accepted / skip_graduation (Requirements 1.1, 1.3).
        assert RECAP_PDF in result.executed
        assert TRANSCRIPT_RENDER in result.executed

        # The transcript artifact is produced whenever its step does not fail.
        if TRANSCRIPT_RENDER not in inp.failing_steps:
            assert ARTIFACT_TRANSCRIPT_MD in result.artifacts

        # The recap PDF is produced whenever its step does not fail and fpdf2 is
        # available for the render.
        if RECAP_PDF not in inp.failing_steps and inp.fpdf2_available:
            assert ARTIFACT_RECAP_PDF in result.artifacts

    # Feature: track-completion-pdf-transcript, Property 2: Reconcile-then-render
    # ordering is preserved in both flows — over st_sequence_input(), in the executed
    # order of both run_completion_sequence and run_graduation_sequence,
    # recap_reconcile precedes recap_pdf and transcript_reconcile precedes
    # transcript_render.
    # Validates: Requirements 1.2, 2.2
    @given(inp=st_sequence_input())
    def test_reconcile_then_render_ordering_in_both_flows(
        self, inp: SequenceInput
    ) -> None:
        """Reconcile always precedes render in both completion and graduation flows."""
        for result in (run_completion_sequence(inp), run_graduation_sequence(inp)):
            executed = result.executed
            # The recap PDF only renders after the recap reconciliation (Req 1.2, 2.2).
            assert executed.index(RECAP_RECONCILE) < executed.index(RECAP_PDF)
            # The transcript only renders after its reconciliation pass (Req 1.2, 2.2).
            assert executed.index(TRANSCRIPT_RECONCILE) < executed.index(
                TRANSCRIPT_RENDER
            )

    # Feature: track-completion-pdf-transcript, Property 3: Graduation after track
    # completion is idempotent — no conflicting duplicates — over st_sequence_input(),
    # running run_completion_sequence then run_graduation_sequence yields the same
    # final artifact set as track completion alone, and the graduation reconciliation
    # steps are no-ops on the already-consistent recap and log.
    # Validates: Requirements 2.1
    @given(inp=st_sequence_input())
    def test_graduation_reuse_is_idempotent(self, inp: SequenceInput) -> None:
        """Completion-then-graduation produces no conflicting duplicate artifacts."""
        completion = run_completion_sequence(inp)
        graduation = run_graduation_sequence(inp)

        # The final artifact set after track completion followed by graduation is the
        # union of what each run produces (both renderers overwrite in place, so a
        # graduation artifact refreshes the same path rather than adding a new one).
        # That union equals the track-completion artifact set alone — graduation
        # refreshes rather than duplicates the deliverables (Requirement 2.1).
        final_artifacts = completion.artifacts | graduation.artifacts
        assert final_artifacts == completion.artifacts

        # Graduation introduces no new or conflicting artifact paths beyond those
        # track completion already produced.
        assert graduation.artifacts <= completion.artifacts

        # The graduation reconciliation steps are no-ops on the already-consistent
        # recap and log: each reconcile artifact graduation would produce is a path
        # track completion already produced, so no second/conflicting copy appears.
        if RECAP_RECONCILE not in inp.failing_steps:
            assert ARTIFACT_RECAP_MD in completion.artifacts
        if TRANSCRIPT_RECONCILE not in inp.failing_steps:
            assert ARTIFACT_SESSION_LOG in completion.artifacts

    # Feature: track-completion-pdf-transcript, Property 4: Generation is non-blocking
    # under any failure — over st_sequence_input() with an arbitrary failing_steps
    # subset (including fpdf2_available=False), the sequence still attempts every
    # subsequent step in order and reaches the graduation offer, every artifact whose
    # step did not fail is still produced, and the Markdown recap is retained when the
    # recap PDF is skipped.
    # Validates: Requirements 3.1, 3.2
    @given(inp=st_sequence_input())
    def test_generation_is_non_blocking_under_failure(self, inp: SequenceInput) -> None:
        """Failures never abort the flow; non-failing artifacts are still produced."""
        result = run_completion_sequence(inp)

        # Non-blocking: every step is still attempted in order and the flow always
        # reaches the graduation offer, no matter which steps fail (Requirement 3.1).
        assert result.executed == [
            RECAP_RECONCILE,
            TRANSCRIPT_RECONCILE,
            RECAP_PDF,
            TRANSCRIPT_RENDER,
            GRADUATION_OFFER,
        ]
        assert GRADUATION_OFFER in result.executed

        # Every artifact whose producing step did not fail is still produced — a
        # failure in one step does not suppress the others (Requirement 3.1).
        if RECAP_RECONCILE not in inp.failing_steps:
            assert ARTIFACT_RECAP_MD in result.artifacts
        if TRANSCRIPT_RECONCILE not in inp.failing_steps:
            assert ARTIFACT_SESSION_LOG in result.artifacts
        if TRANSCRIPT_RENDER not in inp.failing_steps:
            assert ARTIFACT_TRANSCRIPT_MD in result.artifacts

        # The recap PDF is produced only when its step does not fail and fpdf2 is
        # available; otherwise it is suppressed while the flow continues.
        pdf_expected = RECAP_PDF not in inp.failing_steps and inp.fpdf2_available
        assert (ARTIFACT_RECAP_PDF in result.artifacts) == pdf_expected

        # When the recap PDF is skipped (its step failed or fpdf2 is absent), the
        # Markdown recap is retained as the graceful-degradation fallback — provided
        # the recap reconciliation itself did not fail (Requirement 3.2).
        if not pdf_expected and RECAP_RECONCILE not in inp.failing_steps:
            assert ARTIFACT_RECAP_MD in result.artifacts
