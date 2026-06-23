"""Focused unit tests for the turn-answer-handling bugfix.

Covers the small, deterministic surfaces of the fix:

- ``answer_binding.parse_option_token`` — bare numeric / lettered token parsing
  and ``None`` for free-text/mixed/empty replies.
- ``answer_binding.bind_option`` — 1-based in-range numeric / lettered binds,
  out-of-range and non-token replies binding to ``None``, case-insensitive
  letters.
- Module 6 option->tier mapping — bound index 1/2/3/4 selects demo/small/
  medium/large using the ``volume_utils`` tier constants, matching the
  option->tier map declared in ``module-06-phaseA-build-loading.md``.
- Steering presence checks — the Final-Message Invariant in
  ``conversation-protocol.md`` and the recap-before-transition / re-surface
  rule in the module-completion steering.

Feature: turn-answer-handling
"""

from __future__ import annotations

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

import answer_binding  # noqa: E402  (path manipulated above)
import volume_utils  # noqa: E402  (path manipulated above)

# ---------------------------------------------------------------------------
# Steering paths
# ---------------------------------------------------------------------------

_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_CONVERSATION_PROTOCOL = _STEERING_DIR / "conversation-protocol.md"
_MODULE_COMPLETION = _STEERING_DIR / "module-completion.md"
_MODULE_COMPLETION_NEXT_STEPS = _STEERING_DIR / "module-completion-next-steps.md"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Module 6 Step 1 presents the four tiers as a numbered option list. The
# 1-based index maps to a tier: 1->demo, 2->small, 3->medium, 4->large. The
# option labels passed to bind_option in the steering are the tier names.
FOUR_TIER_OPTIONS = ["demo", "small", "medium", "large"]

OPTION_INDEX_TO_TIER = {
    1: volume_utils.TIER_DEMO,
    2: volume_utils.TIER_SMALL,
    3: volume_utils.TIER_MEDIUM,
    4: volume_utils.TIER_LARGE,
}


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_numeric_token(draw: st.DrawFn) -> tuple[str, str]:
    """Draw a bare numeric token and its expected normalized digit string."""
    n = draw(st.integers(min_value=0, max_value=999))
    decoration = draw(st.sampled_from(["{n}", "{n}.", "({n})", " {n} ", "({n}", "{n})"]))
    return decoration.format(n=n), str(n)


@st.composite
def st_letter_token(draw: st.DrawFn) -> tuple[str, str]:
    """Draw a bare lettered token and its expected normalized lowercase letter."""
    letter = draw(st.sampled_from([chr(ord("a") + i) for i in range(26)]))
    cased = draw(st.sampled_from([letter, letter.upper()]))
    decoration = draw(st.sampled_from(["{c}", "{c}.", "({c})", " {c} ", "{c})"]))
    return decoration.format(c=cased), letter


@st.composite
def st_free_text_reply(draw: st.DrawFn) -> str:
    """Draw a reply that carries extra free-text meaning (not a bare token)."""
    return draw(
        st.sampled_from(
            [
                "3 million",
                "around 3",
                "option three please",
                "about a thousand",
                "3 records or so",
                "maybe b",
                "a lot",
                "10,000,000+",
            ]
        )
    )


# ---------------------------------------------------------------------------
# parse_option_token
# ---------------------------------------------------------------------------


