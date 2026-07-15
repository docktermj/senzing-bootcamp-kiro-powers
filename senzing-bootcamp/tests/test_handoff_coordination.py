"""Coordination regression tests for the session-handoff context-reset hook-in.

Task 5.2 of the ``session-handoff`` spec. These example-based (pytest,
non-Hypothesis) tests lock in the invariants of the task 5.1 edit to
``steering/agent-context-management.md`` — the ``### Session Handoff Offer``
subsection appended to the "Context Reset Communication" section — and guard
against regressions in three directions:

1. **Context_Reset_Message preservation.** The hook-in must not remove or alter
   the Context_Reset_Message's four required elements or the forbidden temporal
   phrase discipline that pre-existed the edit (Req 8.4 — no regression to
   Req-owning content).
2. **Hook-in presence.** The new offer must be present: it offers a handoff
   before the reset, references the Session_Handoff steering behavior via the
   ``#[[file:...session-handoff.md]]`` reference, and reuses the
   Continuation_Phrase / current-module convention rather than defining a new
   resume mechanism (Req 1.3, 7.3, 8.4).
3. **Coordination boundary.** The offer must not claim to write persisted state
   and must not override the session-resume / module-completion-artifacts
   responsibilities — no writer of ``config/bootcamp_progress.json``,
   ``config/bootcamp_preferences.yaml``, or ``docs/bootcamp_recap.md`` is
   introduced, and the decisions it carries are explicitly the ones not written
   to any state file (Req 8.2, 10.2).

The assertions read the actual ``agent-context-management.md`` file text and are
tolerant of benign wording changes where practical, but specific enough to fail
if a whole invariant (a required element, a forbidden phrase, the steering
reference, the convention reuse, or the read-only posture) were removed.

Feature: session-handoff
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths — this file lives in senzing-bootcamp/tests/; steering lives in
# senzing-bootcamp/steering/.
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_CONTEXT_MGMT: Path = _STEERING_DIR / "agent-context-management.md"

# ---------------------------------------------------------------------------
# Constants — the invariants the hook-in must not disturb
# ---------------------------------------------------------------------------

# The Context_Reset_Message's four required elements (bold labels in the
# "### Required Message Elements" subsection).
REQUIRED_RESET_ELEMENTS: tuple[str, ...] = (
    "Technical reason",
    "Immediacy clarification",
    "Progress reassurance",
    "Continuation phrase",
)

# The eight forbidden temporal phrases the reset message must never contain.
FORBIDDEN_TEMPORAL_PHRASES: tuple[str, ...] = (
    "come back later",
    "come back tomorrow",
    "take a break",
    "try again in a while",
    "when you're ready",
    "try again later",
    "wait a moment",
    "give it some time",
)

# Persisted state files the handoff path must never write (coordination boundary).
PERSISTED_STATE_FILES: tuple[str, ...] = (
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
    "docs/bootcamp_recap.md",
)

# The literal steering-behavior reference the offer must use to delegate to the
# Session_Handoff behavior rather than restating it.
_SESSION_HANDOFF_REF: str = "#[[file:senzing-bootcamp/steering/session-handoff.md]]"

_RESET_SECTION_HEADING: str = "## Context Reset Communication"
_OFFER_SUBSECTION_HEADING: str = "### Session Handoff Offer"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return a file's UTF-8 text.

    Args:
        path: File to read.

    Returns:
        The file's contents.
    """
    return path.read_text(encoding="utf-8")


def _extract_section(text: str, heading: str) -> str:
    """Return a markdown section by its exact heading line.

    The returned slice starts at the heading line and ends just before the next
    heading of the same or a higher level (fewer or equal ``#`` characters), or
    the end of the document.

    Args:
        text: Full markdown document text.
        heading: The heading line to isolate (with its ``#`` prefix).

    Returns:
        The section text including its heading line.
    """
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    assert start is not None, f"Section heading not found: {heading!r}"

    heading_level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            if level <= heading_level:
                end = index
                break
    return "\n".join(lines[start:end])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def content() -> str:
    """The full ``agent-context-management.md`` text (raw case)."""
    return _read(_CONTEXT_MGMT)


@pytest.fixture(scope="module")
def reset_section(content: str) -> str:
    """The full "## Context Reset Communication" section (raw case)."""
    return _extract_section(content, _RESET_SECTION_HEADING)


@pytest.fixture(scope="module")
def offer_subsection(content: str) -> str:
    """The "### Session Handoff Offer" subsection added by task 5.1 (raw case)."""
    return _extract_section(content, _OFFER_SUBSECTION_HEADING)


# ---------------------------------------------------------------------------
# TestContextResetMessageRegression
# ---------------------------------------------------------------------------


