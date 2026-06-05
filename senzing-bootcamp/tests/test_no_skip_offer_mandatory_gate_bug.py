"""Bug condition exploration tests for no-skip-offer-mandatory-gate bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists:
the agent can offer to skip a ⛔ mandatory gate step because no steering rule
or hook prevents it. Tests are EXPECTED TO FAIL on unfixed code — failure
confirms the steering gap.

Feature: no-skip-offer-mandatory-gate

**Validates: Requirements 1.1, 1.2, 1.3**
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"

_AGENT_INSTRUCTIONS = _STEERING_DIR / "agent-instructions.md"
_CONVERSATION_PROTOCOL = _STEERING_DIR / "conversation-protocol.md"
_MODULE3_STEERING = _STEERING_DIR / "module-03-system-verification.md"
# Module 3 was refactored from a monolith into a dispatcher + phase sub-files.
# Step 8 (Database Operations) and the "proceed DIRECTLY to Step 9" agent-behavior
# instruction now live in phase 1; Step 9 (Web Service + Visualization) and its
# mandatory gate block now live in phase 2.
_MODULE3_PHASE1 = _STEERING_DIR / "module-03-phase1-verification.md"
_MODULE3_PHASE2 = _STEERING_DIR / "module-03-phase2-visualization.md"

# ---------------------------------------------------------------------------
# Constants — Skip-offer patterns (the bug condition)
# ---------------------------------------------------------------------------

_SKIP_OFFER_PHRASES = [
    "would you like to continue with",
    "or skip ahead",
    "or move on to the next module",
    "would you like to skip",
    "or bypass",
    "skip the visualization",
    "move on to Module 4",
    "or we can skip",
    "if you'd like to skip",
    "continue with the remaining steps",
]

_MANDATORY_GATE_STEPS = [
    "Step 9",
    "Web Service + Visualization",
    "visualization",
]

# Patterns that would indicate the fix is in place
_SKIP_OFFER_PROHIBITION_PATTERNS = re.compile(
    r"(never|do\s+not|must\s+not|shall\s+not|prohibited|forbid)"
    r".*"
    r"(offer\s+to\s+skip|presenting\s+it\s+as\s+a\s+choice|"
    r"skip\s+offer|offer.*bypass|ask.*skip.*mandatory)",
    re.IGNORECASE,
)

_PROCEED_DIRECTLY_PATTERN = re.compile(
    r"proceed\s+DIRECTLY\s+to\s+Step\s+9",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read a steering file's content."""
    return path.read_text(encoding="utf-8")


