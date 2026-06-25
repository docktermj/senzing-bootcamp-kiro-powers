"""Property and example tests for the leading-question-continuity turn model.

This module covers Outcome A (leading-question continuity) of the
``leading-question-continuity`` feature. It exercises a small model of an
agent *turn* — characterized by ``(primary_action, yields, leading_question_count)``
— against the continuity invariant defined in the design, and asserts that the
live steering file ``senzing-bootcamp/steering/conversation-protocol.md`` states
the Intercept-Recovery Continuity rule (including the ``config/.question_pending``
write).

Test classes are intentionally kept independent so later tasks can append
additional property/example classes (Property 2, the closing-question-ownership
example) to this same file without restructuring the shared model below.

Conventions: Python 3.11+, stdlib-only helpers, type hints, Google-style
docstrings, pytest + Hypothesis, class-based, ``st_``-prefixed strategies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_CONVERSATION_PROTOCOL = _BOOTCAMP_DIR / "steering" / "conversation-protocol.md"


# ---------------------------------------------------------------------------
# Turn model (shared across property/example classes in this file)
# ---------------------------------------------------------------------------

# The primary action a turn can perform. ``reissued_write_after_intercept`` is
# the regression-prone case: a write re-issued after a ``write-policy-gate``
# intercept. The continuity invariant must hold for it exactly as for any other
# primary action.
PRIMARY_ACTIONS: tuple[str, ...] = (
    "content",
    "write",
    "reissued_write_after_intercept",
    "module_transition",
    "hook_intercept_handling",
)


@dataclass
class Turn:
    """A single unit of agent activity that may yield control to the bootcamper.

    Attributes:
        primary_action: The dominant action performed during the turn (one of
            ``PRIMARY_ACTIONS``).
        yields: Whether the turn returns control to the bootcamper. A turn that
            does not yield is an internal step that immediately continues work.
        leading_question_count: The number of visible-text 👉 leading questions
            presented at the end of the turn.
    """

    primary_action: str
    yields: bool
    leading_question_count: int


def turn_yields(leading_question_count: int) -> bool:
    """Classify whether a turn yields control under the End-of-Turn Protocol.

    A turn yields control to the bootcamper if and only if it ends with exactly
    one leading question. A turn with zero visible leading questions is not yet
    yielding (the agent must continue until a question is presented); a turn with
    more than one question violates the One Question Rule and is likewise not a
    valid yielding turn.

    Args:
        leading_question_count: The number of 👉 leading questions ending the turn.

    Returns:
        True if the turn yields control, False otherwise.
    """
    return leading_question_count == 1


def complete_yielding_turn(primary_action: str) -> Turn:
    """Model a protocol-compliant turn that yields control.

    Regardless of ``primary_action`` — including ``reissued_write_after_intercept``
    — a protocol-compliant agent appends exactly one 👉 leading question before
    yielding control, per the End-of-Turn Protocol and Intercept-Recovery
    Continuity rule.

    Args:
        primary_action: The dominant action performed during the turn.

    Returns:
        A :class:`Turn` that yields control with exactly one leading question.
    """
    count = 1
    return Turn(
        primary_action=primary_action,
        yields=turn_yields(count),
        leading_question_count=count,
    )


# ---------------------------------------------------------------------------
# Steering-content helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Return the full UTF-8 text of a steering file."""
    return path.read_text(encoding="utf-8")