class TestContextResetMessageRegression:
    """The Context_Reset_Message's required elements and phrase discipline persist.

    The 5.1 hook-in appended an offer subsection; it must not have removed or
    altered the reset message's four required elements, the "all four in a single
    response" rule, the forbidden temporal phrase list, or the format
    constraints that the reset message owns.

    **Validates: Requirements 1.3, 8.4**
    """

    def test_context_mgmt_file_present(self) -> None:
        """The steering file exists and is non-empty."""
        assert _CONTEXT_MGMT.is_file(), f"Missing steering file: {_CONTEXT_MGMT}"
        assert _read(_CONTEXT_MGMT).strip(), f"Steering file is empty: {_CONTEXT_MGMT}"

    def test_reset_section_present(self, reset_section: str) -> None:
        """The "Context Reset Communication" section is present and non-empty."""
        assert reset_section.strip(), "Context Reset Communication section is empty."
        assert reset_section.splitlines()[0].strip() == _RESET_SECTION_HEADING

    def test_required_message_elements_heading_present(self, reset_section: str) -> None:
        """The "Required Message Elements" subsection is still present."""
        assert "### Required Message Elements" in reset_section, (
            "The Required Message Elements subsection was removed."
        )

    @pytest.mark.parametrize("element", REQUIRED_RESET_ELEMENTS)
    def test_each_required_element_present(self, reset_section: str, element: str) -> None:
        """Each of the four required reset-message elements is still documented."""
        assert element in reset_section, (
            f"Required Context_Reset_Message element missing: {element!r}"
        )

    def test_requires_all_four_elements_in_single_response(self, reset_section: str) -> None:
        """The 'all four elements in a single response' rule is intact."""
        lower = reset_section.lower()
        assert "all four elements" in lower, (
            "The rule requiring all four elements in a single response was weakened."
        )

    def test_forbidden_temporal_phrases_heading_present(self, reset_section: str) -> None:
        """The "Forbidden Temporal Phrases" subsection is still present."""
        assert "### Forbidden Temporal Phrases" in reset_section, (
            "The Forbidden Temporal Phrases subsection was removed."
        )

    @pytest.mark.parametrize("phrase", FORBIDDEN_TEMPORAL_PHRASES)
    def test_each_forbidden_phrase_listed(self, reset_section: str, phrase: str) -> None:
        """Each of the eight forbidden temporal phrases is still listed."""
        assert phrase in reset_section, (
            f"Forbidden temporal phrase no longer listed: {phrase!r}"
        )

    def test_forbidden_phrase_count_intact(self, reset_section: str) -> None:
        """All eight forbidden phrases remain — no partial deletion of the list."""
        present = [p for p in FORBIDDEN_TEMPORAL_PHRASES if p in reset_section]
        assert len(present) == len(FORBIDDEN_TEMPORAL_PHRASES), (
            f"Expected all {len(FORBIDDEN_TEMPORAL_PHRASES)} forbidden phrases, "
            f"found {len(present)}: {present}"
        )

    def test_format_constraints_intact(self, reset_section: str) -> None:
        """The reset-message format constraints (4 sentences, no questions) persist."""
        lower = reset_section.lower()
        assert "maximum 4 sentences" in lower, "The 4-sentence cap was removed."
        assert "no questions" in lower, "The 'no questions' constraint was removed."

    def test_example_message_uses_quoted_continuation_phrase(self, reset_section: str) -> None:
        """The example reset message still quotes a module-numbered continuation phrase."""
        assert '"continue the bootcamp from module' in reset_section, (
            "The example message's quoted continuation phrase was removed or altered."
        )


# ---------------------------------------------------------------------------
# TestSessionHandoffOfferHookIn
# ---------------------------------------------------------------------------


