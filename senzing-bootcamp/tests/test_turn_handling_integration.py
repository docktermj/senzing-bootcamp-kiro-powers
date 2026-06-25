"""Integration tests for the turn-answer-handling bugfix.

These integration checks are steering-driven: there is no live agent runtime,
so each end-to-end flow is modelled as a deterministic check against the
``answer_binding`` / ``volume_utils`` helpers plus the steering content that
instructs the agent. The three flows mirror the Testing Strategy in the design:

- Module 6 Step 1 end-to-end: present options 1-4, reply ``3`` binds to medium,
  the option->tier map yields medium, the steering instructs to persist via
  ``persist_volume_selection`` and advance without re-asking (Property 1).
- Module-completion turn end-to-end: the completion steering requires the
  forward 👉 "Ready for Module X?" as the final message with
  ``config/.question_pending`` written, even when a recap/confirmation is
  emitted (Property 1, Item 1).
- Affirmative-transition flow: an affirmative confirmation still requires
  immediate module start with all required start content (Property 2
  preservation).

Feature: turn-answer-handling
"""

from __future__ import annotations

import sys
from pathlib import Path

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
_MODULE_06_PHASE_A = _STEERING_DIR / "module-06-phaseA-build-loading.md"

# The four-tier numbered option list presented at Module 6 Step 1, ordered to
# match the steering's option->tier map (1->demo, 2->small, 3->medium, 4->large).
FOUR_TIER_OPTIONS = ["demo", "small", "medium", "large"]

OPTION_INDEX_TO_TIER = {
    1: volume_utils.TIER_DEMO,
    2: volume_utils.TIER_SMALL,
    3: volume_utils.TIER_MEDIUM,
    4: volume_utils.TIER_LARGE,
}


# ---------------------------------------------------------------------------
# Module 6 Step 1 end-to-end
# ---------------------------------------------------------------------------


class TestModule6Step1EndToEnd:
    """Reply ``3`` to the four-tier list binds to medium and advances.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_reply_three_binds_to_medium_tier(self) -> None:
        """bind_option('3', four options) == 3 and the map yields medium."""
        index = answer_binding.bind_option("3", FOUR_TIER_OPTIONS)
        assert index == 3, (
            f"A bare '3' against the four-tier list must bind to option 3, got "
            f"{index!r}."
        )
        assert OPTION_INDEX_TO_TIER[index] == volume_utils.TIER_MEDIUM

    def test_persist_volume_selection_helper_exists(self) -> None:
        """volume_utils exposes the persist_volume_selection helper."""
        assert hasattr(volume_utils, "persist_volume_selection"), (
            "volume_utils.persist_volume_selection is missing — the bind path "
            "cannot persist the selection."
        )
        assert callable(volume_utils.persist_volume_selection)

    def test_steering_binds_first_and_maps_options_to_tiers(self) -> None:
        """Module 6 Step 1 instructs bind-first with the 1-4 -> tier map."""
        content = _MODULE_06_PHASE_A.read_text(encoding="utf-8")
        assert "answer_binding.bind_option" in content, (
            "Module 6 Step 1 does not instruct binding via "
            "answer_binding.bind_option."
        )
        for fragment in ("1 → demo", "2 → small", "3 → medium", "4 → large"):
            assert fragment in content, (
                f"Module 6 Step 1 is missing the option->tier mapping "
                f"{fragment!r}."
            )

    def test_steering_persists_and_advances_without_reasking(self) -> None:
        """A successful bind persists via persist_volume_selection and advances."""
        content = _MODULE_06_PHASE_A.read_text(encoding="utf-8")
        assert "volume_utils.persist_volume_selection" in content, (
            "Module 6 Step 1 does not reference volume_utils."
            "persist_volume_selection for a bound selection."
        )
        lowered = content.lower()
        assert "do not re-present the module 6 banner or the volume question" in lowered, (
            "Module 6 Step 1 does not forbid re-presenting the banner/volume "
            "question after a successful bind (the re-ask bug)."
        )
        assert "advance" in lowered, (
            "Module 6 Step 1 does not instruct advancing after a successful "
            "bind."
        )

    def test_steering_falls_through_for_non_matching_reply(self) -> None:
        """A None bind falls through to the unchanged parse path."""
        content = _MODULE_06_PHASE_A.read_text(encoding="utf-8")
        assert "volume_utils.parse_volume_input" in content, (
            "Module 6 Step 1 dropped the parse_volume_input fall-through path."
        )
        # Confirm the fall-through is exercisable: a non-token reply does not
        # bind, so the parser would drive the outcome.
        assert answer_binding.bind_option("3 million", FOUR_TIER_OPTIONS) is None


# ---------------------------------------------------------------------------
# Module-completion turn end-to-end
# ---------------------------------------------------------------------------


class TestModuleCompletionTurnEndToEnd:
    """A completion turn ends with the forward question as the final message.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_completion_requires_forward_question_as_final_message(self) -> None:
        """Completion steering requires the forward 👉 question last."""
        combined = (
            _MODULE_COMPLETION.read_text(encoding="utf-8")
            + "\n"
            + _MODULE_COMPLETION_NEXT_STEPS.read_text(encoding="utf-8")
        )
        lowered = combined.lower()
        assert "final message" in lowered, (
            "Completion steering does not require the forward question to be "
            "the final message of the turn."
        )
        assert "ready for module x" in lowered or "ready to move on to module" in lowered, (
            "Completion steering does not reference the forward transition "
            "question."
        )

    def test_completion_rewrites_question_pending_after_recap(self) -> None:
        """The forward question is re-surfaced with config/.question_pending."""
        combined = (
            _MODULE_COMPLETION.read_text(encoding="utf-8")
            + "\n"
            + _MODULE_COMPLETION_NEXT_STEPS.read_text(encoding="utf-8")
        )
        lowered = combined.lower()
        assert "config/.question_pending" in combined, (
            "Completion steering does not require config/.question_pending to "
            "be written for the re-surfaced forward question."
        )
        assert "after any recap/confirmation" in lowered, (
            "Completion steering does not require re-surfacing the forward "
            "question after a recap/confirmation emission."
        )
        assert (
            "must never be the final message" in lowered
        ), (
            "Completion steering does not forbid a recap/confirmation line as "
            "the final message of the completion turn."
        )

    def test_completion_invariant_references_conversation_protocol(self) -> None:
        """The completion ordering rule defers to the Final-Message Invariant."""
        protocol = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8").lower()
        assert "final-message invariant" in protocol, (
            "conversation-protocol.md is missing the Final-Message Invariant "
            "the completion steering relies on."
        )


# ---------------------------------------------------------------------------
# Affirmative-transition flow
# ---------------------------------------------------------------------------


class TestAffirmativeTransitionFlow:
    """An affirmative confirmation still starts the module immediately.

    **Validates: Requirements 3.1**
    """

    def test_affirmative_requires_immediate_module_start(self) -> None:
        """conversation-protocol.md keeps the immediate same-turn module start."""
        lowered = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8").lower()
        assert "module transition protocol" in lowered, (
            "conversation-protocol.md dropped the Module Transition Protocol."
        )
        assert "immediately begin that module in the same turn" in lowered, (
            "conversation-protocol.md lost the immediate same-turn module-start "
            "requirement on an affirmative confirmation."
        )

    def test_affirmative_requires_all_start_content(self) -> None:
        """The required start content (banner, journey map, etc.) is intact."""
        lowered = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8").lower()
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