def _extract_section(markdown: str, heading: str) -> str:
    """Extract a markdown section by its exact heading text.

    The section spans from the matched heading up to the next heading of the
    same or higher level, or the end of the document.

    Args:
        markdown: The full markdown document.
        heading: The heading text to locate (without leading ``#`` markers).

    Returns:
        The section text including its heading, or an empty string if not found.
    """
    pattern = re.compile(
        rf"^(#{{2,4}})\s+{re.escape(heading)}\s*$",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    level = len(match.group(1))
    start = match.start()
    # Find the next heading at the same or higher level.
    next_heading = re.compile(rf"^#{{1,{level}}}\s+\S", re.MULTILINE)
    next_match = next_heading.search(markdown, match.end())
    if next_match:
        return markdown[start:next_match.start()]
    return markdown[start:]


def _states_intercept_recovery_continuity(content: str) -> bool:
    """Check that the protocol states the intercept-recovery continuity rule.

    The rule must: (a) exist as an Intercept-Recovery Continuity section,
    (b) tie the continuity obligation to a write re-issued after a
    ``write-policy-gate`` intercept, and (c) require exactly one 👉 leading
    question before the turn completes.

    Args:
        content: The full ``conversation-protocol.md`` text.

    Returns:
        True if all three conditions hold within the section, False otherwise.
    """
    section = _extract_section(content, "Intercept-Recovery Continuity")
    if not section:
        return False
    mentions_intercept = bool(
        re.search(r"re-?issued", section, re.IGNORECASE)
        and re.search(r"write-policy-gate", section, re.IGNORECASE)
        and re.search(r"intercept", section, re.IGNORECASE)
    )
    requires_one_question = bool(
        re.search(r"\bone\b", section, re.IGNORECASE) and "👉" in section
    )
    return mentions_intercept and requires_one_question


def _states_question_pending_write(content: str) -> bool:
    """Check that the intercept-recovery rule requires the question_pending write.

    Args:
        content: The full ``conversation-protocol.md`` text.

    Returns:
        True if the section references writing ``config/.question_pending``.
    """
    section = _extract_section(content, "Intercept-Recovery Continuity")
    if not section:
        return False
    return "config/.question_pending" in section


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_turn(draw: st.DrawFn) -> Turn:
    """Generate an arbitrary turn with a protocol-classified ``yields`` flag.

    ``primary_action`` is drawn across all actions (including
    ``reissued_write_after_intercept``); ``leading_question_count`` is drawn
    from a small range covering zero, exactly one, and multiple questions. The
    ``yields`` flag is derived from the End-of-Turn Protocol classifier.
    """
    primary_action = draw(st.sampled_from(PRIMARY_ACTIONS))
    leading_question_count = draw(st.integers(min_value=0, max_value=3))
    return Turn(
        primary_action=primary_action,
        yields=turn_yields(leading_question_count),
        leading_question_count=leading_question_count,
    )


@st.composite
def st_yielding_turn(draw: st.DrawFn) -> Turn:
    """Generate a protocol-compliant yielding turn with a varied primary action.

    Emphasizes ``reissued_write_after_intercept`` to exercise the
    intercept-recovery continuity case, while still covering every other primary
    action. Every generated turn yields control.
    """
    primary_action = draw(
        st.sampled_from(PRIMARY_ACTIONS)
        | st.just("reissued_write_after_intercept")
    )
    return complete_yielding_turn(primary_action)


# ---------------------------------------------------------------------------
# Property 1 — Every yielding turn ends with exactly one leading question
# ---------------------------------------------------------------------------
# Feature: leading-question-continuity, Property 1


class TestEveryYieldingTurnEndsWithOneLeadingQuestion:
    """Property 1 — every yielding turn ends with exactly one leading question.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**

    For any turn that yields control to the bootcamper — regardless of its
    primary action, including a write re-issued after a ``write-policy-gate``
    intercept — the turn ends with exactly one visible-text leading question,
    and any turn with zero leading questions is not classified as yielding. The
    continuity rule (and the ``config/.question_pending`` write) is also stated
    in the live ``conversation-protocol.md`` steering file.
    """

    @given(turn=st_turn())
    @settings(max_examples=200)
    def test_yields_implies_exactly_one_leading_question(self, turn: Turn) -> None:
        """``yields`` implies ``leading_question_count == 1`` for all turns."""
        if turn.yields:
            assert turn.leading_question_count == 1, (
                "A yielding turn must end with exactly one leading question, but "
                f"primary_action={turn.primary_action!r} yielded with "
                f"leading_question_count={turn.leading_question_count}."
            )

    @given(turn=st_turn())
    @settings(max_examples=200)
    def test_zero_questions_is_not_yielding(self, turn: Turn) -> None:
        """A turn with zero leading questions is never classified as yielding."""
        if turn.leading_question_count == 0:
            assert not turn.yields, (
                "A turn with zero leading questions must not be classified as "
                f"yielding, but primary_action={turn.primary_action!r} did."
            )

    @given(turn=st_yielding_turn())
    @settings(max_examples=200)
    def test_protocol_compliant_yielding_turn_has_one_question(
        self, turn: Turn
    ) -> None:
        """A protocol-compliant yielding turn always carries exactly one question.

        Includes the intercept-recovery case: a write re-issued after a
        ``write-policy-gate`` intercept still ends with exactly one 👉 question.
        """
        assert turn.yields, "Generated turn must yield control"
        assert turn.leading_question_count == 1, (
            "Every yielding turn — including a re-issued write after an "
            "intercept — must end with exactly one leading question, but "
            f"primary_action={turn.primary_action!r} had "
            f"leading_question_count={turn.leading_question_count}."
        )

    @given(turn=st_yielding_turn())
    @settings(max_examples=200)
    def test_steering_states_intercept_recovery_continuity(
        self, turn: Turn
    ) -> None:
        """``conversation-protocol.md`` states the intercept-recovery rule."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _states_intercept_recovery_continuity(content), (
            "conversation-protocol.md must state the Intercept-Recovery "
            "Continuity rule: a write re-issued after a write-policy-gate "
            "intercept still requires exactly one 👉 leading question before "
            "the turn completes."
        )

    @given(turn=st_yielding_turn())
    @settings(max_examples=200)
    def test_steering_requires_question_pending_write(self, turn: Turn) -> None:
        """The intercept-recovery rule requires writing ``config/.question_pending``."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _states_question_pending_write(content), (
            "conversation-protocol.md Intercept-Recovery Continuity section must "
            "require writing config/.question_pending alongside the leading "
            "question."
        )