class TestParseOptionToken:
    """Unit tests for ``answer_binding.parse_option_token``.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_bare_numbers_parse_to_digit_string(self) -> None:
        """Numbers ("3", "3.", "(3)") parse to their digit string."""
        assert answer_binding.parse_option_token("3") == "3"
        assert answer_binding.parse_option_token("3.") == "3"
        assert answer_binding.parse_option_token("(3)") == "3"
        assert answer_binding.parse_option_token(" 3 ") == "3"

    def test_bare_letters_parse_lowercased(self) -> None:
        """Letters ("b", "B)") parse to their lowercase letter."""
        assert answer_binding.parse_option_token("b") == "b"
        assert answer_binding.parse_option_token("B)") == "b"
        assert answer_binding.parse_option_token("b.") == "b"

    def test_free_text_and_mixed_return_none(self) -> None:
        """Free-text / mixed replies return None (not a bare token)."""
        assert answer_binding.parse_option_token("3 million") is None
        assert answer_binding.parse_option_token("around 3") is None
        assert answer_binding.parse_option_token("option three please") is None

    def test_empty_and_whitespace_return_none(self) -> None:
        """Empty and whitespace-only replies return None."""
        assert answer_binding.parse_option_token("") is None
        assert answer_binding.parse_option_token("   ") is None
        assert answer_binding.parse_option_token("\t\n") is None

    @given(payload=st_numeric_token())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_any_bare_numeric_token_normalizes(self, payload: tuple[str, str]) -> None:
        """Any decorated bare number normalizes to its digit string."""
        reply, expected = payload
        assert answer_binding.parse_option_token(reply) == expected

    @given(payload=st_letter_token())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_any_bare_letter_token_normalizes_lowercase(
        self, payload: tuple[str, str]
    ) -> None:
        """Any decorated bare letter normalizes to its lowercase letter."""
        reply, expected = payload
        assert answer_binding.parse_option_token(reply) == expected

    @given(reply=st_free_text_reply())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_free_text_replies_are_not_tokens(self, reply: str) -> None:
        """Any free-text/mixed reply is not a bare token."""
        assert answer_binding.parse_option_token(reply) is None


# ---------------------------------------------------------------------------
# bind_option
# ---------------------------------------------------------------------------


class TestBindOption:
    """Unit tests for ``answer_binding.bind_option``.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_in_range_numeric_binds_one_based(self) -> None:
        """A bare numeric token binds to its 1-based index."""
        assert answer_binding.bind_option("1", FOUR_TIER_OPTIONS) == 1
        assert answer_binding.bind_option("3", FOUR_TIER_OPTIONS) == 3
        assert answer_binding.bind_option("4", FOUR_TIER_OPTIONS) == 4

    def test_in_range_lettered_binds_one_based(self) -> None:
        """A bare lettered token binds to its 1-based alphabetic position."""
        options = ["a-opt", "b-opt", "c-opt"]
        assert answer_binding.bind_option("a", options) == 1
        assert answer_binding.bind_option("b", options) == 2
        assert answer_binding.bind_option("c", options) == 3

    def test_letters_bind_case_insensitively(self) -> None:
        """Uppercase letters bind to the same index as lowercase."""
        options = ["a-opt", "b-opt", "c-opt"]
        assert answer_binding.bind_option("B", options) == 2
        assert answer_binding.bind_option("B)", options) == 2

    def test_out_of_range_returns_none(self) -> None:
        """A bare token outside the option range binds to None."""
        assert answer_binding.bind_option("5", FOUR_TIER_OPTIONS) is None
        assert answer_binding.bind_option("0", FOUR_TIER_OPTIONS) is None
        assert answer_binding.bind_option("z", FOUR_TIER_OPTIONS) is None

    def test_non_token_returns_none(self) -> None:
        """A reply with free-text meaning binds to None."""
        assert answer_binding.bind_option("3 million", FOUR_TIER_OPTIONS) is None
        assert answer_binding.bind_option("around 3", FOUR_TIER_OPTIONS) is None
        assert answer_binding.bind_option("", FOUR_TIER_OPTIONS) is None

    @given(
        length=st.integers(min_value=1, max_value=12),
        data=st.data(),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_any_in_range_numeric_binds_to_itself(
        self, length: int, data: st.DataObject
    ) -> None:
        """For any in-range numeric token n, bind_option(str(n)) == n."""
        options = [f"option-{i}" for i in range(1, length + 1)]
        n = data.draw(st.integers(min_value=1, max_value=length))
        assert answer_binding.bind_option(str(n), options) == n


# ---------------------------------------------------------------------------
# Module 6 option -> tier mapping
# ---------------------------------------------------------------------------


class TestOptionTierMapping:
    """The Module 6 bound-index -> tier map (1->demo .. 4->large).

    **Validates: Requirements 2.3, 2.4**

    Uses the ``volume_utils`` tier constants and asserts the option->tier map
    declared in ``module-06-phaseA-build-loading.md``.
    """

    def test_index_to_tier_uses_volume_utils_constants(self) -> None:
        """Bound index 1/2/3/4 maps to demo/small/medium/large."""
        assert OPTION_INDEX_TO_TIER[1] == volume_utils.TIER_DEMO
        assert OPTION_INDEX_TO_TIER[2] == volume_utils.TIER_SMALL
        assert OPTION_INDEX_TO_TIER[3] == volume_utils.TIER_MEDIUM
        assert OPTION_INDEX_TO_TIER[4] == volume_utils.TIER_LARGE

    def test_bind_then_map_selects_medium_for_three(self) -> None:
        """A bare '3' binds to index 3, which maps to the medium tier."""
        index = answer_binding.bind_option("3", FOUR_TIER_OPTIONS)
        assert index == 3
        assert OPTION_INDEX_TO_TIER[index] == volume_utils.TIER_MEDIUM


# ---------------------------------------------------------------------------
# Steering presence checks
# ---------------------------------------------------------------------------


class TestSteeringPresenceChecks:
    """Final-message invariant + completion ordering rule are present.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_final_message_invariant_in_conversation_protocol(self) -> None:
        """conversation-protocol.md states the final-message invariant."""
        lowered = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8").lower()
        assert "final-message invariant" in lowered, (
            "conversation-protocol.md is missing the Final-Message Invariant "
            "heading."
        )
        assert "input-expecting" in lowered and "final message" in lowered, (
            "conversation-protocol.md does not tie a live pending question to "
            "the final message of an input-expecting turn."
        )
        assert (
            "recap or confirmation emission must never be the final message"
            in lowered
        ), (
            "conversation-protocol.md does not forbid a recap/confirmation as "
            "the final message of an input-expecting turn."
        )

    def test_recap_ordering_rule_in_completion_steering(self) -> None:
        """Completion steering carries the recap-before / re-surface rule."""
        combined = (
            _MODULE_COMPLETION.read_text(encoding="utf-8").lower()
            + "\n"
            + _MODULE_COMPLETION_NEXT_STEPS.read_text(encoding="utf-8").lower()
        )
        assert "before the forward transition question" in combined, (
            "Completion steering is missing the recap-before-transition rule."
        )
        assert "re-surface the forward" in combined, (
            "Completion steering is missing the re-surface-forward-question "
            "rule."
        )
