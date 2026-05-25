"""Tests for answer-processing hook prompt validation.

Validates that the ask-bootcamper.kiro.hook contains the correct Phase 2
(ANSWER PROCESSING RETRY) structure with type-specific retry instructions,
not-waiting detection logic (Sub-phase 2C), and does NOT contain old
Transition_Confirmation prerequisite patterns.

**Validates: Requirements 3.3, 3.4, 4.1-4.6, 6.1, 6.2**
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hook_test_helpers import load_hook

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.kiro.hook")

# The five known question types
QUESTION_TYPES: list[str] = [
    "track_selection",
    "module_transition",
    "step_question",
    "confirmation",
    "choice",
]

# Keywords that MUST appear in the hook prompt for each question type's
# retry instruction block.
TYPE_SPECIFIC_KEYWORDS: dict[str, list[str]] = {
    "track_selection": [
        "bootcamp_progress.json",
        "bootcamp_preferences.yaml",
        "Module 1",
    ],
    "module_transition": [
        "module start banner",
        "journey map",
        "before/after",
        "Step 1",
    ],
    "step_question": [
        "answer",
        "workflow",
        "progress",
        "next action",
    ],
    "confirmation": [
        "confirmation",
        "proceed",
    ],
    "choice": [
        "numbered",
        "selection",
        "selected option",
    ],
}

# Keywords for the unknown/fallback retry instruction block
FALLBACK_KEYWORDS: list[str] = [
    "Re-read",
    "substantive response",
]

# Old patterns that should NOT be present as Phase 2B activation prerequisites
OLD_TRANSITION_PATTERNS: list[str] = [
    "Ready for Module",
    "move on to Module",
    "proceed to Module",
]

# Affirmative phrases that were used in old transition confirmation matching
OLD_AFFIRMATIVE_PHRASES: list[str] = [
    '"yes"',
    '"sure"',
    '"ready"',
    '"let\'s go"',
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the then.prompt field from the hook."""
    data = load_hook(HOOK_PATH)
    return data["then"]["prompt"]


# ---------------------------------------------------------------------------
# Test Class 1: Phase 2 Naming
# ---------------------------------------------------------------------------