# ---------------------------------------------------------------------------
# Single-question detector (Property 2 helper)
# ---------------------------------------------------------------------------
#
# This helper encodes the CHECK 2 "SINGLE-QUESTION ENFORCEMENT" rules from the
# write-policy-gate hook prompt and the One Question Rule referenced by
# Requirement 1.4. A leading question is single and unambiguous when:
#   1. It contains exactly one question mark.
#   2. It uses no conjunction phrase that joins separate choices in prose
#      ('also', 'but first', 'alternatively', 'or if you prefer',
#      'or would you rather').
#   3. It appends no alternative action after the main question (a ', or ...'
#      or ', alternatively ...' tail before the question mark).
# A compound or ambiguous question violates at least one rule.

# Conjunction phrases that join separate choices in prose (CHECK 2, rule 2).
_CONJUNCTION_PHRASES: tuple[str, ...] = (
    " also ",
    "but first",
    "alternatively",
    "or if you prefer",
    "or would you rather",
)

# An appended alternative is a comma followed by 'or'/'alternatively' that tacks
# a second choice onto the main question (CHECK 2, rule 3).
_APPENDED_ALTERNATIVE = re.compile(r",\s*(?:or|alternatively)\b", re.IGNORECASE)


def is_single_unambiguous_question(text: str) -> bool:
    """Return whether ``text`` is a single, unambiguous leading question.

    Encodes the CHECK 2 single-question rules from the ``write-policy-gate``
    hook prompt (consistent with the One Question Rule): exactly one question
    mark, no conjunction joining separate choices, and no appended alternative.

    Args:
        text: The candidate leading-question text.

    Returns:
        True if the text satisfies every single-question rule, False if it is
        compound or ambiguous.
    """
    # Rule 1: exactly one question mark.
    if text.count("?") != 1:
        return False
    # Rule 3: no appended alternative tacked on with a comma.
    if _APPENDED_ALTERNATIVE.search(text):
        return False
    # Rule 2: no conjunction phrase joining separate choices.
    lowered = text.lower()
    for phrase in _CONJUNCTION_PHRASES:
        if phrase in lowered:
            return False
    return True


# Question bodies (no trailing punctuation) reused to compose both clean and
# compound questions so the two strategies share a vocabulary.
_QUESTION_BODIES: tuple[str, ...] = (
    "Want to load the truth set now",
    "Should I generate the data sources file",
    "Ready to move on to the next module",
    "Which data source should we map first",
    "Do you want to run the entity resolution step",
    "Shall I create config/data_sources.yaml",
)

# Trailing alternatives used to build appended-alternative violations.
_APPENDED_TAILS: tuple[str, ...] = (
    "or should we skip ahead",
    "or we could move on",
    "alternatively regenerate it",
)


@st.composite
def st_single_question(draw: st.DrawFn) -> str:
    """Generate a single, unambiguous leading question string.

    Each generated string has exactly one question mark, no conjunction joining
    separate choices, and no appended alternative. A pointing-hand prefix is
    optionally added to mirror the agent's visible-text format.
    """
    body = draw(st.sampled_from(_QUESTION_BODIES))
    prefix = draw(st.sampled_from(("", "👉 ")))
    return f"{prefix}{body}?"


@st.composite
def st_compound_question(draw: st.DrawFn) -> str:
    """Generate a compound or ambiguous leading-question string.

    Produces one of three violation kinds, each of which the single-question
    detector must reject: two question marks, an appended alternative, or a
    conjunction phrase joining separate choices.
    """
    body = draw(st.sampled_from(_QUESTION_BODIES))
    kind = draw(st.sampled_from(("two_marks", "appended_alternative", "conjunction")))
    if kind == "two_marks":
        other = draw(st.sampled_from(_QUESTION_BODIES))
        return f"{body}? {other}?"
    if kind == "appended_alternative":
        tail = draw(st.sampled_from(_APPENDED_TAILS))
        return f"{body}, {tail}?"
    phrase = draw(st.sampled_from(_CONJUNCTION_PHRASES))
    return f"{body}{phrase}confirm the mapping?"


