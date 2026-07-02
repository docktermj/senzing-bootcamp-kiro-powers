"""Tests for the Advanced Track Knowledge Check feature (Step 5c).

This module verifies the branch decision the ``5c. Advanced Track Knowledge
Check`` sub-step encodes and (in later tasks) the structural placement and
content of that sub-step in ``onboarding-phase2-track-setup.md``.

The Knowledge_Check is presented **only** for the Advanced track
(``advanced_topics``), inserted after the Step 5 Track Selection gate resolves
and before Module 1. A correct answer earns a brief affirmation; an incorrect
or unsure answer earns a short Re_Explanation. Either way the flow proceeds to
Module 1 — the Knowledge_Check is never a Mandatory_Gate and never blocks.

Because the feature is steering-driven (authored prose, not a runtime script),
the branch logic is captured here as a small, pure **reference model** defined
in this test module only — it is not shipped in the distributed power path
under ``senzing-bootcamp/`` runtime scripts. Property tests exercise the model;
content tests (added by later tasks) keep the model faithful to the authored
steering.

Feature: advanced-track-knowledge-check
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (project convention; harmless if unused here)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Steering file helpers
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"

_ONBOARDING_PHASE2_FILE = _STEERING_DIR / "onboarding-phase2-track-setup.md"

_STEERING_INDEX_FILE = _STEERING_DIR / "steering-index.yaml"


def _read_phase2() -> str:
    """Return the full text of onboarding-phase2-track-setup.md."""
    return _ONBOARDING_PHASE2_FILE.read_text(encoding="utf-8")


def _read_steering_index() -> str:
    """Return the full text of steering-index.yaml."""
    return _STEERING_INDEX_FILE.read_text(encoding="utf-8")


def _extract_section(text: str, heading_pattern: str) -> str:
    """Extract a markdown section by its heading regex.

    Returns everything from the matched heading up to (but not including) the
    next heading of the same or higher level.

    Args:
        text: Full markdown text to search.
        heading_pattern: Regex matching the heading title (after the ``#`` run).

    Returns:
        The section text including its heading line.
    """
    pattern = r"^(#{2,3})\s+" + heading_pattern
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        pytest.fail(f"Could not find section matching: {heading_pattern}")

    level = len(match.group(1))  # 2 for ##, 3 for ###
    start = match.start()

    rest = text[match.end():]
    next_heading = re.search(
        r"^#{1," + str(level) + r"}\s",
        rest,
        re.MULTILINE,
    )
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[start:end]


# ---------------------------------------------------------------------------
# Test-only reference decision model
# ---------------------------------------------------------------------------
#
# This models exactly what Step 5c instructs: gate on the persisted ``track``,
# branch on the answer class, and always proceed to Module 1. It is defined in
# the test module only and is NOT shipped in the distributed power runtime path.

Track = str  # "advanced_topics" | "core_bootcamp" (and unknown values)
AnswerClass = str  # "correct" | "incorrect" | "unsure"


def presents_knowledge_check(track: str) -> bool:
    """Return True iff the Advanced track was selected (Reqs 1.1, 1.2).

    Args:
        track: The persisted track value.

    Returns:
        True only when ``track`` is the Advanced track (``advanced_topics``);
        every other value (Core, unknown, empty) returns False.
    """
    return track == "advanced_topics"


@dataclass(frozen=True)
class CheckOutcome:
    """The modeled outcome of the Step 5c branch decision.

    Attributes:
        presented: Whether a question was shown.
        branch: ``"affirm"``, ``"re_explanation"``, or ``None`` (not presented).
        re_explanation: Whether a Re_Explanation was offered.
        proceeds_to_module_1: Always True — the check never blocks (Req 2.4).
    """

    presented: bool
    branch: str | None
    re_explanation: bool
    proceeds_to_module_1: bool


def resolve_knowledge_check(track: str, answer: str | None) -> CheckOutcome:
    """Model Step 5c: gate on track, branch on answer, always proceed.

    Args:
        track: The persisted track value.
        answer: The classified answer (``"correct"``/``"incorrect"``/
            ``"unsure"``) or ``None`` for no answer.

    Returns:
        The :class:`CheckOutcome` for the given input. Core and unknown tracks
        are skipped (not presented); on the Advanced track a correct answer
        affirms while any other answer triggers a Re_Explanation. Every input
        proceeds to Module 1.
    """
    if not presents_knowledge_check(track):
        return CheckOutcome(False, None, False, True)  # Core: skipped, proceed
    if answer == "correct":
        return CheckOutcome(True, "affirm", False, True)
    # incorrect, unsure, or no answer -> Re_Explanation, then proceed
    return CheckOutcome(True, "re_explanation", True, True)


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_KNOWN_TRACKS = ("advanced_topics", "core_bootcamp")


@st.composite
def st_track(draw: st.DrawFn) -> str:
    """Draw a track value spanning the full input space.

    Samples the two known tracks (``advanced_topics``, ``core_bootcamp``) plus
    arbitrary/unknown strings and the empty string, so gating (Property 1) and
    the never-blocks contract (Property 4) are exercised across every track
    shape, not just the happy-path values. Values are synthetic and PII-free.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A track string.
    """
    return draw(
        st.one_of(
            st.sampled_from(_KNOWN_TRACKS),
            st.just(""),
            st.text(max_size=20),
        )
    )


@st.composite
def st_answer_class(draw: st.DrawFn) -> str | None:
    """Draw an answer class, including the no-answer case.

    Samples ``"correct"``, ``"incorrect"``, ``"unsure"``, and ``None`` (no
    answer) so the branch properties (2, 3) and the never-blocks property (4)
    see every answer shape. Values are synthetic and PII-free.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One of ``"correct"``, ``"incorrect"``, ``"unsure"``, or ``None``.
    """
    return draw(st.sampled_from(["correct", "incorrect", "unsure", None]))


# ---------------------------------------------------------------------------
# Smoke test — module imports cleanly and the model is wired up
# ---------------------------------------------------------------------------


class TestReferenceModelSmoke:
    """Sanity checks that the reference model and strategies are importable.

    These are placeholder-level checks; the universal properties (Tasks
    4.2–4.5) and content/flow tests (Tasks 5.x) fill in the real coverage.
    """

    def test_presents_knowledge_check_advanced_only(self) -> None:
        """The guard is true for Advanced and false for Core."""
        assert presents_knowledge_check("advanced_topics") is True
        assert presents_knowledge_check("core_bootcamp") is False

    def test_resolve_always_proceeds(self) -> None:
        """A representative outcome proceeds to Module 1."""
        outcome = resolve_knowledge_check("advanced_topics", "correct")
        assert isinstance(outcome, CheckOutcome)
        assert outcome.proceeds_to_module_1 is True

    @given(track=st_track(), answer=st_answer_class())
    def test_strategies_produce_resolvable_inputs(
        self, track: str, answer: str | None
    ) -> None:
        """Both strategies feed the model without error and return an outcome."""
        outcome = resolve_knowledge_check(track, answer)
        assert isinstance(outcome, CheckOutcome)


# ---------------------------------------------------------------------------
# Property 1: Advanced-only presentation
# ---------------------------------------------------------------------------


class TestProperty1AdvancedOnlyPresentation:
    """Property 1: the Knowledge_Check is presented iff the track is Advanced.

    Validates: Requirements 1.1, 1.2 — the check is presented for the Advanced
    track (``advanced_topics``) and never for the Core track or any other /
    unknown track value.
    """

    # Feature: advanced-track-knowledge-check, Property 1: Advanced-only presentation
    @given(track=st_track())
    def test_presents_knowledge_check_iff_advanced(self, track: str) -> None:
        """``presents_knowledge_check`` is true iff ``track == "advanced_topics"``.

        Args:
            track: A track value drawn across the full input space.
        """
        assert presents_knowledge_check(track) == (track == "advanced_topics")


# ---------------------------------------------------------------------------
# Property 2: Correct answers affirm and proceed
# ---------------------------------------------------------------------------


class TestProperty2CorrectAnswersAffirm:
    """Property 2: a correct answer on the Advanced track affirms and proceeds.

    Validates: Requirements 2.2 — when the bootcamper answers correctly on the
    Advanced track, the flow selects the ``affirm`` branch (no Re_Explanation)
    and proceeds to Module 1.
    """

    # Feature: advanced-track-knowledge-check, Property 2: Correct answers affirm and proceed
    @given(answer=st.just("correct"))
    def test_correct_answer_affirms_and_proceeds(self, answer: str) -> None:
        """A correct Advanced-track answer affirms with no Re_Explanation.

        Args:
            answer: The correct answer class (constant ``"correct"``).
        """
        outcome = resolve_knowledge_check("advanced_topics", answer)
        assert outcome.branch == "affirm"
        assert outcome.re_explanation is False
        assert outcome.proceeds_to_module_1 is True

# ---------------------------------------------------------------------------
# Property 3: Incorrect or unsure answers trigger a Re_Explanation and proceed
# ---------------------------------------------------------------------------


class TestProperty3IncorrectUnsureReExplanation:
    """Property 3: incorrect/unsure/no answers trigger a Re_Explanation and proceed.

    Validates: Requirements 2.3 — when the bootcamper answers incorrectly, is
    unsure, or gives no answer on the Advanced track, the flow selects the
    ``re_explanation`` branch and still proceeds to Module 1.
    """

    # Feature: advanced-track-knowledge-check, Property 3: Incorrect or unsure answers trigger a Re_Explanation and proceed
    @given(answer=st.sampled_from(["incorrect", "unsure", None]))
    def test_incorrect_unsure_triggers_re_explanation(
        self, answer: str | None
    ) -> None:
        """A non-correct Advanced-track answer re-explains, then proceeds.

        Args:
            answer: A non-correct answer class (``"incorrect"``, ``"unsure"``,
                or ``None`` for no answer).
        """
        outcome = resolve_knowledge_check("advanced_topics", answer)
        assert outcome.branch == "re_explanation"
        assert outcome.re_explanation is True
        assert outcome.proceeds_to_module_1 is True


# ---------------------------------------------------------------------------
# Property 4: The Knowledge_Check never blocks
# ---------------------------------------------------------------------------


class TestProperty4NeverBlocks:
    """Property 4: no ``(track, answer)`` pair ever blocks the flow.

    Validates: Requirements 2.4 — for every track (Advanced, Core, unknown,
    empty) and every answer (correct, incorrect, unsure, or none), the outcome
    proceeds to Module 1. There is no input for which the flow is blocked.
    """

    # Feature: advanced-track-knowledge-check, Property 4: The Knowledge_Check never blocks
    @given(track=st_track(), answer=st_answer_class())
    def test_never_blocks(self, track: str, answer: str | None) -> None:
        """Every ``(track, answer)`` pair proceeds to Module 1.

        Args:
            track: A track value drawn across the full input space.
            answer: An answer class (``"correct"``/``"incorrect"``/``"unsure"``)
                or ``None`` for no answer.
        """
        assert resolve_knowledge_check(track, answer).proceeds_to_module_1 is True


# ---------------------------------------------------------------------------
# Content / flow tests — placement and Advanced-only guard (Task 5.1)
# ---------------------------------------------------------------------------


class TestPlacementAndGuard:
    """Content tests pinning Step 5c placement and the Advanced-only guard.

    These example-based (non-Hypothesis) tests read the real bundled steering
    file ``onboarding-phase2-track-setup.md`` and assert the structural facts
    the design fixes in prose, keeping the reference model faithful to the
    authored flow.

    Validates:
        Requirements 1.1, 1.2, 1.3 — the ``5c. Advanced Track Knowledge Check``
        section exists, is positioned after ``## 5. Track Selection`` and before
        ``## Switching Tracks``, states the check precedes Module 1, scopes the
        check to the Advanced track (``advanced_topics``), and states the Core
        track (``core_bootcamp``) skips it and is unchanged.
    """

    def test_knowledge_check_heading_exists(self) -> None:
        """The ``5c. Advanced Track Knowledge Check`` heading is present (Req 1.1)."""
        text = _read_phase2()
        assert "## 5c. Advanced Track Knowledge Check" in text

    def test_heading_positioned_after_track_selection_before_switching(self) -> None:
        """5c sits after Track Selection and before Switching Tracks (Reqs 1.1, 1.3).

        Uses ``str.index()`` on the full text to compare heading offsets, so the
        section is anchored between the resolved track-selection gate and the
        ``## Switching Tracks`` appendix.
        """
        text = _read_phase2()
        track_selection_idx = text.index("## 5. Track Selection")
        knowledge_check_idx = text.index("## 5c. Advanced Track Knowledge Check")
        switching_tracks_idx = text.index("## Switching Tracks")

        assert track_selection_idx < knowledge_check_idx, (
            "5c must appear after '## 5. Track Selection'"
        )
        assert knowledge_check_idx < switching_tracks_idx, (
            "5c must appear before '## Switching Tracks'"
        )

    def test_section_states_check_precedes_module_1(self) -> None:
        """The 5c section states the check precedes Module 1 (Reqs 1.1, 1.3)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "Module 1" in section

    def test_section_scopes_check_to_advanced_track(self) -> None:
        """The section scopes the check to the Advanced track (Req 1.1)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "advanced_topics" in section

    def test_section_states_core_track_skips_and_unchanged(self) -> None:
        """The section states the Core track skips the check / is unchanged (Req 1.2)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "core_bootcamp" in section
        lowered = section.lower()
        assert "skip" in lowered, "section must state the Core track skips the check"
        assert "unchanged" in lowered, "section must state Core onboarding is unchanged"


# ---------------------------------------------------------------------------
# Content / flow tests — single question, tone, and branch docs (Task 5.2)
# ---------------------------------------------------------------------------


class TestSingleQuestionToneAndBranches:
    """Content tests pinning the single question, tone, and branch docs of 5c.

    These example-based (non-Hypothesis) tests read the real bundled steering
    file ``onboarding-phase2-track-setup.md``, extract the ``5c. Advanced Track
    Knowledge Check`` section, and assert the prose the design fixes: exactly
    one warm ``👉``-prefixed ER question in non-quiz framing, plus documented
    affirm-and-proceed and Re_Explanation-and-proceed branches. They keep the
    reference model faithful to the authored flow.

    Validates:
        Requirements 2.1, 2.2, 2.3, 3.1 — the section asks a single
        ``👉``-prefixed question about a core ER concept in a warm, non-quiz
        tone (2.1, 3.1), documents affirming and proceeding to Module 1 on a
        correct answer (2.2), and documents a Re_Explanation before proceeding
        on an incorrect/unsure answer (2.3).
    """

    def test_section_contains_exactly_one_pointer_question(self) -> None:
        """The section carries exactly one ``👉``-prefixed question (Reqs 2.1, 3.1).

        The section mentions the ``👉`` marker inline while describing the
        required output format, so a raw occurrence count is not meaningful.
        What must be singular is the actual ``👉``-*prefixed* question: a line
        that begins with the marker and asks a question. Exactly one such line
        (the fenced example) is authored.
        """
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        pointer_questions = [
            line
            for line in section.splitlines()
            if line.lstrip().startswith("👉") and "?" in line
        ]
        assert len(pointer_questions) == 1

    def test_section_references_core_er_concept(self) -> None:
        """The single question targets a core ER concept (Req 2.1)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        lowered = section.lower()
        assert "entity resolution" in lowered
        assert "same real-world entity" in lowered

    def test_section_carries_non_quiz_framing(self) -> None:
        """The section frames the check as a friendly gut-check, not a quiz (Reqs 2.1, 3.1)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        lowered = section.lower()
        assert "gut-check" in lowered
        assert "not a quiz" in lowered

    def test_section_documents_affirm_and_proceed_path(self) -> None:
        """The section documents affirming and proceeding on a correct answer (Req 2.2)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        lowered = section.lower()
        assert "affirm" in lowered
        assert "module 1" in lowered

    def test_section_documents_re_explanation_and_proceed_path(self) -> None:
        """The section documents a Re_Explanation before proceeding on incorrect/unsure (Req 2.3)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        lowered = section.lower()
        assert "re_explanation" in lowered
        assert "proceed to module 1" in lowered


# ---------------------------------------------------------------------------
# Content / flow tests — non-gate contract + hook/verbosity notes (Task 5.3)
# ---------------------------------------------------------------------------


class TestNonGateContractAndHookVerbosity:
    """Content tests pinning the non-gate contract and hook/verbosity notes of 5c.

    These example-based (non-Hypothesis) tests read the real bundled steering
    file ``onboarding-phase2-track-setup.md``, extract the ``5c. Advanced Track
    Knowledge Check`` section, and assert the prose the design fixes: the
    section carries no gate markers (mirroring the Step 5b non-gate contract
    test in ``test_comprehension_check.py``), references the ``ask-bootcamper``
    closing-question note, and instructs applying the bootcamper's current
    verbosity settings when giving the Re_Explanation. They keep the reference
    model faithful to the never-blocks contract.

    Validates:
        Requirements 2.4, 3.1, 3.3 — Step 5c is NOT a mandatory gate and never
        prevents continuing (no ``⛔``, no ``MUST stop``, no ``mandatory gate``,
        no ``MUST NOT proceed``, and no ``WAIT``) (2.4), notes that the
        ``ask-bootcamper`` hook owns the closing question (3.1), and instructs
        applying the bootcamper's current verbosity settings (3.3).
    """

    # -- Gate keyword / WAIT marker absence (Req 2.4) --

    def test_no_gate_emoji(self) -> None:
        """The 5c section must not contain the ``⛔`` mandatory gate marker (Req 2.4)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "⛔" not in section, (
            "Step 5c contains ⛔ gate marker but is not a mandatory gate"
        )

    def test_no_must_stop_keyword(self) -> None:
        """The 5c section must not contain 'MUST stop' gate language (Req 2.4)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "MUST stop" not in section, (
            "Step 5c contains 'MUST stop' gate language but is not a mandatory gate"
        )

    def test_no_mandatory_gate_keyword(self) -> None:
        """The 5c section must not contain 'mandatory gate' language (Req 2.4)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "mandatory gate" not in section.lower(), (
            "Step 5c contains 'mandatory gate' language but is not a mandatory gate"
        )

    def test_no_must_not_proceed_keyword(self) -> None:
        """The 5c section must not contain 'MUST NOT proceed' gate language (Req 2.4)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "MUST NOT proceed" not in section, (
            "Step 5c contains 'MUST NOT proceed' gate language "
            "but is not a mandatory gate"
        )

    def test_no_wait_instruction(self) -> None:
        """The 5c section must not contain a WAIT instruction (Req 2.4)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "WAIT" not in section, (
            "Step 5c contains WAIT instruction "
            "but the ask-bootcamper hook handles closing questions"
        )

    # -- Hook + verbosity notes (Reqs 3.1, 3.3) --

    def test_references_ask_bootcamper_closing_question_note(self) -> None:
        """The 5c section references the ``ask-bootcamper`` closing-question note (Req 3.1)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "ask-bootcamper" in section, (
            "Step 5c missing note that the ask-bootcamper hook handles "
            "the closing question"
        )

    def test_instructs_applying_current_verbosity_settings(self) -> None:
        """The 5c section instructs applying current verbosity settings (Req 3.3)."""
        section = _extract_section(
            _read_phase2(), r"5c\. Advanced Track Knowledge Check"
        )
        assert "verbosity" in section.lower(), (
            "Step 5c missing instruction to apply the bootcamper's current "
            "verbosity settings when giving the Re_Explanation"
        )


# ---------------------------------------------------------------------------
# Content / flow tests — steering index sync (Task 5.4)
# ---------------------------------------------------------------------------


class TestSteeringIndexSync:
    """Content tests pinning the steering-index.yaml entries for the modified file.

    These example-based (non-Hypothesis) tests read the real bundled
    ``steering-index.yaml`` and assert that both index entries referencing the
    modified steering file ``onboarding-phase2-track-setup.md`` are present: the
    ``phase2-track-setup`` phase entry under ``onboarding`` and the
    ``file_metadata`` entry. CI's ``measure_steering.py --check`` separately
    enforces that the recorded token counts match the file; these tests keep
    the two entries wired up so that enforcement has something to check.

    Validates:
        Requirement 3.2 — the feature updates the affected steering file token
        counts in ``steering-index.yaml``; both the ``phase2-track-setup`` phase
        entry and the ``file_metadata`` entry for
        ``onboarding-phase2-track-setup.md`` exist for the modified file.
    """

    _MODIFIED_FILE = "onboarding-phase2-track-setup.md"

    def test_phase2_track_setup_phase_entry_references_modified_file(self) -> None:
        """The ``phase2-track-setup`` phase entry references the modified file (Req 3.2).

        Asserts both the phase key and its ``file:`` reference to
        ``onboarding-phase2-track-setup.md`` are present in the index text.
        """
        index_text = _read_steering_index()
        assert "phase2-track-setup:" in index_text, (
            "steering-index.yaml missing the 'phase2-track-setup' phase entry"
        )
        assert f"file: {self._MODIFIED_FILE}" in index_text, (
            "phase2-track-setup phase entry must reference "
            f"'{self._MODIFIED_FILE}' via a 'file:' key"
        )

    def test_phase_entry_and_file_reference_are_adjacent(self) -> None:
        """The ``file:`` reference follows the ``phase2-track-setup`` phase key (Req 3.2).

        Anchors the ``file: onboarding-phase2-track-setup.md`` reference after
        the ``phase2-track-setup:`` phase key so the phase entry (not some other
        entry) is the one that references the modified file.
        """
        index_text = _read_steering_index()
        phase_idx = index_text.index("phase2-track-setup:")
        file_ref_idx = index_text.index(f"file: {self._MODIFIED_FILE}")
        assert phase_idx < file_ref_idx, (
            "'file: onboarding-phase2-track-setup.md' must follow the "
            "'phase2-track-setup:' phase key"
        )

    def test_file_metadata_entry_exists_for_modified_file(self) -> None:
        """A ``file_metadata`` entry exists for the modified file (Req 3.2).

        Asserts the ``file_metadata:`` section is present and contains a keyed
        entry for ``onboarding-phase2-track-setup.md``.
        """
        index_text = _read_steering_index()
        assert "file_metadata:" in index_text, (
            "steering-index.yaml missing the 'file_metadata' section"
        )
        assert f"{self._MODIFIED_FILE}:" in index_text, (
            f"file_metadata missing an entry for '{self._MODIFIED_FILE}'"
        )

    def test_file_metadata_entry_follows_file_metadata_section(self) -> None:
        """The modified file's ``file_metadata`` entry sits under ``file_metadata:`` (Req 3.2).

        Anchors the ``onboarding-phase2-track-setup.md:`` keyed entry after the
        ``file_metadata:`` section header so the entry is the file_metadata one,
        not merely the phase entry's ``file:`` reference.
        """
        index_text = _read_steering_index()
        file_metadata_idx = index_text.index("file_metadata:")
        entry_idx = index_text.index(f"  {self._MODIFIED_FILE}:")
        assert file_metadata_idx < entry_idx, (
            f"the '{self._MODIFIED_FILE}' file_metadata entry must appear "
            "under the 'file_metadata:' section"
        )
