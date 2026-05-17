"""Bug condition exploration tests for leading-question-enforcement bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: leading-question-enforcement

The bug: After a bootcamper answers the last gap-filling sub-step question
(e.g., Step 7d), the agent writes the checkpoint but stops without asking
the next numbered step's leading question (Step 8). The steering files lack
an explicit "step-chaining" instruction for this transition.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_MODULE_01 = _BOOTCAMP_DIR / "steering" / "module-01-business-problem.md"
_MODULE_TRANSITIONS = _BOOTCAMP_DIR / "steering" / "module-transitions.md"
_CONVERSATION_PROTOCOL = _BOOTCAMP_DIR / "steering" / "conversation-protocol.md"

# ---------------------------------------------------------------------------
# Domain Model
# ---------------------------------------------------------------------------


@dataclass
class AgentTurnContext:
    """Represents the context of an agent turn during gap-filling sub-steps.

    Attributes:
        current_step: The current sub-step identifier (e.g., "7d").
        is_last_sub_step_in_sequence: Whether this is the final sub-step.
        undetermined_items_remaining: Count of items still needing answers.
        next_numbered_step_exists: Whether a next numbered step follows.
        next_step_number: The next numbered step (e.g., 8).
    """

    current_step: str
    is_last_sub_step_in_sequence: bool
    undetermined_items_remaining: int
    next_numbered_step_exists: bool
    next_step_number: int


def is_bug_condition(ctx: AgentTurnContext) -> bool:
    """Determine if the given context triggers the bug condition.

    The bug manifests when:
    - currentStep is the last lettered sub-step (e.g., "7d")
    - isLastSubStepInSequence = TRUE
    - undeterminedItemsRemaining = 0
    - nextNumberedStepExists = TRUE
    """
    return (
        ctx.is_last_sub_step_in_sequence
        and ctx.undetermined_items_remaining == 0
        and ctx.next_numbered_step_exists
    )


# ---------------------------------------------------------------------------
# Helpers — Steering File Parsing
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read a steering file's full content."""
    return path.read_text(encoding="utf-8")


def _extract_step_section(markdown: str, step_id: str) -> str:
    """Extract a step or sub-step section from module steering.

    Handles both numbered steps (e.g., "7") and lettered sub-steps (e.g., "7d").
    Steps are formatted as numbered list items with bold text.
    """
    # Try to match sub-step pattern like "7d. **..."
    if re.match(r"\d+[a-z]", step_id):
        pattern = re.compile(
            rf"^{re.escape(step_id)}\.\s+\*\*",
            re.MULTILINE,
        )
    else:
        pattern = re.compile(
            rf"^{re.escape(step_id)}\.\s+\*\*",
            re.MULTILINE,
        )

    match = pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next step/sub-step heading or end of file
    next_step = re.compile(r"^\d+[a-z]?\.\s+\*\*", re.MULTILINE)
    next_match = next_step.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _contains_step_chaining_instruction(text: str, next_step: int) -> bool:
    """Check if text contains an explicit instruction to proceed to the next step.

    Looks for patterns like:
    - "proceed to Step 8"
    - "advance to Step 8"
    - "continue to Step 8"
    - "ask Step 8's question"
    - "present Step 8's 👉 question"
    """
    patterns = [
        rf"proceed.*(?:to|with)\s+Step\s+{next_step}",
        rf"advance.*to\s+Step\s+{next_step}",
        rf"continue.*to\s+Step\s+{next_step}",
        rf"Step\s+{next_step}.*👉\s*question",
        rf"👉\s*question.*Step\s+{next_step}",
        rf"next\s+numbered\s+step",
        rf"immediately\s+proceed",
        rf"same\s+turn",
        rf"do\s+NOT\s+end\s+your\s+turn",
        rf"All\s+sub-steps\s+complete",
    ]
    combined = "|".join(patterns)
    return bool(re.search(combined, text, re.IGNORECASE))


