"""Bug condition exploration tests for the turn-answer-handling bugfix.

Property 1 (Bug Condition): One Live Pending Question, Answers Bound.

These tests encode the EXPECTED post-fix behavior. They are EXPECTED TO FAIL
on the unfixed code because:

- Item 2: the answer-binding helper (`scripts/answer_binding.py`) does not yet
  exist, so a bare option token (e.g. "3") cannot be bound to a presented
  numbered/lettered option list. `volume_utils.parse_volume_input("3")`
  instead returns the literal integer 3 (classified as the demo tier),
  documenting the wrong literal interpretation the binding step must override.
- Item 1: the steering invariants are absent — `conversation-protocol.md` has
  no explicit "live 👉 pending question must be the final message of an
  input-expecting turn" rule, and the module-completion steering has no
  recap-before-transition (or re-surface-forward-question) ordering rule.

Failure of these tests confirms the bug exists. They will validate the fix
when they pass after implementation.

Feature: turn-answer-handling
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Scripts import via sys.path (scripts aren't packages)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_BOOTCAMP_DIR / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import volume_utils  # noqa: E402  (path manipulated above)

# ---------------------------------------------------------------------------
# Steering paths
# ---------------------------------------------------------------------------

_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_CONVERSATION_PROTOCOL = _STEERING_DIR / "conversation-protocol.md"
_MODULE_COMPLETION = _STEERING_DIR / "module-completion.md"
_MODULE_COMPLETION_NEXT_STEPS = _STEERING_DIR / "module-completion-next-steps.md"

# ---------------------------------------------------------------------------
# Fixtures / option lists presented to the bootcamper
# ---------------------------------------------------------------------------

# Module 6 Step 1 production-volume question presents a four-tier numbered list.
# The 1-based index maps to a tier: 1->demo, 2->small, 3->medium, 4->large.
FOUR_VOLUME_OPTIONS = [
    "Demo / proof-of-concept (under 500 records)",
    "Small production (500 - 500K records)",
    "Medium production (500K - 10M records)",
    "Large production (over 10M records)",
]

OPTION_INDEX_TO_TIER = {
    1: volume_utils.TIER_DEMO,
    2: volume_utils.TIER_SMALL,
    3: volume_utils.TIER_MEDIUM,
    4: volume_utils.TIER_LARGE,
}


def _import_answer_binding():
    """Import the (post-fix) answer_binding helper module.

    On unfixed code this raises ModuleNotFoundError because
    ``scripts/answer_binding.py`` does not exist yet — that failure is the
    expected counterexample for the binding half of the bug condition.
    """
    return importlib.import_module("answer_binding")


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_numeric_token_in_range(draw: st.DrawFn) -> tuple[list[str], int]:
    """Generate (options, n) where n is a 1-based index within the list."""
    length = draw(st.integers(min_value=1, max_value=12))
    options = [f"option-{i}" for i in range(1, length + 1)]
    n = draw(st.integers(min_value=1, max_value=length))
    return options, n


@st.composite
def st_letter_token_in_range(draw: st.DrawFn) -> tuple[list[str], int, str]:
    """Generate (options, position, letter) for a bare lettered token.

    ``letter`` may be upper- or lower-case; ``position`` is its 1-based index.
    """
    length = draw(st.integers(min_value=1, max_value=26))
    options = [f"{chr(ord('a') + i)}-opt" for i in range(length)]
    position = draw(st.integers(min_value=1, max_value=length))
    base_letter = chr(ord("a") + position - 1)
    letter = draw(st.sampled_from([base_letter, base_letter.upper()]))
    return options, position, letter


# ---------------------------------------------------------------------------
# Item 2 — Bare option-token binding (Property 1, binding half)
# ---------------------------------------------------------------------------


class TestBareOptionTokenBinding:
    """Item 2 — a bare matching option token binds to the presented option.

    **Validates: Requirements 2.3, 2.4**

    From the Bug Condition:
    ``unboundMatchingTokenAnswer ← priorQuestionHasOptionList
    AND isBareMatchingToken(reply, options) AND NOT replyBoundToPendingQuestion``.

    EXPECTED TO FAIL on unfixed code: the `answer_binding` helper does not exist.
    """

    def test_bare_numeric_token_binds_to_option(self) -> None:
        """`bind_option("3", four_volume_options)` returns 3 (-> medium tier)."""
        answer_binding = _import_answer_binding()
        result = answer_binding.bind_option("3", FOUR_VOLUME_OPTIONS)
        assert result == 3, (
            f"Expected bare token '3' to bind to option 3, got {result!r}. "
            "A bare numeric token matching a presented option must bind to that "
            "option (option 3 -> medium tier), not be reinterpreted as a literal "
            "record count."
        )
        assert OPTION_INDEX_TO_TIER[result] == volume_utils.TIER_MEDIUM

    @given(payload=st_numeric_token_in_range())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_any_bare_numeric_token_binds_to_its_index(
        self, payload: tuple[list[str], int]
    ) -> None:
        """For any bare numeric token n within range, bind_option == n."""
        options, n = payload
        answer_binding = _import_answer_binding()
        assert answer_binding.bind_option(str(n), options) == n, (
            f"Bare numeric token {n!r} must bind to its 1-based option index "
            f"within a {len(options)}-option list."
        )

    def test_bare_lettered_token_binds_to_option(self) -> None:
        """`bind_option("b", ["a-opt","b-opt","c-opt"])` returns 2."""
        answer_binding = _import_answer_binding()
        result = answer_binding.bind_option("b", ["a-opt", "b-opt", "c-opt"])
        assert result == 2, (
            f"Expected bare letter 'b' to bind to option 2, got {result!r}."
        )

    @given(payload=st_letter_token_in_range())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_any_bare_letter_binds_case_insensitively(
        self, payload: tuple[list[str], int, str]
    ) -> None:
        """Any bare letter within range maps case-insensitively to its position."""
        options, position, letter = payload
        answer_binding = _import_answer_binding()
        assert answer_binding.bind_option(letter, options) == position, (
            f"Bare letter {letter!r} must bind case-insensitively to 1-based "
            f"position {position} within a {len(options)}-option list."
        )


# ---------------------------------------------------------------------------
# Item 2 — Mis-parse documentation (current wrong literal interpretation)
# ---------------------------------------------------------------------------


class TestVolumeMisParseDocumentation:
    """Item 2 — document the wrong literal interpretation of a bare "3".

    **Validates: Requirements 2.3, 2.4**

    `parse_volume_input("3")` returns the literal integer 3, classified as the
    demo tier. This is the wrong interpretation the binding step must override
    for an Option_List question (where "3" means option 3 -> medium tier).
    """

    def test_parse_volume_input_treats_bare_3_as_literal_demo(self) -> None:
        parsed = volume_utils.parse_volume_input("3")
        assert parsed == 3, (
            f"Expected parse_volume_input('3') == 3 (literal), got {parsed!r}."
        )
        assert volume_utils.classify_tier(parsed) == volume_utils.TIER_DEMO, (
            "A literal 3 records classifies as the demo tier — the wrong tier "
            "for option 3 (medium), which is exactly why binding must run first."
        )


# ---------------------------------------------------------------------------
# Item 1 — Final-message invariant in conversation-protocol.md
# ---------------------------------------------------------------------------


class TestFinalMessageInvariantPresent:
    """Item 1 — conversation-protocol.md states the final-message invariant.

    **Validates: Requirements 2.1, 2.2**

    EXPECTED TO FAIL on unfixed code: the explicit "live 👉 pending question
    must be the final message of an input-expecting turn" rule is absent.
    """

    def test_protocol_requires_pending_question_as_final_message(self) -> None:
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        lowered = content.lower()

        assert "final message" in lowered, (
            "conversation-protocol.md does not mention a 'final message' "
            "requirement. The invariant that a live 👉 pending question must be "
            "the final message of an input-expecting turn is absent."
        )
        assert "input-expecting" in lowered, (
            "conversation-protocol.md does not reference an 'input-expecting' "
            "turn in the context of the final-message invariant."
        )
        # The live pending question must be tied to the final-message rule.
        final_message_invariant = re.search(
            r"live[^\n]{0,80}pending question[^\n]{0,80}final message"
            r"|final message[^\n]{0,80}live[^\n]{0,80}pending question",
            lowered,
        )
        assert final_message_invariant, (
            "conversation-protocol.md lacks an explicit rule that the live 👉 "
            "pending question must be the final message of an input-expecting "
            "turn. Without it, a recap/confirmation can displace the forward "
            "question and leave the turn with zero live pending questions."
        )
        # A recap/confirmation must never be the final message of such a turn.
        recap_never_final = re.search(
            r"(recap|confirmation)[^\n]{0,80}never[^\n]{0,80}final message",
            lowered,
        )
        assert recap_never_final, (
            "conversation-protocol.md does not state that a recap/confirmation "
            "emission must never be the final message of an input-expecting turn."
        )


# ---------------------------------------------------------------------------
# Item 1 — Completion ordering rule in module-completion steering
# ---------------------------------------------------------------------------


class TestCompletionOrderingRulePresent:
    """Item 1 — completion steering carries the recap/transition ordering rule.

    **Validates: Requirements 2.1, 2.2**

    EXPECTED TO FAIL on unfixed code: neither `module-completion.md` nor
    `module-completion-next-steps.md` requires the recap/confirmation to run
    BEFORE the forward transition question, nor that the forward 👉 question be
    re-surfaced as the final message after any recap/confirmation.
    """

    def test_completion_steering_requires_recap_before_transition(self) -> None:
        completion = _MODULE_COMPLETION.read_text(encoding="utf-8").lower()
        next_steps = _MODULE_COMPLETION_NEXT_STEPS.read_text(encoding="utf-8").lower()
        combined = completion + "\n" + next_steps

        recap_before_transition = re.search(
            r"recap[^\n]{0,120}before[^\n]{0,120}(transition|forward|ready for)",
            combined,
        )
        re_surface_forward = re.search(
            r"re-?surface[^\n]{0,120}(transition|forward|ready for)"
            r"|(transition|forward|ready for)[^\n]{0,120}re-?surface[^\n]{0,120}"
            r"final message",
            combined,
        )
        assert recap_before_transition or re_surface_forward, (
            "Neither module-completion.md nor module-completion-next-steps.md "
            "contains the recap-before-transition rule (run recap/confirmation "
            "BEFORE the forward transition question) or the re-surface rule "
            "(re-surface the forward 👉 'Ready for Module X?' question as the "
            "final message after any recap/confirmation). A completion turn can "
            "therefore end on a confirmation line with zero live pending "
            "questions."
        )
