"""Property test for bold-marker-transparent compound-question validation.

Feature: onboarding-session-ux, Property 3: Bold-marker-transparent validation

This module validates that CommonMark bold (``**``) markers are transparent to
the write-policy-gate's single/compound-question validation. The gate strips all
``**`` markers *before* validating (CHECK 2), so the presence or absence of bold
emphasis must never change the verdict for otherwise-identical wording.

The property drives :func:`helpers.bold_format.strip_bold_markers` against a mock
compound-question validator defined in this module. The validator mirrors the
write-policy-gate CHECK 2 logic on marker-stripped wording: it counts ``?``
question marks (rule 1) and detects joining conjunctions between clauses
(rule 2). The invariant under test: injecting extra ``**`` markers at arbitrary
positions cannot change the verdict once markers are stripped.

**Validates: Requirements 5.1, 5.2, 5.3**
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make the test-helpers package importable (senzing-bootcamp/tests on sys.path)
# ---------------------------------------------------------------------------
# The bold-format helper lives in ``senzing-bootcamp/tests/helpers/``. Adding the
# tests directory to ``sys.path`` lets it resolve as the top-level ``helpers``
# package regardless of the pytest import mode or invocation cwd, matching the
# sibling-module import pattern used elsewhere in this suite.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from helpers.bold_format import strip_bold_markers  # noqa: E402

# Conjunctions that join two question clauses into one compound question. The
# write-policy-gate CHECK 2 detects these on the marker-stripped wording.
_JOINING_CONJUNCTIONS: tuple[str, ...] = (" and ", " or ", " and/or ")

# Wording alphabet for the plain generator: lowercase letters, spaces, ``?`` and
# ``*``. Including ``?`` exercises the zero/one/many question-mark verdicts, and
# including ``*`` means inputs may already carry stray ``*`` or ``**`` runs before
# any injection.
_WORDING_ALPHABET = "abcdefghijklmnopqrstuvwxyz ?*"


def mock_single_question_verdict(stripped_text: str) -> bool:
    """Return whether ``stripped_text`` passes single-question validation.

    A mock of the write-policy-gate CHECK 2 single-question rule, operating on
    already marker-stripped wording (the caller strips ``**`` first, mirroring
    the gate's "strip before evaluating" ordering). The wording passes when it
    contains exactly one ``?`` (rule 1) and no joining conjunction that would
    splice two clauses into a compound question (rule 2).

    Args:
        stripped_text: Question wording with all ``**`` bold markers removed.

    Returns:
        ``True`` if the wording reads as a single question, ``False`` if it is
        empty, question-mark-free, multi-question, or conjunction-joined.
    """
    question_mark_count = stripped_text.count("?")
    has_joining_conjunction = any(
        conjunction in stripped_text.lower() for conjunction in _JOINING_CONJUNCTIONS
    )
    return question_mark_count == 1 and not has_joining_conjunction


@st.composite
def st_compound_wording(draw) -> str:
    """Draw two clauses joined by a conjunction, each optionally ending in ``?``.

    This deliberately manufactures compound-shaped wording so the property
    exercises the ``False`` (compound) verdict branch as well as the ``True``
    branch, rather than relying on rare conjunction runs from random letters.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A wording string of the form ``"{left}{?} {conj} {right}{?}"``.
    """
    clause = st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", max_size=15)
    left = draw(clause)
    right = draw(clause)
    conjunction = draw(st.sampled_from(_JOINING_CONJUNCTIONS))
    left_mark = "?" if draw(st.booleans()) else ""
    right_mark = "?" if draw(st.booleans()) else ""
    return f"{left}{left_mark}{conjunction}{right}{right_mark}"


# Base wording: broad random text (may already contain ``*``/``**``/``?``) mixed
# with deliberately compound-shaped wording for verdict variety.
st_wording = st.one_of(
    st.text(alphabet=_WORDING_ALPHABET, max_size=120),
    st_compound_wording(),
)


@st.composite
def st_text_with_injected_bold(draw) -> tuple[str, str]:
    """Draw ``(base, injected)`` where ``injected`` adds ``**`` at random spots.

    ``injected`` is ``base`` with zero or more ``**`` markers spliced in at
    arbitrary character positions, modeling a bootcamper-facing question that has
    been wrapped (or partially wrapped) in bold emphasis.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(base, injected)`` pair of wording strings that differ only by the
        presence of injected ``**`` bold markers.
    """
    base = draw(st_wording)
    injection_count = draw(st.integers(min_value=0, max_value=6))
    injected = base
    for _ in range(injection_count):
        position = draw(st.integers(min_value=0, max_value=len(injected)))
        injected = f"{injected[:position]}**{injected[position:]}"
    return base, injected


class TestBoldMarkerTransparentValidation:
    """Property 3 — bold markers are transparent to compound-question validation.

    Feature: onboarding-session-ux, Property 3: Bold-marker-transparent validation

    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    @given(pair=st_text_with_injected_bold())
    def test_injected_bold_markers_do_not_change_verdict(
        self, pair: tuple[str, str]
    ) -> None:
        """Stripping ``**`` before validation yields the same verdict either way.

        For any wording, validating it after stripping bold markers must produce
        the identical single/compound verdict whether or not extra ``**`` markers
        were injected first. This is the invariance the write-policy-gate relies
        on: bold emphasis cannot weaken (or strengthen) the single-question check.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        base, injected = pair
        base_verdict = mock_single_question_verdict(strip_bold_markers(base))
        injected_verdict = mock_single_question_verdict(strip_bold_markers(injected))
        assert base_verdict == injected_verdict, (
            "Bold-marker injection changed the compound-question verdict: "
            f"base={base!r} -> {base_verdict}, injected={injected!r} -> {injected_verdict}"
        )