def _sub_step_convention_has_last_step_rule(text: str) -> bool:
    """Check if the Sub-Step Convention section addresses what happens after the last sub-step.

    Looks for patterns like:
    - "after the last sub-step"
    - "final sub-step"
    - "last sub-step"
    - "all sub-steps complete"
    - "proceed to the next numbered step"
    """
    # Extract the Sub-Step Convention section
    convention_match = re.search(
        r"## Sub-Step Convention(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not convention_match:
        return False

    convention_text = convention_match.group(1)

    patterns = [
        r"after\s+the\s+last\s+sub-step",
        r"final\s+sub-step.*(?:proceed|advance|continue|next\s+numbered)",
        r"last\s+sub-step.*(?:proceed|advance|continue|next\s+numbered)",
        r"all\s+sub-steps\s+complete",
        r"no\s+undetermined\s+items\s+remain.*proceed",
    ]
    combined = "|".join(patterns)
    return bool(re.search(combined, convention_text, re.IGNORECASE))


def _end_of_turn_protocol_addresses_sub_step_completion(text: str) -> bool:
    """Check if End-of-Turn Protocol addresses sub-step completion.

    The protocol should explicitly state that completing the last sub-step's
    checkpoint is NOT the end of the turn — the agent must also ask the next
    step's 👉 question.
    """
    # Extract the End-of-Turn Protocol section
    protocol_match = re.search(
        r"## End-of-Turn Protocol(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not protocol_match:
        return False

    protocol_text = protocol_match.group(1)

    patterns = [
        r"sub-step.*completion",
        r"last\s+sub-step.*(?:not|NOT).*end\s+of.*turn",
        r"checkpoint.*(?:not|NOT).*end\s+of.*turn",
        r"checkpoint\s+marks\s+sub-step\s+completion",
        r"gap-filling\s+sequence.*(?:checkpoint|turn)",
        r"sub-step.*checkpoint.*(?:not|NOT).*turn\s+completion",
    ]
    combined = "|".join(patterns)
    return bool(re.search(combined, protocol_text, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------

# Sub-step letters used in Module 1 Step 7
_SUB_STEP_LETTERS = ["a", "b", "c", "d"]

# The last sub-step in Module 1's gap-filling sequence
_LAST_SUB_STEPS = ["7d"]

# All possible sub-steps in Module 1 Step 7
_ALL_SUB_STEPS = [f"7{letter}" for letter in _SUB_STEP_LETTERS]


@st.composite
def st_bug_condition_context(draw: st.DrawFn) -> AgentTurnContext:
    """Generate AgentTurnContext inputs that satisfy the bug condition.

    These represent the scenario where:
    - currentStep is the last lettered sub-step (e.g., "7d")
    - isLastSubStepInSequence = TRUE
    - undeterminedItemsRemaining = 0
    - nextNumberedStepExists = TRUE
    """
    # Pick a last sub-step (currently only "7d" in Module 1)
    current_step = draw(st.sampled_from(_LAST_SUB_STEPS))

    # The next numbered step after Step 7 is Step 8
    next_step = draw(st.just(8))

    return AgentTurnContext(
        current_step=current_step,
        is_last_sub_step_in_sequence=True,
        undetermined_items_remaining=0,
        next_numbered_step_exists=True,
        next_step_number=next_step,
    )


# ---------------------------------------------------------------------------
# Test 1 — Module 01 Missing Step-Chaining Instruction After Step 7d
# ---------------------------------------------------------------------------


class TestModule01StepChainingInstruction:
    """Test 1 — Module 01 lacks step-chaining instruction after Step 7d.

    **Validates: Requirements 1.1, 1.2**

    Parse module-01-business-problem.md, extract the Step 7d section, and
    assert it contains an explicit instruction directing the agent to proceed
    to Step 8's 👉 question after the checkpoint. On unfixed content this
    will FAIL because no such instruction exists — Step 7d contains only
    🛑 STOP with no instruction to advance to Step 8.
    """

    @given(ctx=st_bug_condition_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_step_7d_contains_chaining_instruction(
        self, ctx: AgentTurnContext
    ) -> None:
        """For all bug-condition inputs, steering must contain step-chaining."""
        assert is_bug_condition(ctx), "Generated context must satisfy bug condition"

        content = _read_file(_MODULE_01)
        step_section = _extract_step_section(content, ctx.current_step)

        assert step_section, (
            f"Step {ctx.current_step} section not found in "
            "module-01-business-problem.md"
        )

        assert _contains_step_chaining_instruction(
            step_section, ctx.next_step_number
        ), (
            f"Step {ctx.current_step} section contains 🛑 STOP but no "
            f"instruction to proceed to Step {ctx.next_step_number}. "
            f"The agent has no guidance to advance to the next numbered "
            f"step's 👉 question after completing the last sub-step.\n"
            f"Step section excerpt:\n{step_section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Module Transitions Sub-Step Convention Missing Last-Step Rule
# ---------------------------------------------------------------------------


class TestModuleTransitionsSubStepConvention:
    """Test 2 — Sub-Step Convention lacks rule for after the last sub-step.

    **Validates: Requirements 1.2, 1.3**

    Parse module-transitions.md and assert the Sub-Step Convention section
    includes a rule for what happens after the last sub-step in a sequence.
    On unfixed content this will FAIL because the convention is silent on
    post-final-sub-step behavior.
    """

    @given(ctx=st_bug_condition_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_sub_step_convention_addresses_last_step(
        self, ctx: AgentTurnContext
    ) -> None:
        """For all bug-condition inputs, Sub-Step Convention must define behavior."""
        assert is_bug_condition(ctx), "Generated context must satisfy bug condition"

        content = _read_file(_MODULE_TRANSITIONS)

        assert _sub_step_convention_has_last_step_rule(content), (
            "module-transitions.md Sub-Step Convention does not include a rule "
            "for what happens after the last sub-step in a sequence. "
            "The convention defines naming and checkpointing but is silent on "
            "step-chaining after the final sub-step completes.\n"
            f"Bug condition: currentStep={ctx.current_step}, "
            f"undeterminedItemsRemaining={ctx.undetermined_items_remaining}, "
            f"nextNumberedStep={ctx.next_step_number}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Conversation Protocol Missing Sub-Step Completion Clause
# ---------------------------------------------------------------------------


class TestConversationProtocolSubStepCompletion:
    """Test 3 — End-of-Turn Protocol doesn't address sub-step completion.

    **Validates: Requirements 1.1, 1.3**

    Parse conversation-protocol.md and assert the End-of-Turn Protocol
    section addresses sub-step completion — specifically that writing a
    checkpoint for the last sub-step is NOT the end of the turn. On unfixed
    content this will FAIL because the protocol does not mention sub-step
    completion at all.
    """

    @given(ctx=st_bug_condition_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_end_of_turn_protocol_addresses_sub_step_completion(
        self, ctx: AgentTurnContext
    ) -> None:
        """For all bug-condition inputs, protocol must address sub-step completion."""
        assert is_bug_condition(ctx), "Generated context must satisfy bug condition"

        content = _read_file(_CONVERSATION_PROTOCOL)

        assert _end_of_turn_protocol_addresses_sub_step_completion(content), (
            "conversation-protocol.md End-of-Turn Protocol does not address "
            "sub-step completion. The protocol does not state that writing a "
            "checkpoint for the last sub-step is NOT the end of the turn — "
            "the agent must also present the next step's 👉 question.\n"
            f"Bug condition: currentStep={ctx.current_step}, "
            f"undeterminedItemsRemaining={ctx.undetermined_items_remaining}, "
            f"nextNumberedStep={ctx.next_step_number}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Combined Property: Bug Condition → Step-Chaining Required
# ---------------------------------------------------------------------------


class TestBugConditionProperty:
    """PBT — For all inputs satisfying isBugCondition, steering must chain.

    **Validates: Requirements 1.1, 1.2, 1.3**

    Property: for all inputs satisfying isBugCondition(input), the relevant
    steering text contains an unambiguous instruction to advance to the next
    numbered step's 👉 question in the same turn.

    This is the combined property test that checks ALL three steering files
    together. On unfixed code, this will FAIL because none of the files
    contain the required step-chaining instructions.
    """

    @given(ctx=st_bug_condition_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_bug_condition_requires_step_chaining_in_steering(
        self, ctx: AgentTurnContext
    ) -> None:
        """For all bug-condition inputs, at least one steering file must chain."""
        assert is_bug_condition(ctx), "Generated context must satisfy bug condition"

        module_content = _read_file(_MODULE_01)
        transitions_content = _read_file(_MODULE_TRANSITIONS)
        protocol_content = _read_file(_CONVERSATION_PROTOCOL)

        step_section = _extract_step_section(module_content, ctx.current_step)

        # Check all three sources for step-chaining instructions
        has_module_instruction = _contains_step_chaining_instruction(
            step_section, ctx.next_step_number
        )
        has_convention_rule = _sub_step_convention_has_last_step_rule(
            transitions_content
        )
        has_protocol_clause = _end_of_turn_protocol_addresses_sub_step_completion(
            protocol_content
        )

        assert has_module_instruction or has_convention_rule or has_protocol_clause, (
            f"NONE of the steering files contain an unambiguous instruction to "
            f"advance to Step {ctx.next_step_number}'s 👉 question after "
            f"completing the last sub-step ({ctx.current_step}).\n\n"
            f"Counterexample:\n"
            f"  - currentStep: {ctx.current_step}\n"
            f"  - isLastSubStepInSequence: True\n"
            f"  - undeterminedItemsRemaining: 0\n"
            f"  - nextNumberedStepExists: True\n"
            f"  - nextStepNumber: {ctx.next_step_number}\n\n"
            f"Findings:\n"
            f"  - module-01-business-problem.md Step {ctx.current_step}: "
            f"Contains 🛑 STOP but no instruction to proceed to "
            f"Step {ctx.next_step_number}\n"
            f"  - module-transitions.md Sub-Step Convention: Silent on "
            f"post-final-sub-step behavior\n"
            f"  - conversation-protocol.md End-of-Turn Protocol: Does not "
            f"address sub-step completion"
        )


# ===========================================================================
# PRESERVATION PROPERTY TESTS (Task 2)
#
# These tests verify baseline behavior that MUST be preserved after the fix.
# They should PASS on UNFIXED steering files — confirming the behavior exists.
# ===========================================================================

# ---------------------------------------------------------------------------
# Helpers — Preservation Checks
# ---------------------------------------------------------------------------


def _step_7_has_one_item_per_turn_instruction(content: str) -> bool:
    """Check that Step 7 contains 'ask about only one undetermined item per turn'."""
    # Extract Step 7 section (before sub-steps start)
    step7_match = re.search(
        r"^7\.\s+\*\*Confirm inferred details and fill gaps\*\*"
        r"(.*?)(?=^7[a-z]\.\s+\*\*|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not step7_match:
        return False
    step7_text = step7_match.group(1)
    return bool(
        re.search(r"[Aa]sk about only one undetermined item per turn", step7_text)
    )


def _sub_step_has_stop_marker(content: str, sub_step_id: str) -> bool:
    """Check that a specific sub-step contains a 🛑 STOP marker."""
    section = _extract_step_section(content, sub_step_id)
    if not section:
        return False
    return "🛑" in section and "STOP" in section


def _get_all_stop_markers_in_step7_substeps(content: str) -> dict[str, bool]:
    """Return a dict mapping each sub-step (7a-7d) to whether it has a 🛑 STOP."""
    results = {}
    for letter in _SUB_STEP_LETTERS:
        sub_step_id = f"7{letter}"
        results[sub_step_id] = _sub_step_has_stop_marker(content, sub_step_id)
    return results


def _conversation_protocol_has_one_question_rule(content: str) -> bool:
    """Check that conversation-protocol.md contains the One Question Rule section."""
    return bool(re.search(r"## One Question Rule", content))


def _one_question_rule_has_critical_marker(content: str) -> bool:
    """Check that the One Question Rule has the CRITICAL — ZERO TOLERANCE marker."""
    # Find the One Question Rule section
    oqr_match = re.search(
        r"## One Question Rule(.*?)(?=^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not oqr_match:
        return False
    oqr_text = oqr_match.group(1)
    return bool(re.search(r"CRITICAL.*ZERO TOLERANCE", oqr_text))


def _one_question_rule_has_exactly_one_question(content: str) -> bool:
    """Check that the One Question Rule states 'exactly one' 👉 question per turn."""
    oqr_match = re.search(
        r"## One Question Rule(.*?)(?=^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not oqr_match:
        return False
    oqr_text = oqr_match.group(1)
    return bool(re.search(r"exactly one.*👉\s*question", oqr_text, re.IGNORECASE))


def _conversation_protocol_has_gate_behavior(content: str) -> bool:
    """Check that conversation-protocol.md references ⛔ gate behavior."""
    # The Question Stop Protocol mentions ⛔ gate
    return bool(re.search(r"⛔\s*gate", content))


def _gate_blocks_advancement(content: str) -> bool:
    """Check that ⛔ gates block advancement (end-of-turn boundary)."""
    # The Question Stop Protocol says "Every 👉 question and ⛔ gate is an
    # end-of-turn boundary"
    return bool(
        re.search(
            r"⛔\s*gate.*end-of-turn\s*boundary|end-of-turn\s*boundary.*⛔\s*gate",
            content,
            re.IGNORECASE,
        )
    )


# ---------------------------------------------------------------------------
# Hypothesis Strategies — Preservation Tests
# ---------------------------------------------------------------------------


@st.composite
def st_mid_sequence_context(draw: st.DrawFn) -> AgentTurnContext:
    """Generate AgentTurnContext for mid-sequence sub-steps (NOT the bug condition).

    These represent scenarios where undetermined items remain:
    - currentStep is any sub-step (7a, 7b, 7c, 7d)
    - undeterminedItemsRemaining > 0
    - The agent should ask only the next undetermined item and stop
    """
    current_step = draw(st.sampled_from(_ALL_SUB_STEPS))
    # At least 1 undetermined item remains (non-bug-condition)
    undetermined = draw(st.integers(min_value=1, max_value=4))
    # Whether this is the last sub-step doesn't matter — what matters is
    # undetermined items remain
    is_last = current_step == "7d"

    return AgentTurnContext(
        current_step=current_step,
        is_last_sub_step_in_sequence=is_last,
        undetermined_items_remaining=undetermined,
        next_numbered_step_exists=True,
        next_step_number=8,
    )


@st.composite
def st_any_sub_step(draw: st.DrawFn) -> str:
    """Generate any sub-step identifier from 7a to 7d."""
    return draw(st.sampled_from(_ALL_SUB_STEPS))


# ---------------------------------------------------------------------------
# Test 5 — Mid-Sequence Sub-Steps Contain One-Item-Per-Turn and 🛑 STOP
# ---------------------------------------------------------------------------


class TestPreservationMidSequenceStops:
    """Test 5 — Mid-sequence sub-steps have one-item-per-turn and 🛑 STOP.

    **Validates: Requirements 3.1, 3.2**

    For all sub-step positions where undeterminedItemsRemaining > 0
    (non-bug-condition), the steering contains "ask about only one
    undetermined item per turn" instruction and each sub-step has 🛑 STOP.

    These tests PASS on unfixed steering — confirming baseline behavior.
    """

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_step7_has_one_item_per_turn_instruction(
        self, ctx: AgentTurnContext
    ) -> None:
        """Step 7 contains 'ask about only one undetermined item per turn'."""
        assert ctx.undetermined_items_remaining > 0, (
            "Mid-sequence context must have undetermined items remaining"
        )

        content = _read_file(_MODULE_01)
        assert _step_7_has_one_item_per_turn_instruction(content), (
            f"Step 7 in module-01-business-problem.md does not contain "
            f"'ask about only one undetermined item per turn' instruction.\n"
            f"Context: currentStep={ctx.current_step}, "
            f"undeterminedItemsRemaining={ctx.undetermined_items_remaining}"
        )

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_current_sub_step_has_stop_marker(self, ctx: AgentTurnContext) -> None:
        """Each sub-step position has a 🛑 STOP marker."""
        assert ctx.undetermined_items_remaining > 0, (
            "Mid-sequence context must have undetermined items remaining"
        )

        content = _read_file(_MODULE_01)
        assert _sub_step_has_stop_marker(content, ctx.current_step), (
            f"Sub-step {ctx.current_step} in module-01-business-problem.md "
            f"does not contain a 🛑 STOP marker.\n"
            f"Context: undeterminedItemsRemaining="
            f"{ctx.undetermined_items_remaining}"
        )


# ---------------------------------------------------------------------------
# Test 6 — All 🛑 STOP Markers in Steps 7a–7d Are Present
# ---------------------------------------------------------------------------


class TestPreservationAllStopMarkers:
    """Test 6 — All existing 🛑 STOP markers in sub-steps 7a–7d are present.

    **Validates: Requirements 3.1, 3.2**

    Verify that every sub-step (7a, 7b, 7c, 7d) has a 🛑 STOP marker.
    This establishes the baseline that must be preserved after the fix.
    """

    @given(sub_step=st_any_sub_step())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_all_sub_steps_have_stop_markers(self, sub_step: str) -> None:
        """Every sub-step 7a–7d has a 🛑 STOP marker."""
        content = _read_file(_MODULE_01)
        assert _sub_step_has_stop_marker(content, sub_step), (
            f"Sub-step {sub_step} in module-01-business-problem.md "
            f"does not contain a 🛑 STOP marker. All sub-steps must have "
            f"🛑 STOP to enforce one-question-per-turn behavior."
        )


# ---------------------------------------------------------------------------
# Test 7 — One Question Rule Is Not Weakened or Removed
# ---------------------------------------------------------------------------


class TestPreservationOneQuestionRule:
    """Test 7 — The 'One Question Rule' in conversation-protocol.md is intact.

    **Validates: Requirements 3.1, 3.3**

    Verify that conversation-protocol.md contains the One Question Rule
    section with its CRITICAL — ZERO TOLERANCE marker and the statement
    that each turn contains exactly one 👉 question.
    """

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_one_question_rule_section_exists(self, ctx: AgentTurnContext) -> None:
        """conversation-protocol.md has a One Question Rule section."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _conversation_protocol_has_one_question_rule(content), (
            "conversation-protocol.md does not contain a '## One Question Rule' "
            "section. This section is critical for enforcing one-question-per-turn."
        )

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_one_question_rule_has_critical_marker(
        self, ctx: AgentTurnContext
    ) -> None:
        """One Question Rule has CRITICAL — ZERO TOLERANCE enforcement marker."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _one_question_rule_has_critical_marker(content), (
            "conversation-protocol.md One Question Rule does not contain the "
            "'CRITICAL — ZERO TOLERANCE' enforcement marker. This marker "
            "signals the rule's absolute priority."
        )

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_one_question_rule_states_exactly_one(
        self, ctx: AgentTurnContext
    ) -> None:
        """One Question Rule states 'exactly one' 👉 question per turn."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _one_question_rule_has_exactly_one_question(content), (
            "conversation-protocol.md One Question Rule does not state that "
            "each turn contains 'exactly one' 👉 question. This is the core "
            "preservation requirement."
        )


# ---------------------------------------------------------------------------
# Test 8 — ⛔ Gates Continue to Block Advancement
# ---------------------------------------------------------------------------


class TestPreservationGateBehavior:
    """Test 8 — ⛔ gates continue to block advancement.

    **Validates: Requirements 3.4, 3.5**

    Verify that conversation-protocol.md references ⛔ gate behavior and
    that gates are defined as end-of-turn boundaries that block advancement
    regardless of any step-chaining rule.
    """

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_gate_behavior_referenced(self, ctx: AgentTurnContext) -> None:
        """conversation-protocol.md references ⛔ gate behavior."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _conversation_protocol_has_gate_behavior(content), (
            "conversation-protocol.md does not reference ⛔ gate behavior. "
            "Gates must continue to block advancement regardless of any "
            "step-chaining rule added by the fix."
        )

    @given(ctx=st_mid_sequence_context())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_gate_is_end_of_turn_boundary(self, ctx: AgentTurnContext) -> None:
        """⛔ gates are defined as end-of-turn boundaries."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        assert _gate_blocks_advancement(content), (
            "conversation-protocol.md does not define ⛔ gates as "
            "'end-of-turn boundary'. Gates must block advancement — "
            "the step-chaining rule must not override gate behavior."
        )
