"""Preservation property tests for no-skip-offer-mandatory-gate bugfix.

These tests verify baseline behavior that MUST be preserved after the fix:
non-mandatory step questions are unaffected, questions not referencing ⛔ steps
pass without interference, and the ask-bootcamper hook generates closing
questions normally.

Tests are written BEFORE the fix and MUST PASS on unfixed code — confirming
the behavior we want to preserve.

Feature: no-skip-offer-mandatory-gate

**Validates: Requirements 3.1, 3.2, 3.4**
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
_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"

_AGENT_INSTRUCTIONS = _STEERING_DIR / "agent-instructions.md"
_CONVERSATION_PROTOCOL = _STEERING_DIR / "conversation-protocol.md"
_MODULE3_STEERING = _STEERING_DIR / "module-03-system-verification.md"
_ASK_BOOTCAMPER_HOOK = _HOOKS_DIR / "ask-bootcamper.kiro.hook"

# ---------------------------------------------------------------------------
# Constants — Non-mandatory steps and question patterns
# ---------------------------------------------------------------------------

_NON_MANDATORY_STEPS = [
    "performance report",
    "optional cleanup",
    "bonus exercise",
    "extra examples",
    "Step 1",
    "Step 2",
    "Step 3",
    "Step 4",
    "Step 5",
    "Step 6",
    "Step 7",
    "Step 8",
    "Step 10",
    "Step 11",
    "Step 12",
]

_SKIP_OFFER_PHRASES = [
    "or skip ahead",
    "or move on to the next module",
    "would you like to skip",
    "or bypass",
    "or we can skip",
    "if you'd like to skip",
]

_GENERIC_QUESTION_TOPICS = [
    "your project",
    "the next step",
    "your progress",
    "the results",
    "your preferences",
    "the configuration",
    "your environment",
    "the output",
]

# Patterns that indicate the self-check would flag a question
_SELF_CHECK_VIOLATIONS = [
    re.compile(r"👉.*👉", re.DOTALL),  # Multiple questions
    # Missing prefix is checked by absence of 👉
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read a file's content."""
    return path.read_text(encoding="utf-8")


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


def _self_check_passes_for_question(question_content: str) -> bool:
    """Simulate the 4-item self-check from conversation-protocol.md.

    The self-check validates:
    1. Does this turn contain more than one 👉 question?
    2. Does any 👉 question lack the 👉 prefix?
    3. Is there content after a 👉 question?
    4. Am I answering my own question?

    Returns True if the question passes all checks (no violations).
    """
    # Check 1: More than one 👉 question
    question_marks_after_pointer = len(re.findall(r"👉[^👉]*\?", question_content))
    if question_marks_after_pointer > 1:
        return False

    # Check 2: Question lacks 👉 prefix (we ensure our generated questions have it)
    if "👉" not in question_content:
        return False

    # Check 3: Content after a 👉 question (simplified — no trailing content)
    # Our generated questions end with the question mark
    lines = question_content.strip().split("\n")
    question_line_found = False
    for line in lines:
        if "👉" in line and "?" in line:
            question_line_found = True
        elif question_line_found and line.strip():
            # Content after the question line
            return False

    # Check 4: Self-answering (our generated questions don't self-answer)
    # A self-answer would be an assertion/statement after the question
    # Our test questions are single-line, so this passes

    return True


