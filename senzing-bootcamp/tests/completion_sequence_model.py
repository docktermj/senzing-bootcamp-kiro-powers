"""Pure reference model of the track-completion / graduation deliverable sequence.

This is a **test-only** helper co-located with the tests for the
``track-completion-pdf-transcript`` feature. It is *not* shipped as a power script
and performs **no** real I/O — it is a specification of the intended steering order
that the property and unit tests quantify over.

The model captures the sequence as an ordered list of attempted steps plus the
resulting artifact set, parameterized by the inputs that vary the flow. Two flows
are modeled:

* :func:`run_completion_sequence` — the ``module-completion-track.md`` track-completion
  order: ``recap_reconcile`` -> ``transcript_reconcile`` -> ``recap_pdf``,
  ``transcript_render``, then the graduation offer. Renders are attempted regardless
  of ``graduation_accepted`` / ``skip_graduation``; any failing step is still
  "attempted" and never aborts the remaining steps (non-blocking); ``fpdf2_available``
  affects only the ``recap_pdf`` artifact, never the ordering.
* :func:`run_graduation_sequence` — the ``graduation.md`` Step 0a/0b idempotent reuse:
  ``recap_reconcile`` -> ``recap_pdf``, ``transcript_reconcile`` -> ``transcript_render``,
  overwriting in place.

Both flows encode the reconcile-then-render ordering constraints:
``index(recap_reconcile) < index(recap_pdf)`` and
``index(transcript_reconcile) < index(transcript_render)``.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Step and artifact vocabulary
# ---------------------------------------------------------------------------

Step = str  # e.g. "recap_reconcile", "transcript_reconcile", "recap_pdf", ...

# Canonical step names.
RECAP_RECONCILE: Step = "recap_reconcile"
TRANSCRIPT_RECONCILE: Step = "transcript_reconcile"
RECAP_PDF: Step = "recap_pdf"
TRANSCRIPT_RENDER: Step = "transcript_render"
GRADUATION_OFFER: Step = "graduation_offer"

# The steps that may appear in ``SequenceInput.failing_steps``.
FAILABLE_STEPS: frozenset[Step] = frozenset(
    {RECAP_RECONCILE, TRANSCRIPT_RECONCILE, RECAP_PDF, TRANSCRIPT_RENDER}
)

# Canonical artifact paths (relative to the project root).
ARTIFACT_RECAP_MD: str = "docs/bootcamp_recap.md"
ARTIFACT_SESSION_LOG: str = "config/session_log.jsonl"
ARTIFACT_RECAP_PDF: str = "docs/bootcamp_recap.pdf"
ARTIFACT_TRANSCRIPT_MD: str = "docs/bootcamp_transcript.md"

# Which artifact each step produces when it does not fail.
_STEP_ARTIFACT: dict[Step, str] = {
    RECAP_RECONCILE: ARTIFACT_RECAP_MD,
    TRANSCRIPT_RECONCILE: ARTIFACT_SESSION_LOG,
    RECAP_PDF: ARTIFACT_RECAP_PDF,
    TRANSCRIPT_RENDER: ARTIFACT_TRANSCRIPT_MD,
}


# ---------------------------------------------------------------------------
# Model inputs / outputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SequenceInput:
    """The dimensions that vary the completion / graduation flow.

    Attributes:
        graduation_accepted: Did the bootcamper accept the graduation offer?
        skip_graduation: The ``config/bootcamp_preferences.yaml`` ``skip_graduation``
            preference. Gates only the graduation workflow, never the track-completion
            renders.
        failing_steps: Steps that fail this run (``fpdf2`` absent, filesystem error, ...).
            A failing step is still attempted and never aborts the remaining steps.
        fpdf2_available: Affects only whether the ``recap_pdf`` artifact is produced;
            never affects step ordering or whether the sequence completes.
    """

    graduation_accepted: bool
    skip_graduation: bool
    failing_steps: frozenset[str]
    fpdf2_available: bool


@dataclass(frozen=True)
class SequenceResult:
    """The outcome of modeling a flow.

    Attributes:
        executed: Steps attempted, in order. Failing steps are still "attempted"
            and therefore still appear here.
        artifacts: Deliverables that exist after the run.
    """

    executed: list[Step]
    artifacts: frozenset[str]


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _artifact_for(step: Step, inp: SequenceInput) -> str | None:
    """Return the artifact produced by ``step`` this run, or ``None``.

    A step produces its artifact only when it does not fail. The ``recap_pdf`` step
    additionally requires ``fpdf2`` to be available — when it is absent the PDF
    artifact is suppressed while the step is still attempted and the ordering is
    unchanged.

    Args:
        step: The step being evaluated.
        inp: The flow inputs.

    Returns:
        The artifact path produced by ``step``, or ``None`` when the step fails
        (or, for ``recap_pdf``, when ``fpdf2`` is unavailable).
    """
    if step in inp.failing_steps:
        return None
    if step == RECAP_PDF and not inp.fpdf2_available:
        return None
    return _STEP_ARTIFACT.get(step)


# ---------------------------------------------------------------------------
# Flow models
# ---------------------------------------------------------------------------


def run_completion_sequence(inp: SequenceInput) -> SequenceResult:
    """Model the ``module-completion-track.md`` track-completion order.

    The order is ``recap_reconcile`` -> ``transcript_reconcile`` -> ``recap_pdf``,
    ``transcript_render``, then the graduation offer. Both render steps are attempted
    regardless of ``graduation_accepted`` / ``skip_graduation``. Any step in
    ``failing_steps`` is still "attempted" (it appears in ``executed``) and never
    aborts the remaining steps — the sequence is non-blocking and always reaches the
    graduation offer. ``fpdf2_available=False`` suppresses only the ``recap_pdf``
    artifact, never the ordering.

    Args:
        inp: The flow inputs.

    Returns:
        The attempted steps in order and the artifact set that exists afterward.
    """
    executed: list[Step] = [
        RECAP_RECONCILE,
        TRANSCRIPT_RECONCILE,
        RECAP_PDF,
        TRANSCRIPT_RENDER,
        GRADUATION_OFFER,
    ]

    artifacts: set[str] = set()
    for step in (RECAP_RECONCILE, TRANSCRIPT_RECONCILE, RECAP_PDF, TRANSCRIPT_RENDER):
        artifact = _artifact_for(step, inp)
        if artifact is not None:
            artifacts.add(artifact)

    return SequenceResult(executed=executed, artifacts=frozenset(artifacts))


def run_graduation_sequence(inp: SequenceInput) -> SequenceResult:
    """Model the ``graduation.md`` Step 0a/0b idempotent reuse.

    The order is ``recap_reconcile`` -> ``recap_pdf`` (Step 0a then Step 0b.3), then
    ``transcript_reconcile`` -> ``transcript_render`` (Step 0b.4). The renderers
    overwrite their output in place rather than appending, and the reconciliation
    steps are no-ops on already-consistent inputs, so a graduation run after track
    completion refreshes rather than duplicates the deliverables. Performs no real
    I/O.

    Args:
        inp: The flow inputs.

    Returns:
        The attempted steps in order and the artifact set that exists afterward.
    """
    executed: list[Step] = [
        RECAP_RECONCILE,
        RECAP_PDF,
        TRANSCRIPT_RECONCILE,
        TRANSCRIPT_RENDER,
    ]

    artifacts: set[str] = set()
    for step in (RECAP_RECONCILE, RECAP_PDF, TRANSCRIPT_RECONCILE, TRANSCRIPT_RENDER):
        artifact = _artifact_for(step, inp)
        if artifact is not None:
            artifacts.add(artifact)

    return SequenceResult(executed=executed, artifacts=frozenset(artifacts))