# ---------------------------------------------------------------------------
# Property 2 — Leading questions are single and unambiguous
# ---------------------------------------------------------------------------
# Feature: leading-question-continuity, Property 2


class TestLeadingQuestionsAreSingleAndUnambiguous:
    """Property 2 — leading questions are single and unambiguous.

    **Validates: Requirements 1.4**

    For any leading-question text the agent emits, it satisfies the single-question
    rule: exactly one question mark, no conjunction joining separate choices, and
    no appended alternative. A compound or ambiguous question is rejected. The
    detector encodes the CHECK 2 rules from the ``write-policy-gate`` hook prompt,
    consistent with the One Question Rule.
    """

    @given(question=st_single_question())
    @settings(max_examples=200)
    def test_single_question_is_accepted(self, question: str) -> None:
        """A single, unambiguous question passes the single-question detector."""
        assert is_single_unambiguous_question(question), (
            "A single, unambiguous question must be accepted, but the detector "
            f"rejected {question!r}."
        )

    @given(question=st_compound_question())
    @settings(max_examples=200)
    def test_compound_question_is_rejected(self, question: str) -> None:
        """A compound or ambiguous question is rejected by the detector."""
        assert not is_single_unambiguous_question(question), (
            "A compound or ambiguous question must be rejected, but the detector "
            f"accepted {question!r}."
        )

    @given(question=st_single_question())
    @settings(max_examples=200)
    def test_single_question_has_exactly_one_question_mark(
        self, question: str
    ) -> None:
        """Every accepted single question carries exactly one question mark."""
        assert question.count("?") == 1, (
            "A single leading question must contain exactly one question mark, "
            f"but {question!r} did not."
        )


# ---------------------------------------------------------------------------
# Closing-question-ownership helpers (example-based)
# ---------------------------------------------------------------------------


def _states_closing_question_is_agent_owned(content: str) -> bool:
    """Check that the Intercept-Recovery Continuity rule owns the closing question.

    The Intercept-Recovery Continuity section must state that the closing
    question is the agent's own responsibility and is *not* deferred to a hook
    (i.e. the obligation is not handed off to the ``ask-bootcamper`` hook).

    Args:
        content: The full ``conversation-protocol.md`` text.

    Returns:
        True if the section states the closing question is agent-owned and not
        deferred to a hook, False otherwise.
    """
    section = _extract_section(content, "Intercept-Recovery Continuity")
    if not section:
        return False
    lowered = section.lower()
    claims_ownership = "your responsibility" in lowered
    not_deferred = bool(re.search(r"not\s+deferred\s+to\s+a\s+hook", lowered))
    return claims_ownership and not_deferred


def _states_hook_is_safety_net_only(content: str) -> bool:
    """Check the protocol frames the ``ask-bootcamper`` hook as a safety net only.

    The agent must not rely on the ``ask-bootcamper`` hook to supply the closing
    question; the protocol states the hook is a safety net only.

    Args:
        content: The full ``conversation-protocol.md`` text.

    Returns:
        True if the protocol states the ask-bootcamper hook is a safety net only
        and must not be relied on for closing questions, False otherwise.
    """
    lowered = content.lower()
    mentions_hook = "ask-bootcamper" in lowered
    safety_net_only = "safety net only" in lowered
    do_not_rely = bool(re.search(r"do not rely on it for closing questions", lowered))
    return mentions_hook and safety_net_only and do_not_rely


# ---------------------------------------------------------------------------
# Example — Closing question is the agent's responsibility, not a hook's
# ---------------------------------------------------------------------------
# Feature: leading-question-continuity, closing-question ownership example


class TestClosingQuestionIsAgentResponsibility:
    """Example — the closing question is owned by the agent, not deferred to a hook.

    **Validates: Requirements 2.4**

    The live ``conversation-protocol.md`` steering file must state that the
    closing 👉 leading question is the agent's own responsibility and is not
    deferred to the ``ask-bootcamper`` hook (the hook is a safety net only).
    These are concrete example-based assertions against the actual steering
    content rather than property checks over generated inputs.
    """

    def test_intercept_recovery_section_owns_the_closing_question(self) -> None:
        """The Intercept-Recovery Continuity rule claims agent ownership."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _states_closing_question_is_agent_owned(content), (
            "conversation-protocol.md Intercept-Recovery Continuity section must "
            "state the closing question is the agent's responsibility and is not "
            "deferred to a hook."
        )

    def test_ask_bootcamper_hook_is_safety_net_only(self) -> None:
        """The protocol frames the ask-bootcamper hook as a safety net only."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _states_hook_is_safety_net_only(content), (
            "conversation-protocol.md must state the ask-bootcamper hook is a "
            "safety net only and must not be relied on for closing questions."
        )
