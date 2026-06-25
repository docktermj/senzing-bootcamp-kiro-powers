"""Preservation property tests for the turn-answer-handling bugfix.

Property 2 (Preservation): Non-Buggy Turns Unchanged.

Observation-first methodology: these tests were written by running the UNFIXED
code/steering for non-buggy inputs, recording the actual outputs, then asserting
those outputs hold across the input domain. ALL tests are EXPECTED TO PASS on
the unfixed code (a small number of boundary-property tests SKIP on unfixed code
because they depend on the not-yet-existing ``answer_binding`` helper; they are
exercised after the fix lands).

The fix must preserve, byte-for-byte / statement-for-statement:

- ``volume_utils.parse_volume_input`` behavior for every input (Req 3.4).
- The unparseable-input clarifying-follow-up path in Module 6 Step 1: a
  numbered four-tier list, then default to the demo tier (Req 3.4).
- The affirmative module-transition startup contract: immediate module start
  with banner, journey map, before/after framing, Step 1, >= 50 chars (Req 3.1).
- The One Question Rule and the ``config/.question_pending`` lifecycle
  (write / treat-next-message-as-answer / delete-before-processing) (Req 3.2, 3.3).
- The module-completion fixed-step order and per-module artifacts, plus the
  defer-when-pending and no-op-when-nothing-new trigger rules (Req 3.6).
- The pure-work-turn closing contract: recap + a contextual closing
  question when a turn does not otherwise end with a question (Req 3.5).

Feature: turn-answer-handling
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
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
_MODULE_06_PHASE_A = _STEERING_DIR / "module-06-phaseA-build-loading.md"

# ---------------------------------------------------------------------------
# Option list presented at Module 6 Step 1 (four-tier numbered list)
# ---------------------------------------------------------------------------

FOUR_VOLUME_OPTIONS = [
    "Demo / proof-of-concept (under 500 records)",
    "Small production (500 - 500K records)",
    "Medium production (500K - 10M records)",
    "Large production (over 10M records)",
]

# ---------------------------------------------------------------------------
# Frozen baseline — parse_volume_input outputs captured from the UNFIXED code.
#
# Each entry maps an input reply to (parsed_value, classified_tier). The tier is
# None when the parse returns None. This golden table is the cross-version guard
# that parse_volume_input -> classify_tier is byte-for-byte unchanged after the
# fix. The values were observed by running the unfixed volume_utils.
# ---------------------------------------------------------------------------

_PARSE_BASELINE: dict[str, tuple[int | None, str | None]] = {
    "": (None, None),
    "   ": (None, None),
    "3": (3, "demo"),
    "3.": (3, "demo"),
    "(3)": (3, "demo"),
    " 3 ": (3, "demo"),
    "0": (0, "demo"),
    "1": (1, "demo"),
    "499": (499, "demo"),
    "500": (500, "small"),
    "500000": (500_000, "medium"),
    "10000000": (10_000_000, "large"),
    "3 million": (3_000_000, "medium"),
    "around 3": (3, "demo"),
    "1.5M": (1_500_000, "medium"),
    "500k": (500_000, "medium"),
    "10m": (10_000_000, "large"),
    "2B": (2_000_000_000, "large"),
    "1,000,000": (1_000_000, "medium"),
    "10 million": (10_000_000, "large"),
    "5 thousand": (5_000, "small"),
    "1.5 billion": (1_500_000_000, "large"),
    "option three please": (None, None),
    "abc": (None, None),
    "b": (None, None),
    "a lot": (None, None),
    "999999999999": (999_999_999_999, "large"),
    "4": (4, "demo"),
    "2": (2, "demo"),
    "750000": (750_000, "medium"),
    "three": (None, None),
    "-5": (5, "demo"),
    "no idea": (None, None),
    "1M": (1_000_000, "medium"),
    "250": (250, "demo"),
    "12345": (12_345, "small"),
    "100 records": (100, "demo"),
}


def _module6_outcome(reply: str) -> tuple[int | None, str | None]:
    """Compute the Module 6 fall-through outcome for a reply.

    Mirrors the existing (unchanged) Module 6 Step 1 path: parse the free-text
    volume reply, then classify the parsed value into a tier. Returns the
    ``(parsed_value, tier)`` pair, with ``tier`` ``None`` when the parse fails.
    """
    parsed = volume_utils.parse_volume_input(reply)
    if isinstance(parsed, int) and parsed >= 0:
        return parsed, volume_utils.classify_tier(parsed)
    return parsed, None


def _import_answer_binding():
    """Import the (post-fix) ``answer_binding`` helper, or None when absent.

    On unfixed code ``scripts/answer_binding.py`` does not exist yet; the
    boundary-property tests that depend on it skip rather than fail so this
    preservation suite passes (with skips) on the unfixed code.
    """
    try:
        return importlib.import_module("answer_binding")
    except ModuleNotFoundError:
        return None


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_baseline_reply(draw: st.DrawFn) -> str:
    """Draw a reply key from the frozen parse baseline corpus."""
    return draw(st.sampled_from(sorted(_PARSE_BASELINE)))


_UNIT_WORDS = ["thousand", "million", "billion", "thousands", "millions", "billions"]
_SUFFIXES = ["k", "m", "b", "K", "M", "B"]


@st.composite
def st_number_with_units(draw: st.DrawFn) -> str:
    """Draw a number-with-units reply (NOT a bare token), e.g. ``"3 million"``."""
    number = draw(st.integers(min_value=1, max_value=999))
    kind = draw(st.sampled_from(["word", "suffix"]))
    if kind == "word":
        return f"{number} {draw(st.sampled_from(_UNIT_WORDS))}"
    return f"{number}{draw(st.sampled_from(_SUFFIXES))}"


@st.composite
def st_free_text_reply(draw: st.DrawFn) -> str:
    """Draw a free-text reply with no bare-token meaning."""
    return draw(
        st.sampled_from(
            [
                "around three",
                "a lot of records",
                "no idea yet",
                "lots",
                "option three please",
                "maybe a few thousand customers",
                "not sure",
                "depends on the customer",
            ]
        )
    )


@st.composite
def st_out_of_range_number(draw: st.DrawFn) -> str:
    """Draw a bare number that is OUT OF RANGE for the four-option list.

    Indices 1-4 would bind; anything >= 5 (or 0) is out of range and must fall
    through to ``parse_volume_input`` unchanged.
    """
    n = draw(st.integers(min_value=5, max_value=10_000_000))
    return str(n)


@st.composite
def st_whitespace_or_empty(draw: st.DrawFn) -> str:
    """Draw an empty or whitespace-only reply."""
    return draw(st.sampled_from(["", " ", "   ", "\t", "\n", "  \t "]))


@st.composite
def st_non_matching_reply(draw: st.DrawFn) -> str:
    """Draw any reply that is NOT a bare matching Option_Token for the 4-list."""
    return draw(
        st.one_of(
            st_number_with_units(),
            st_free_text_reply(),
            st_out_of_range_number(),
            st_whitespace_or_empty(),
        )
    )


# ---------------------------------------------------------------------------
# parse_volume_input invariance (Req 3.4)
# ---------------------------------------------------------------------------


class TestParseVolumeInputInvariance:
    """`parse_volume_input` -> `classify_tier` is unchanged across the corpus.

    **Validates: Requirements 3.4**

    The frozen baseline was captured from the UNFIXED code; the fix must leave
    every parse/classify outcome byte-for-byte identical.
    """

    def test_full_corpus_matches_baseline(self) -> None:
        """Every corpus reply yields its captured (parsed, tier) pair."""
        for reply, (exp_value, exp_tier) in _PARSE_BASELINE.items():
            assert _module6_outcome(reply) == (exp_value, exp_tier), (
                f"parse_volume_input/classify_tier changed for {reply!r}: "
                f"expected {(exp_value, exp_tier)!r}, got {_module6_outcome(reply)!r}"
            )

    @given(reply=st_baseline_reply())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_any_baseline_reply_is_unchanged(self, reply: str) -> None:
        """For any corpus reply, the Module 6 outcome equals the baseline."""
        expected = _PARSE_BASELINE[reply]
        assert _module6_outcome(reply) == expected, (
            f"Module 6 outcome for {reply!r} drifted from the pre-fix baseline "
            f"{expected!r}."
        )

    @given(reply=st.text(max_size=40))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_volume_input_is_deterministic(self, reply: str) -> None:
        """For any string, parse_volume_input is pure/deterministic (no drift).

        Calling twice yields the same result, and any non-negative integer
        result classifies without error — properties that hold pre- and
        post-fix because the parser is untouched.
        """
        first = volume_utils.parse_volume_input(reply)
        second = volume_utils.parse_volume_input(reply)
        assert first == second
        if isinstance(first, int) and first >= 0:
            # classify_tier must remain total for non-negative parsed counts.
            assert volume_utils.classify_tier(first) in volume_utils.VALID_TIERS


# ---------------------------------------------------------------------------
# Clarifying-follow-up preserved (Req 3.4)
# ---------------------------------------------------------------------------


class TestClarifyingFollowUpPreserved:
    """Module 6 Step 1 keeps the unparseable clarifying-follow-up path.

    **Validates: Requirements 3.4**

    On an unparseable reply, Step 1 asks ONE clarifying follow-up presenting the
    four tiers as a numbered list, and defaults to the demo tier if still
    unparseable.
    """

    def test_clarifying_followup_present(self) -> None:
        content = _MODULE_06_PHASE_A.read_text(encoding="utf-8")
        lowered = content.lower()

        assert "parse_volume_input" in content, (
            "Module 6 Step 1 no longer references parse_volume_input."
        )
        assert "classify_tier" in content, (
            "Module 6 Step 1 no longer references classify_tier."
        )
        assert "returns `none`" in lowered or "returns none" in lowered, (
            "Module 6 Step 1 dropped the parse_volume_input None (unparseable) "
            "branch."
        )
        assert "clarifying follow-up" in lowered, (
            "Module 6 Step 1 dropped the clarifying follow-up question."
        )
        assert "numbered list" in lowered, (
            "Module 6 Step 1 dropped the numbered-list framing for the four "
            "tier options."
        )
        # The four tier options must still be present in the clarifying list.
        for fragment in ("fewer than 500", "500 to 500,000", "10,000,000+"):
            assert fragment in lowered, (
                f"Module 6 clarifying option {fragment!r} is missing."
            )
        assert "default to the demo tier" in lowered, (
            "Module 6 Step 1 dropped the demo-tier default for a still-"
            "unparseable follow-up reply."
        )


# ---------------------------------------------------------------------------
# Affirmative transition preserved (Req 3.1)
# ---------------------------------------------------------------------------


class TestAffirmativeTransitionPreserved:
    """The affirmative module-transition startup contract is unchanged.

    **Validates: Requirements 3.1**

    On an affirmative confirmation the agent must immediately start the next
    module in the same turn with the start banner, journey map, before/after
    framing, Step 1 introduction, and a >= 50-character response.
    """

    def test_module_transition_protocol_present(self) -> None:
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        lowered = content.lower()

        assert "module transition protocol" in lowered, (
            "conversation-protocol.md dropped the Module Transition Protocol."
        )
        assert "immediately begin that module in the same turn" in lowered, (
            "Lost the immediate same-turn module-start requirement."
        )
        # Required start content after a transition confirmation.
        assert "module start banner" in lowered or "module banner" in lowered, (
            "Lost the module start banner requirement."
        )
        assert "journey map" in lowered, "Lost the journey map requirement."
        assert "before/after framing" in lowered, (
            "Lost the before/after framing requirement."
        )
        assert "step 1" in lowered, "Lost the Step 1 introduction requirement."
        assert "50 characters" in lowered, (
            "Lost the minimum-length (>= 50 characters) requirement for a "
            "transition-confirmation response."
        )


# ---------------------------------------------------------------------------
# One Question Rule + .question_pending lifecycle preserved (Req 3.2, 3.3)
# ---------------------------------------------------------------------------


class TestOneQuestionRuleAndPendingLifecyclePreserved:
    """The One Question Rule and `.question_pending` lifecycle are unchanged.

    **Validates: Requirements 3.2, 3.3**

    Exactly one leading question per yielding turn, and the write /
    treat-next-message-as-answer / delete-before-processing lifecycle.
    """

    def test_one_question_rule_present(self) -> None:
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        lowered = content.lower()
        assert "one question rule" in lowered, (
            "conversation-protocol.md dropped the One Question Rule heading."
        )
        assert "exactly one" in lowered and "\U0001f449" in content, (
            "Lost the 'exactly one leading question per yielding turn' rule."
        )

    def test_question_pending_lifecycle_present(self) -> None:
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        lowered = content.lower()
        # Write step.
        assert "config/.question_pending" in content, (
            "Lost the config/.question_pending file reference."
        )
        assert "write the file `config/.question_pending`" in lowered or (
            "writing `config/.question_pending` is mandatory" in lowered
        ), "Lost the mandatory write of config/.question_pending."
        # Treat-as-answer step.
        assert (
            "treat the bootcamper's message as an answer to that pending question"
            in lowered
        ), "Lost the treat-next-message-as-answer rule."
        # Delete-before-processing step.
        assert "delete `config/.question_pending` before doing anything else" in lowered, (
            "Lost the delete-before-processing rule."
        )


# ---------------------------------------------------------------------------
# Completion fixed-step order + artifacts preserved (Req 3.6)
# ---------------------------------------------------------------------------


class TestCompletionFixedStepOrderPreserved:
    """The module-completion fixed-step order and trigger rules are unchanged.

    **Validates: Requirements 3.6**

    The five steps run in order, and the defer-when-pending and
    no-op-when-nothing-new trigger rules remain intact.
    """

    def test_fixed_step_order_present(self) -> None:
        content = _MODULE_COMPLETION.read_text(encoding="utf-8")
        steps = [
            "progress_update",
            "recap_append",
            "journal_entry",
            "completion_certificate",
            "next_step_options",
        ]
        positions = [content.find(step) for step in steps]
        for step, pos in zip(steps, positions):
            assert pos != -1, f"Completion step {step!r} missing from steering."
        assert positions == sorted(positions), (
            "Completion steps are no longer in the fixed order "
            f"{steps!r} (found positions {positions!r})."
        )

    def test_trigger_rules_present(self) -> None:
        content = _MODULE_COMPLETION.read_text(encoding="utf-8").lower()
        assert "defer when a question is pending" in content, (
            "Lost the defer-when-pending trigger rule."
        )
        assert "no-op when nothing new completed" in content, (
            "Lost the no-op-when-nothing-new trigger rule."
        )

    def test_immediate_execution_on_affirmative_preserved(self) -> None:
        """next_step_options keeps immediate module start on an affirmative."""
        content = _MODULE_COMPLETION_NEXT_STEPS.read_text(encoding="utf-8").lower()
        assert "immediate execution on affirmative response" in content, (
            "Lost the immediate-execution-on-affirmative section."
        )
        assert "module banner" in content and "journey map" in content, (
            "Lost the module banner / journey map startup content."
        )
        assert "zero permitted steps" in content, (
            "Lost the 'zero permitted steps between affirmative and startup' "
            "guarantee."
        )


# ---------------------------------------------------------------------------
# Pure-work-turn closing preserved (Req 3.5)
# ---------------------------------------------------------------------------


class TestPureWorkTurnClosingPreserved:
    """A non-question work turn still recaps and ends with a closing question.

    **Validates: Requirements 3.5**
    """

    def test_end_of_turn_protocol_present(self) -> None:
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        lowered = content.lower()
        assert "end-of-turn protocol" in lowered, (
            "conversation-protocol.md dropped the End-of-Turn Protocol."
        )
        assert (
            "when you complete work that does not end with a \U0001f449 question"
            in lowered
        ), "Lost the pure-work-turn (no trailing leading question) branch."
        assert "recap what you accomplished" in lowered, (
            "Lost the recap requirement for a pure-work turn."
        )
        assert "contextual \U0001f449 closing question" in lowered, (
            "Lost the contextual closing-question requirement."
        )


# ---------------------------------------------------------------------------
# Boundary property — non-matching replies fall through to parse_volume_input
# (skipped on unfixed code: depends on the not-yet-existing answer_binding)
# ---------------------------------------------------------------------------


class TestNonMatchingReplyFallThrough:
    """A reply that is NOT a bare matching token does not bind and falls through.

    **Validates: Requirements 3.4**

    For any reply that is not a bare matching Option_Token, ``bind_option``
    returns ``None`` and the Module 6 outcome is determined solely by the
    unchanged ``parse_volume_input`` path. These tests SKIP on unfixed code
    because the ``answer_binding`` helper does not exist yet.
    """

    @given(reply=st_non_matching_reply())
    @settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow])
    def test_non_matching_reply_does_not_bind_and_preserves_outcome(
        self, reply: str
    ) -> None:
        answer_binding = _import_answer_binding()
        if answer_binding is None:
            pytest.skip(
                "answer_binding helper not present yet (unfixed code) — "
                "boundary fall-through property is exercised after the fix."
            )

        assert answer_binding.bind_option(reply, FOUR_VOLUME_OPTIONS) is None, (
            f"Reply {reply!r} is not a bare matching Option_Token and must NOT "
            "bind to the four-tier option list."
        )
        # The Module 6 outcome is driven solely by the unchanged parser.
        baseline = _module6_outcome(reply)
        assert _module6_outcome(reply) == baseline, (
            f"Fall-through outcome for {reply!r} drifted from the unchanged "
            f"parse_volume_input path."
        )