class TestSessionHandoffOfferHookIn:
    """The Session Handoff Offer hook-in is present and correctly wired.

    The offer must precede the reset, delegate to the Session_Handoff steering
    behavior by reference, and reuse the existing Continuation_Phrase /
    current-module convention instead of defining a new resume mechanism.

    **Validates: Requirements 1.3, 7.3, 8.4**
    """

    def test_offer_subsection_present(self, offer_subsection: str) -> None:
        """The "### Session Handoff Offer" subsection exists and is non-empty."""
        assert offer_subsection.strip(), "Session Handoff Offer subsection is empty."
        assert offer_subsection.splitlines()[0].strip() == _OFFER_SUBSECTION_HEADING

    def test_offer_precedes_reset_message(self, offer_subsection: str) -> None:
        """The offer is made before the Context_Reset_Message is emitted (Req 1.3)."""
        lower = offer_subsection.lower()
        assert "before emitting the context_reset_message" in lower, (
            "The offer no longer explicitly precedes the Context_Reset_Message."
        )
        assert "offer to produce a session_handoff" in lower, (
            "The subsection no longer offers to produce a Session_Handoff."
        )

    def test_references_session_handoff_steering_behavior(self, offer_subsection: str) -> None:
        """The offer delegates to session-handoff.md via the file reference (Req 1.3)."""
        assert _SESSION_HANDOFF_REF in offer_subsection, (
            "The offer no longer references the Session_Handoff steering behavior "
            f"via {_SESSION_HANDOFF_REF!r}."
        )

    def test_reuses_continuation_phrase_convention(self, offer_subsection: str) -> None:
        """The offer reuses the Continuation_Phrase / current-module convention (Req 7.3)."""
        lower = offer_subsection.lower()
        assert "reuses the continuation_phrase and current-module convention" in lower, (
            "The offer no longer states that it reuses the Continuation_Phrase and "
            "current-module convention."
        )

    def test_does_not_define_new_resume_mechanism(self, offer_subsection: str) -> None:
        """The offer defers to the existing resume mechanism (Req 7.3, 8.4)."""
        lower = offer_subsection.lower()
        assert "rather than introducing a new resume mechanism" in lower, (
            "The offer no longer disclaims introducing a new resume mechanism."
        )

    def test_offer_respects_single_question_protocol(self, offer_subsection: str) -> None:
        """The offer is a single question per the one-question-per-turn rule (Req 1.3)."""
        lower = offer_subsection.lower()
        assert "one-question-per-turn" in lower, (
            "The offer no longer respects the one-question-per-turn rule."
        )
        assert "conversation-protocol.md" in offer_subsection, (
            "The offer no longer references conversation-protocol.md for the protocol."
        )

    def test_offer_does_not_alter_reset_message_requirements(self, offer_subsection: str) -> None:
        """The offer explicitly leaves the reset message's requirements unchanged."""
        lower = offer_subsection.lower()
        assert "does not alter" in lower and "four required elements" in lower, (
            "The offer no longer states it leaves the reset message's four required "
            "elements unchanged."
        )


# ---------------------------------------------------------------------------
# TestCoordinationBoundary
# ---------------------------------------------------------------------------


class TestCoordinationBoundary:
    """The offer holds the coordination boundary: it writes no persisted state.

    The handoff offer must not claim to write the persisted state files owned by
    session-resume / module-completion-artifacts, and must position the state it
    carries as the in-session decisions that are *not* written to any file.

    **Validates: Requirements 8.2, 8.4, 10.2**
    """

    def test_offer_states_decisions_not_persisted(self, offer_subsection: str) -> None:
        """The offer frames its value as decisions not written to any state file."""
        lower = offer_subsection.lower()
        assert "not written to any state file" in lower, (
            "The offer no longer clarifies that the carried decisions are the ones "
            "not written to any state file (the unique value-add over session-resume)."
        )

    @pytest.mark.parametrize("state_file", PERSISTED_STATE_FILES)
    def test_offer_adds_no_persisted_state_writer(
        self, offer_subsection: str, state_file: str
    ) -> None:
        """The offer introduces no literal writer of a persisted state file (Req 8.2, 10.2)."""
        assert state_file not in offer_subsection, (
            f"The handoff offer must not reference the persisted state file "
            f"{state_file!r}; the offer path performs no writes to it. A literal "
            f"reference here signals a coordination-boundary regression."
        )

    def test_offer_reads_current_module_by_glossary_term(self, offer_subsection: str) -> None:
        """The offer reads current-module from the Progress_File by name, not by writing it."""
        # It refers to the Progress_File / current_module field for a read, and must
        # not pair that with a write instruction.
        lower = offer_subsection.lower()
        assert "current_module" in lower and "progress_file" in lower, (
            "The offer no longer sources the module number from the Progress_File's "
            "current_module field."
        )
        for verb in ("write to the progress_file", "update the progress_file",
                     "modify the progress_file", "rewrite the progress_file"):
            assert verb not in lower, (
                f"The offer must not instruct a write to persisted state: found {verb!r}."
            )

    def test_reset_section_adds_no_persisted_state_writer(self, reset_section: str) -> None:
        """The whole reset section names no persisted state file as a write target.

        The reset section reads the Progress_File for the module number (a read),
        so the literal ``config/bootcamp_progress.json`` path may appear there; a
        write of preferences or recap, however, would be out of scope for this
        section and signal a regression.
        """
        lower = reset_section.lower()
        for state_file in ("config/bootcamp_preferences.yaml", "docs/bootcamp_recap.md"):
            assert state_file not in reset_section, (
                f"The Context Reset Communication section must not reference "
                f"{state_file!r} as a write target."
            )
        # Guard against write verbs targeting the recap/preferences state.
        for verb in ("write to docs/bootcamp_recap.md", "modify docs/bootcamp_recap.md",
                     "rewrite docs/bootcamp_recap.md"):
            assert verb not in lower, (
                f"The reset section must not instruct rewriting persisted artifacts: "
                f"found {verb!r}."
            )