def _question_references_mandatory_gate(question_content: str) -> bool:
    """Check if a question references a ⛔ mandatory gate step.

    On the current unfixed code, the only ⛔ mandatory gate step is Step 9
    (Web Service + Visualization) in Module 3.
    """
    mandatory_patterns = [
        r"Step\s*9",
        r"visualization",
        r"web\s+service",
        r"⛔",
        r"mandatory\s+gate",
    ]
    for pattern in mandatory_patterns:
        if re.search(pattern, question_content, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_non_mandatory_skip_question(draw: st.DrawFn) -> dict:
    """Generate a question offering to skip a NON-mandatory step.

    These questions are permitted behavior — skip offers for non-⛔ steps
    should always be allowed.

    Returns:
        A dict representing a permitted skip-offer question.
    """
    step = draw(st.sampled_from(_NON_MANDATORY_STEPS))
    skip_phrase = draw(st.sampled_from(_SKIP_OFFER_PHRASES))

    content = f"👉 Would you like to proceed with {step}, {skip_phrase}?"

    return {
        "type": "question",
        "referencesStep": {"name": step, "hasMandatoryGate": False},
        "offersSkipOrBypass": True,
        "initiator": "agent",
        "content": content,
    }


@st.composite
def st_generic_question_no_step_reference(draw: st.DrawFn) -> dict:
    """Generate a question that does NOT reference any step at all.

    These questions should never trigger any step-related validation.

    Returns:
        A dict representing a generic closing question.
    """
    topic = draw(st.sampled_from(_GENERIC_QUESTION_TOPICS))
    framing = draw(st.sampled_from([
        f"👉 Ready to look at {topic}?",
        f"👉 Would you like to review {topic}?",
        f"👉 Shall we move on to {topic}?",
        f"👉 How would you like to handle {topic}?",
    ]))

    return {
        "type": "question",
        "referencesStep": None,
        "offersSkipOrBypass": False,
        "initiator": "agent",
        "content": framing,
    }


@st.composite
def st_closing_question(draw: st.DrawFn) -> dict:
    """Generate a closing question like the ask-bootcamper hook would produce.

    The ask-bootcamper hook generates contextual closing questions when no
    question is pending. These should be unaffected by the fix.

    Returns:
        A dict representing a hook-generated closing question.
    """
    closing_patterns = [
        "👉 Ready to continue to the next step?",
        "👉 Would you like to see the results?",
        "👉 What would you like to do next?",
        "👉 Ready to move on?",
        "👉 Would you like me to explain what happened?",
        "👉 Shall we proceed?",
        "👉 Any questions before we continue?",
        "👉 Would you like to try a different approach?",
    ]
    content = draw(st.sampled_from(closing_patterns))

    return {
        "type": "question",
        "referencesStep": None,
        "offersSkipOrBypass": False,
        "initiator": "hook",
        "content": content,
    }


# ---------------------------------------------------------------------------
# Test Class 1 — Non-mandatory step skip offers are permitted
# ---------------------------------------------------------------------------


class TestNonMandatorySkipOffersPermitted:
    """Property: Skip offers for non-⛔ steps are always permitted.

    On UNFIXED code, the steering files have no rule that would block skip
    offers for non-mandatory steps. This behavior MUST be preserved after
    the fix — the fix should only block skip offers for ⛔ steps.

    **Validates: Requirements 3.1**
    """

    @given(question=st_non_mandatory_skip_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_mandatory_skip_offers_not_blocked_by_steering(
        self, question: dict
    ) -> None:
        """For any skip-offer about a non-⛔ step, no steering rule blocks it.

        The Mandatory Gate Precedence section only applies to ⛔ steps.
        Questions about non-mandatory steps should never be affected.
        """
        # Verify the question is about a non-mandatory step
        assert question["referencesStep"]["hasMandatoryGate"] is False

        # The Mandatory Gate Precedence section should not contain rules
        # that would block this question (it only mentions ⛔ steps)
        content = _read_file(_AGENT_INSTRUCTIONS)
        section = _extract_mandatory_gate_section(content)

        # The section mentions "NEVER skip a ⛔ mandatory gate step" — this
        # only applies to ⛔ steps, not to the non-mandatory step in our question
        assert "⛔" in section, (
            "Mandatory Gate Precedence section should reference ⛔ steps"
        )

        # Verify our question does NOT reference a mandatory gate step
        assert not _question_references_mandatory_gate(question["content"]), (
            f"Test invariant violated: generated question '{question['content']}' "
            f"unexpectedly references a mandatory gate step"
        )

    @given(question=st_non_mandatory_skip_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_mandatory_skip_offers_pass_self_check(
        self, question: dict
    ) -> None:
        """For any skip-offer about a non-⛔ step, the self-check passes.

        The current 4-item self-check validates question FORMAT (multiple
        questions, prefix, trailing content, self-answering) — it does NOT
        validate question CONTENT against mandatory gates. Skip offers for
        non-mandatory steps pass all 4 checks.
        """
        assert _self_check_passes_for_question(question["content"]), (
            f"Question '{question['content']}' should pass the self-check — "
            f"it has proper format (single question, 👉 prefix, no trailing "
            f"content, no self-answering)"
        )


# ---------------------------------------------------------------------------
# Test Class 2 — Questions not referencing any step are unaffected
# ---------------------------------------------------------------------------


class TestGenericQuestionsUnaffected:
    """Property: Questions not referencing any step pass without interference.

    On UNFIXED code, generic questions (not referencing any step) are
    completely unaffected by mandatory gate rules. This MUST remain true
    after the fix.

    **Validates: Requirements 3.2**
    """

    @given(question=st_generic_question_no_step_reference())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_generic_questions_not_blocked(self, question: dict) -> None:
        """For any question not referencing a step, no validation fires.

        Generic questions about progress, preferences, or next actions
        should never trigger any step-related validation.
        """
        # Verify the question doesn't reference any step
        assert question["referencesStep"] is None
        assert question["offersSkipOrBypass"] is False

        # Verify the question doesn't accidentally reference a mandatory gate
        assert not _question_references_mandatory_gate(question["content"]), (
            f"Test invariant violated: generic question '{question['content']}' "
            f"unexpectedly references a mandatory gate step"
        )

    @given(question=st_generic_question_no_step_reference())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_generic_questions_pass_self_check(self, question: dict) -> None:
        """For any generic question, the self-check passes.

        The 4-item self-check only validates format. Generic questions with
        proper format (single question, 👉 prefix) always pass.
        """
        assert _self_check_passes_for_question(question["content"]), (
            f"Question '{question['content']}' should pass the self-check"
        )


# ---------------------------------------------------------------------------
# Test Class 3 — ask-bootcamper hook closing questions are unaffected
# ---------------------------------------------------------------------------


class TestAskBootcamperHookPreserved:
    """Property: ask-bootcamper hook closing questions are unaffected.

    The ask-bootcamper hook generates contextual closing questions when no
    question is pending. These questions don't reference ⛔ steps and should
    be completely unaffected by the fix.

    **Validates: Requirements 3.4**
    """

    def test_ask_bootcamper_hook_exists(self) -> None:
        """The ask-bootcamper hook file must exist."""
        assert _ASK_BOOTCAMPER_HOOK.exists(), (
            f"ask-bootcamper.kiro.hook not found at {_ASK_BOOTCAMPER_HOOK}"
        )

    def test_ask_bootcamper_hook_generates_closing_questions(self) -> None:
        """The hook prompt instructs generation of closing questions.

        The hook's prompt contains instructions to generate a contextual
        closing question. This behavior must be preserved.
        """
        content = _read_file(_ASK_BOOTCAMPER_HOOK)

        # The hook should contain closing question generation instructions
        assert "closing question" in content.lower(), (
            "ask-bootcamper hook should contain 'closing question' instructions"
        )
        assert "👉" in content, (
            "ask-bootcamper hook should reference the 👉 question prefix"
        )

    @given(question=st_closing_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_closing_questions_pass_self_check(self, question: dict) -> None:
        """For any hook-generated closing question, the self-check passes.

        Closing questions generated by the ask-bootcamper hook have proper
        format and don't reference ⛔ steps. They should always pass the
        self-check.
        """
        assert _self_check_passes_for_question(question["content"]), (
            f"Closing question '{question['content']}' should pass the self-check"
        )

    @given(question=st_closing_question())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_closing_questions_dont_reference_mandatory_gates(
        self, question: dict
    ) -> None:
        """Hook-generated closing questions don't reference ⛔ steps.

        The ask-bootcamper hook generates generic closing questions about
        what to do next — they don't reference specific mandatory gate steps.
        """
        assert not _question_references_mandatory_gate(question["content"]), (
            f"Closing question '{question['content']}' should not reference "
            f"a mandatory gate step"
        )


# ---------------------------------------------------------------------------
# Test Class 4 — Self-check structure is preserved
# ---------------------------------------------------------------------------


class TestSelfCheckStructurePreserved:
    """Property: The existing self-check items continue to function.

    The current 4-item self-check validates question format. After the fix
    adds a 5th item, the original 4 items must still be present and functional.
    This test verifies the baseline structure.

    **Validates: Requirements 3.2**
    """

    def test_self_check_has_format_validation_items(self) -> None:
        """The Self-Check section contains format validation items.

        The 4 existing items check:
        1. Multiple questions
        2. Missing prefix
        3. Content after question
        4. Self-answering

        These must remain present after the fix.
        """
        content = _read_file(_CONVERSATION_PROTOCOL)
        section = _extract_self_check_section(content)

        # Verify the 4 core format checks are present
        assert re.search(r"more than one.*question", section, re.IGNORECASE), (
            "Self-Check should contain 'more than one question' check"
        )
        assert re.search(r"lack.*👉.*prefix|👉.*prefix", section, re.IGNORECASE), (
            "Self-Check should contain prefix check"
        )
        assert re.search(r"content after.*question", section, re.IGNORECASE), (
            "Self-Check should contain 'content after question' check"
        )
        assert re.search(r"answering.*own.*question|answer.*my.*question",
                         section, re.IGNORECASE), (
            "Self-Check should contain self-answering check"
        )

    def test_self_check_has_revision_instruction(self) -> None:
        """The Self-Check section instructs revision when violations found."""
        content = _read_file(_CONVERSATION_PROTOCOL)
        section = _extract_self_check_section(content)

        assert re.search(r"(revise|rewrite|fix)", section, re.IGNORECASE), (
            "Self-Check should instruct revision when violations are found"
        )