def _extract_mandatory_gate_section(content: str) -> str:
    """Extract the Mandatory Gate Precedence section from agent-instructions.md."""
    match = re.search(r"^## Mandatory Gate Precedence\b", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^## ", content[start + 1:], re.MULTILINE)
    if next_heading:
        return content[start:start + 1 + next_heading.start()]
    return content[start:]


def _extract_self_check_section(content: str) -> str:
    """Extract the Self-Check section from conversation-protocol.md."""
    match = re.search(r"^## Self-Check\b", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^## ", content[start + 1:], re.MULTILINE)
    if next_heading:
        return content[start:start + 1 + next_heading.start()]
    return content[start:]


def _extract_step8_region(content: str) -> str:
    """Extract the Step 8 region from module-03 phase 1.

    After the module-03 dispatcher refactor, Step 8 (Database Operations) lives
    in ``module-03-phase1-verification.md`` and Step 9 lives in a separate phase
    file. The agent-behavior / proceed-directly instruction sits after Step 8 in
    phase 1, just before the pointer that loads the phase 2 visualization file.
    Returns the content from the Step 8 heading to the end of the phase 1 file.
    """
    step8_match = re.search(r"^###\s+Step\s+8\b", content, re.MULTILINE)
    if not step8_match:
        return ""
    return content[step8_match.end():]


def _count_self_check_items(section: str) -> int:
    """Count numbered items in the Self-Check section."""
    items = re.findall(r"^\s*\d+\.\s+", section, re.MULTILINE)
    return len(items)


# ---------------------------------------------------------------------------
# Hypothesis strategies — generate skip-offer question content
# ---------------------------------------------------------------------------


@st.composite
def st_skip_offer_question(draw: st.DrawFn) -> dict:
    """Generate a question that offers to skip a ⛔ mandatory gate step.

    This represents the bug condition: a question referencing a mandatory gate
    step that offers to skip or bypass it.

    Returns:
        A dict with type, step reference, and question content.
    """
    skip_phrase = draw(st.sampled_from(_SKIP_OFFER_PHRASES))
    gate_step = draw(st.sampled_from(_MANDATORY_GATE_STEPS))
    prefix = draw(st.sampled_from([
        "👉 ",
        "👉 Would you like to ",
        "👉 Ready to ",
        "👉 I can ",
    ]))
    filler = draw(st.sampled_from([
        f"proceed with {gate_step}",
        f"continue to {gate_step}",
        f"do the {gate_step}",
        f"run {gate_step}",
    ]))

    question_content = f"{prefix}{filler}, {skip_phrase}?"

    return {
        "type": "question",
        "referencesStep": {"name": gate_step, "hasMandatoryGate": True},
        "offersSkipOrBypass": True,
        "initiator": "agent",
        "content": question_content,
    }


@st.composite
def st_non_mandatory_skip_offer(draw: st.DrawFn) -> dict:
    """Generate a question that offers to skip a NON-mandatory step.

    This is NOT a bug condition — skip offers for non-⛔ steps are permitted.

    Returns:
        A dict representing a permitted skip-offer question.
    """
    non_mandatory_steps = [
        "performance report",
        "optional cleanup",
        "bonus exercise",
        "extra examples",
    ]
    step = draw(st.sampled_from(non_mandatory_steps))
    skip_phrase = draw(st.sampled_from(_SKIP_OFFER_PHRASES[:5]))

    return {
        "type": "question",
        "referencesStep": {"name": step, "hasMandatoryGate": False},
        "offersSkipOrBypass": True,
        "initiator": "agent",
        "content": f"👉 Would you like to see the {step}, {skip_phrase}?",
    }


# ---------------------------------------------------------------------------
# Test 1 — agent-instructions.md lacks skip-offer prohibition
# ---------------------------------------------------------------------------


class TestAgentInstructionsSkipOfferProhibition:
    """Test 1 — Mandatory Gate Precedence section lacks skip-offer prohibition.

    The section prohibits SKIPPING ⛔ steps but does NOT prohibit OFFERING to
    skip them. The agent interprets "don't skip" as "don't skip without asking"
    rather than "don't even ask."

    **Validates: Requirements 1.1, 1.2**
    """

    def test_mandatory_gate_section_exists(self) -> None:
        """The Mandatory Gate Precedence section must exist."""
        content = _read_file(_AGENT_INSTRUCTIONS)
        section = _extract_mandatory_gate_section(content)
        assert section, (
            "Mandatory Gate Precedence section not found in agent-instructions.md"
        )

    def test_section_prohibits_skipping(self) -> None:
        """Confirm the section DOES prohibit skipping (baseline behavior)."""
        content = _read_file(_AGENT_INSTRUCTIONS)
        section = _extract_mandatory_gate_section(content)
        assert re.search(r"NEVER\s+skip", section), (
            "Mandatory Gate Precedence section does not contain 'NEVER skip' — "
            "unexpected baseline state"
        )

    def test_section_has_skip_offer_prohibition(self) -> None:
        """The section contains language prohibiting skip OFFERS.

        After the fix, the section says "NEVER offer to skip a ⛔ mandatory
        gate step" in addition to "NEVER skip." This confirms the steering
        gap is closed.
        """
        content = _read_file(_AGENT_INSTRUCTIONS)
        section = _extract_mandatory_gate_section(content)

        assert _SKIP_OFFER_PROHIBITION_PATTERNS.search(section), (
            "Mandatory Gate Precedence section does NOT contain skip-offer "
            "prohibition language. The fix has not been applied. "
            f"Section content:\n{section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — conversation-protocol.md Self-Check lacks mandatory gate check
# ---------------------------------------------------------------------------


class TestConversationProtocolSelfCheck:
    """Test 2 — Self-Check section has only 4 items (no mandatory gate check).

    The Self-Check section validates question format but does NOT check whether
    a question offers to skip a ⛔ mandatory gate step.

    **Validates: Requirements 1.2**
    """

    def test_self_check_section_exists(self) -> None:
        """The Self-Check section must exist."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        section = _extract_self_check_section(content)
        assert section, (
            "Self-Check section not found in conversation-protocol.md"
        )

    def test_self_check_has_five_items(self) -> None:
        """The Self-Check section has 5 items (including mandatory gate check).

        After the fix, the Self-Check has 5 items:
        1. Multiple questions check
        2. Missing prefix check
        3. Content after question check
        4. Self-answering check
        5. Mandatory gate skip-offer check

        This confirms the fix has been applied.
        """
        content = _read_file(_CONVERSATION_PROTOCOL)
        section = _extract_self_check_section(content)
        item_count = _count_self_check_items(section)

        assert item_count == 5, (
            f"Self-Check section has {item_count} items, expected 5. "
            f"The fix should add item 5 (mandatory gate skip-offer check). "
            f"Section content:\n{section[:500]}"
        )

    def test_self_check_references_mandatory_gates(self) -> None:
        """The Self-Check section mentions mandatory gates or ⛔.

        After the fix, the Self-Check validates question content against
        mandatory gate steps — it references ⛔ and mandatory gates.
        """
        content = _read_file(_CONVERSATION_PROTOCOL)
        section = _extract_self_check_section(content)

        has_mandatory_gate_ref = bool(
            re.search(r"(mandatory\s+gate|⛔|skip.*mandatory|bypass.*mandatory)",
                      section, re.IGNORECASE)
        )
        assert has_mandatory_gate_ref, (
            "Self-Check section does NOT reference mandatory gates. "
            "The fix should add a check for mandatory gate skip offers. "
            f"Section content:\n{section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — module-03 lacks "proceed directly" instruction before Step 9
# ---------------------------------------------------------------------------


class TestModule03ProceedDirectlyInstruction:
    """Test 3 — No 'proceed directly' instruction before Step 9.

    module-03 marks Step 9 as ⛔ mandatory but does NOT explicitly instruct the
    agent to proceed directly without asking. The agent can still ask "Would you
    like to continue with the visualization?"

    After the module-03 dispatcher refactor, Step 9 + its ⛔ MANDATORY GATE marker
    live in ``module-03-phase2-visualization.md`` and the proceed-directly /
    agent-behavior instruction lives after Step 8 in
    ``module-03-phase1-verification.md``. These assertions are re-targeted to the
    shipped post-refactor locations.

    **Validates: Requirements 1.1, 1.3**
    """

    def test_step9_exists_with_mandatory_gate(self) -> None:
        """Step 9 exists and has the ⛔ MANDATORY GATE marker.

        In the shipped phase 2 file the marker is rendered with markdown
        emphasis (``> ⛔ **MANDATORY GATE — ...**``), so the regex tolerates
        optional blockquote/bold markup around the marker text.
        """
        content = _read_file(_MODULE3_PHASE2)
        assert re.search(r"#+\s+Step\s+9", content), (
            "Step 9 heading not found in module-03-phase2-visualization.md"
        )
        assert re.search(r"⛔\s*\*{0,2}\s*MANDATORY\s*GATE", content), (
            "⛔ MANDATORY GATE marker not found in module-03-phase2-visualization.md"
        )

    def test_proceed_directly_instruction_before_step9(self) -> None:
        """A 'proceed DIRECTLY to Step 9' instruction exists after Step 8.

        The instruction tells the agent to proceed directly to Step 9 after
        Step 8 completes. It lives in the Step 8 region of phase 1.
        """
        content = _read_file(_MODULE3_PHASE1)
        step8_region = _extract_step8_region(content)

        assert _PROCEED_DIRECTLY_PATTERN.search(step8_region), (
            "'proceed DIRECTLY to Step 9' instruction NOT found after Step 8 "
            "in module-03-phase1-verification.md. "
            f"Step 8 region content:\n{step8_region[:500]}"
        )

    def test_agent_behavior_instruction_before_step9(self) -> None:
        """An 'Agent behavior' instruction exists after Step 8.

        An '**Agent behavior:**' block sits after Step 8 instructing the agent
        to proceed without asking before Step 9 (which lives in phase 2).
        """
        content = _read_file(_MODULE3_PHASE1)
        step8_region = _extract_step8_region(content)

        has_agent_behavior = bool(
            re.search(r"\*\*Agent\s+behavior", step8_region, re.IGNORECASE)
        )
        assert has_agent_behavior, (
            "'**Agent behavior:**' instruction NOT found after Step 8 in "
            "module-03-phase1-verification.md. "
            f"Step 8 region content:\n{step8_region[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Property: Skip offers for ⛔ steps are unblocked
# ---------------------------------------------------------------------------


class TestBugConditionProperty:
    """PBT — Bug Condition: No steering rule prevents skip offers for ⛔ steps.

    For any agent question that references a ⛔ mandatory gate step and offers
    to skip or bypass it, the steering files contain NO prohibition preventing
    this question from being generated.

    On UNFIXED code, all assertions FAIL — confirming the steering gap exists
    and no rule prevents the agent from offering to skip ⛔ steps.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @given(question=st_skip_offer_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_no_steering_blocks_skip_offer_for_mandatory_gate(
        self, question: dict
    ) -> None:
        """For any skip-offer question targeting a ⛔ step, no steering blocks it.

        The bug condition is:
          X.type = "question"
          AND X.referencesStep.hasMandatoryGate = true
          AND X.offersSkipOrBypass = true

        On unfixed code, the steering files lack prohibition language for this
        pattern, so the agent can freely generate such questions.

        Args:
            question: A generated question satisfying the bug condition.
        """
        # Verify the generated input satisfies the bug condition
        assert question["type"] == "question"
        assert question["referencesStep"]["hasMandatoryGate"] is True
        assert question["offersSkipOrBypass"] is True

        # Check 1: agent-instructions.md must have skip-offer prohibition
        content = _read_file(_AGENT_INSTRUCTIONS)
        section = _extract_mandatory_gate_section(content)
        assert _SKIP_OFFER_PROHIBITION_PATTERNS.search(section), (
            f"Bug condition: agent can generate '{question['content']}' — "
            f"no skip-offer prohibition in Mandatory Gate Precedence section. "
            f"The section prohibits skipping but not OFFERING to skip."
        )

    @given(question=st_skip_offer_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_self_check_would_catch_skip_offer(self, question: dict) -> None:
        """For any skip-offer question targeting a ⛔ step, self-check catches it.

        The conversation-protocol.md Self-Check must include a check for
        mandatory gate skip offers. On unfixed code, it only has 4 items
        and none reference mandatory gates.

        Args:
            question: A generated question satisfying the bug condition.
        """
        content = _read_file(_CONVERSATION_PROTOCOL)
        section = _extract_self_check_section(content)
        item_count = _count_self_check_items(section)

        # The self-check must have more than 4 items (fix adds item 5)
        assert item_count > 4, (
            f"Bug condition: agent can generate '{question['content']}' — "
            f"Self-Check has only {item_count} items and none validate "
            f"question content against mandatory gate steps."
        )

    @given(question=st_skip_offer_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_module03_has_proceed_directly_instruction(
        self, question: dict
    ) -> None:
        """Module 03 must have a proceed-directly instruction before Step 9.

        On unfixed code, no such instruction exists — the agent is free to ask
        whether the bootcamper wants to continue with Step 9.

        Args:
            question: A generated question satisfying the bug condition.
        """
        content = _read_file(_MODULE3_PHASE1)
        step8_region = _extract_step8_region(content)

        assert _PROCEED_DIRECTLY_PATTERN.search(step8_region), (
            f"Bug condition: agent can generate '{question['content']}' — "
            f"no 'proceed DIRECTLY to Step 9' instruction exists after "
            f"Step 8 in module-03-phase1-verification.md."
        )