class TestPhase2Naming:
    """Verify Phase 2 is named "ANSWER PROCESSING RETRY" not "MODULE TRANSITION RETRY".

    **Validates: Requirements 3.3**
    """

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_answer_processing_retry_present(self, data: None) -> None:
        """The hook prompt SHALL contain 'ANSWER PROCESSING RETRY'."""
        prompt = load_hook_prompt()
        assert "ANSWER PROCESSING RETRY" in prompt, (
            "Hook prompt does not contain 'ANSWER PROCESSING RETRY' — "
            "Phase 2 has not been renamed from the old module-transition-only scope"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_module_transition_retry_absent(self, data: None) -> None:
        """The hook prompt SHALL NOT contain 'MODULE TRANSITION RETRY'."""
        prompt = load_hook_prompt()
        assert "MODULE TRANSITION RETRY" not in prompt, (
            "Hook prompt still contains 'MODULE TRANSITION RETRY' — "
            "Phase 2 should be renamed to 'ANSWER PROCESSING RETRY'"
        )


# ---------------------------------------------------------------------------
# Test Class 2: Type-Specific Retry Instructions
# ---------------------------------------------------------------------------


class TestTypeSpecificRetryInstructions:
    """Verify the hook prompt contains type-specific retry instruction blocks.

    For each of the 5 question types plus the unknown/fallback, the hook prompt
    must contain the required keywords indicating the correct recovery actions.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    """

    @given(question_type=st.sampled_from(QUESTION_TYPES))
    @settings(max_examples=20)
    def test_type_specific_keywords_present(self, question_type: str) -> None:
        """For any known question type, the hook prompt SHALL contain all
        required keywords for that type's retry instruction block."""
        prompt = load_hook_prompt()
        keywords = TYPE_SPECIFIC_KEYWORDS[question_type]
        for keyword in keywords:
            assert keyword in prompt, (
                f"Hook prompt missing keyword '{keyword}' for question type "
                f"'{question_type}' retry instructions"
            )

    @given(question_type=st.sampled_from(QUESTION_TYPES))
    @settings(max_examples=20)
    def test_type_name_appears_in_prompt(self, question_type: str) -> None:
        """For any known question type, the type name itself SHALL appear
        in the hook prompt as part of the dispatch logic."""
        prompt = load_hook_prompt()
        assert question_type in prompt, (
            f"Hook prompt does not reference question type '{question_type}' — "
            f"type-specific dispatch is incomplete"
        )

    @given(keyword=st.sampled_from(FALLBACK_KEYWORDS))
    @settings(max_examples=20)
    def test_fallback_keywords_present(self, keyword: str) -> None:
        """The hook prompt SHALL contain fallback/unknown retry instruction
        keywords for when the question type cannot be determined."""
        prompt = load_hook_prompt()
        assert keyword in prompt, (
            f"Hook prompt missing fallback keyword '{keyword}' — "
            f"generic retry instructions for unknown type are incomplete"
        )


# ---------------------------------------------------------------------------
# Test Class 3: Not-Waiting Detection
# ---------------------------------------------------------------------------


class TestNotWaitingDetection:
    """Verify the hook prompt contains not-waiting violation detection logic.

    Sub-phase 2C activation conditions and recovery instructions must be present.

    **Validates: Requirements 6.1, 6.2**
    """

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_not_waiting_violation_marker_present(self, data: None) -> None:
        """The hook prompt SHALL contain 'NOT-WAITING' violation detection."""
        prompt = load_hook_prompt()
        assert "NOT-WAITING" in prompt, (
            "Hook prompt does not contain 'NOT-WAITING' violation detection — "
            "Sub-phase 2C is missing"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_not_waiting_detection_label(self, data: None) -> None:
        """The hook prompt SHALL contain 'NOT-WAITING DETECTION' as a sub-phase."""
        prompt = load_hook_prompt()
        assert "NOT-WAITING DETECTION" in prompt, (
            "Hook prompt does not contain 'NOT-WAITING DETECTION' sub-phase label"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_not_waiting_activation_checks_question_pending(self, data: None) -> None:
        """The not-waiting detection SHALL check that .question_pending exists."""
        prompt = load_hook_prompt()
        # The prompt must reference .question_pending in the context of 2C
        assert ".question_pending" in prompt, (
            "Hook prompt does not reference '.question_pending' file — "
            "not-waiting detection cannot check for pending questions"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_not_waiting_checks_workflow_advancing_content(self, data: None) -> None:
        """The not-waiting detection SHALL check for workflow-advancing content."""
        prompt = load_hook_prompt()
        assert "workflow-advancing" in prompt.lower() or "workflow-advancing" in prompt, (
            "Hook prompt does not reference 'workflow-advancing' content detection — "
            "not-waiting detection cannot identify premature output"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_not_waiting_recovery_discard_instruction(self, data: None) -> None:
        """The not-waiting recovery SHALL instruct to discard premature output."""
        prompt = load_hook_prompt()
        prompt_lower = prompt.lower()
        assert "discard" in prompt_lower, (
            "Hook prompt does not contain 'discard' instruction — "
            "not-waiting recovery is incomplete"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_not_waiting_recovery_wait_instruction(self, data: None) -> None:
        """The not-waiting recovery SHALL instruct to wait for bootcamper response."""
        prompt = load_hook_prompt()
        prompt_lower = prompt.lower()
        assert "wait" in prompt_lower, (
            "Hook prompt does not contain 'wait' instruction — "
            "not-waiting recovery is incomplete"
        )


# ---------------------------------------------------------------------------
# Test Class 4: Old Patterns Removed
# ---------------------------------------------------------------------------


def _extract_phase_2b_section(prompt: str) -> str:
    """Extract the Sub-phase 2B section from the hook prompt.

    Returns the text between 'SUB-PHASE 2B' and the next 'SUB-PHASE' or
    'PHASE' marker, which is the answer processing retry section.
    """
    import re
    # Find the start of Sub-phase 2B
    match_start = re.search(r"SUB-PHASE 2B", prompt)
    if not match_start:
        return ""
    start_idx = match_start.start()

    # Find the end — next SUB-PHASE or PHASE marker after 2B
    rest = prompt[match_start.end():]
    match_end = re.search(r"(SUB-PHASE 2C|PHASE \d|════)", rest)
    if match_end:
        end_idx = match_start.end() + match_end.start()
    else:
        end_idx = len(prompt)

    return prompt[start_idx:end_idx]


class TestOldPatternsRemoved:
    """Verify the hook prompt does NOT contain old Transition_Confirmation patterns.

    The old Phase 2 required detecting "Ready for Module" / "move on to Module" /
    "proceed to Module" patterns plus affirmative response matching as prerequisites
    for Phase 2B activation. These should no longer be present in the Phase 2B
    section as activation prerequisites.

    **Validates: Requirements 3.4**
    """

    @given(pattern=st.sampled_from(OLD_TRANSITION_PATTERNS))
    @settings(max_examples=20)
    def test_old_transition_detection_patterns_absent_from_phase_2b(
        self, pattern: str
    ) -> None:
        """The Phase 2B section SHALL NOT contain old transition detection
        patterns as activation prerequisites."""
        prompt = load_hook_prompt()
        phase_2b = _extract_phase_2b_section(prompt)
        assert phase_2b, (
            "Could not extract Phase 2B section from hook prompt"
        )
        assert pattern not in phase_2b, (
            f"Phase 2B section still contains old transition detection pattern "
            f"'{pattern}' — Phase 2B should use question_pending existence "
            f"check instead of pattern matching"
        )

    @given(phrase=st.sampled_from(OLD_AFFIRMATIVE_PHRASES))
    @settings(max_examples=20)
    def test_old_affirmative_phrase_lists_absent(self, phrase: str) -> None:
        """The hook prompt SHALL NOT contain lists of affirmative phrases
        used for old transition confirmation matching."""
        prompt = load_hook_prompt()
        phase_2b = _extract_phase_2b_section(prompt)
        assert phase_2b, (
            "Could not extract Phase 2B section from hook prompt"
        )
        assert phrase not in phase_2b, (
            f"Phase 2B section still contains old affirmative phrase {phrase} — "
            f"transition confirmation matching should be removed"
        )


# ---------------------------------------------------------------------------
# Minimal_Output Classification Logic
# ---------------------------------------------------------------------------

# Single-word acknowledgments that count as minimal output
SINGLE_WORD_ACKS: set[str] = {
    "ok", "sure", "got it", "understood", "great",
    "yes", "no", "thanks", "done", "right",
}


def is_minimal_output(text: str) -> bool:
    """Determine if agent output qualifies as Minimal_Output.

    Output is Minimal_Output if ANY of these are true:
    - Output is exactly "."
    - Output is empty or whitespace-only
    - Output length is fewer than 50 characters
    - Output is a single-word acknowledgment (e.g., "OK", "Sure", "Got it",
      "Understood", "Great")

    Args:
        text: The agent output string to classify.

    Returns:
        True if the output is minimal, False otherwise.
    """
    # Empty or whitespace-only
    if not text or text.strip() == "":
        return True
    # Exactly "."
    if text == ".":
        return True
    # Fewer than 50 characters
    if len(text) < 50:
        return True
    # Single-word acknowledgment (case-insensitive)
    if text.strip().lower() in SINGLE_WORD_ACKS:
        return True
    return False


# ---------------------------------------------------------------------------
# Test Class 5: Minimal_Output Classification
# ---------------------------------------------------------------------------


class TestMinimalOutputClassification:
    """Verify the Minimal_Output detection logic correctly classifies strings.

    Output is Minimal_Output if ANY of these are true:
    - Output is exactly "."
    - Output is empty or whitespace-only
    - Output length is fewer than 50 characters
    - Output is a single-word acknowledgment

    **Validates: Requirements 3.1**
    """

    @given(text=st.text(alphabet=" \t\n\r", min_size=0, max_size=100))
    @settings(max_examples=20)
    def test_empty_or_whitespace_only_is_minimal(self, text: str) -> None:
        """Any empty or whitespace-only string SHALL be classified as minimal."""
        assert is_minimal_output(text) is True, (
            f"Whitespace-only string {text!r} was not classified as minimal"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_dot_is_minimal(self, data: None) -> None:
        """The string '.' SHALL be classified as minimal."""
        assert is_minimal_output(".") is True, (
            "The string '.' was not classified as minimal"
        )

    @given(text=st.text(min_size=1, max_size=49))
    @settings(max_examples=20)
    def test_short_strings_are_minimal(self, text: str) -> None:
        """Any string shorter than 50 characters SHALL be classified as minimal."""
        assert is_minimal_output(text) is True, (
            f"String of length {len(text)} was not classified as minimal "
            f"(must be minimal when < 50 chars)"
        )

    @given(ack=st.sampled_from(sorted(SINGLE_WORD_ACKS)))
    @settings(max_examples=20)
    def test_known_acknowledgments_are_minimal(self, ack: str) -> None:
        """Known single-word acknowledgments SHALL be classified as minimal
        regardless of case or surrounding whitespace."""
        # Test as-is
        assert is_minimal_output(ack) is True, (
            f"Acknowledgment {ack!r} was not classified as minimal"
        )
        # Test uppercase
        assert is_minimal_output(ack.upper()) is True, (
            f"Uppercase acknowledgment {ack.upper()!r} was not classified as minimal"
        )
        # Test with surrounding whitespace (padded to 50+ chars to isolate ack logic)
        padded = " " * 50 + ack + " " * 50
        assert is_minimal_output(padded) is True, (
            f"Padded acknowledgment {padded!r} was not classified as minimal"
        )

    @given(
        text=st.text(
            alphabet=st.characters(blacklist_categories=("Cs",)),
            min_size=50,
            max_size=200,
        ).filter(
            lambda s: s.strip() != ""
            and s != "."
            and s.strip().lower() not in SINGLE_WORD_ACKS
            and " " in s.strip()
        )
    )
    @settings(max_examples=20)
    def test_long_multiword_non_ack_is_not_minimal(self, text: str) -> None:
        """A string that is 50+ characters, multi-word, not '.', and not
        whitespace-only is NOT minimal (unless it happens to be a single-word
        acknowledgment, which is filtered out)."""
        assert is_minimal_output(text) is False, (
            f"String of length {len(text)} with multiple words was incorrectly "
            f"classified as minimal: {text!r}"
        )
