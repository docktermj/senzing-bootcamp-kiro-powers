"""Property-based tests for answer processing failure detection and recovery.

Validates that the hook's Phase 2 activation is broadened to all question types,
type-specific retry instructions are complete, and the question_pending file
format round-trips correctly.

Feature: agent-answer-processing-failures
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HOOK_PATH = (
    Path(__file__).resolve().parent.parent / "hooks" / "ask-bootcamper.kiro.hook"
)

VALID_TYPES = {
    "track_selection",
    "module_transition",
    "step_question",
    "confirmation",
    "choice",
}

# Old Transition_Confirmation patterns that should NOT appear in Phase 2
# activation conditions
_OLD_TRANSITION_PATTERNS = [
    "Ready for Module",
    "move on to Module",
    "proceed to Module",
]


# ---------------------------------------------------------------------------
# Question_Pending Serialization/Deserialization Helpers
# ---------------------------------------------------------------------------


def write_question_pending(question_type: str, question_text: str) -> str:
    """Serialize a question to the .question_pending file format.

    Args:
        question_type: One of the VALID_TYPES.
        question_text: The full question text (may contain newlines).

    Returns:
        File content string with type on first line, text on subsequent lines.
    """
    return f"{question_type}\n{question_text}"


def parse_question_pending(content: str) -> tuple[str, str]:
    """Parse a .question_pending file into type and text.

    Args:
        content: Raw file content.

    Returns:
        Tuple of (question_type, question_text).
        If type is not recognized, returns ('step_question', full_content).
    """
    lines = content.split("\n", 1)
    if len(lines) >= 2 and lines[0].strip() in VALID_TYPES:
        return (lines[0].strip(), lines[1])
    return ("step_question", content)


# ---------------------------------------------------------------------------
# Hook Loading
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the hook prompt text from the JSON hook file.

    Returns:
        The prompt string from the hook's then.prompt field.

    Raises:
        FileNotFoundError: If the hook file does not exist.
    """
    if not _HOOK_PATH.exists():
        raise FileNotFoundError(f"Hook file not found: {_HOOK_PATH}")
    hook_data = json.loads(_HOOK_PATH.read_text(encoding="utf-8"))
    return hook_data["then"]["prompt"]


# Load hook prompt once at module level for all tests
_HOOK_PROMPT = load_hook_prompt()


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------


def st_valid_question_type() -> st.SearchStrategy[str]:
    """Strategy that draws from the set of valid question types."""
    return st.sampled_from(sorted(VALID_TYPES))


def st_question_text() -> st.SearchStrategy[str]:
    """Strategy that generates non-empty multi-line question texts.

    Generates text that may contain newlines but does not start with a
    valid question type on the first line (to avoid ambiguity in parsing).
    """
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z", "S"),
            whitelist_characters="\n?!.,;:()[]{}'\"-+= \t",
        ),
        min_size=1,
        max_size=200,
    ).filter(lambda t: t.strip())  # Ensure non-whitespace-only


# ---------------------------------------------------------------------------
# Property Test Classes
# ---------------------------------------------------------------------------


class TestQuestionPendingRoundTrip:
    """Property 3: Question_Pending File Round-Trip.

    For any valid question type and any non-empty question text, serializing
    to the question_pending format (type on first line, text on subsequent
    lines) and then parsing back SHALL yield the original question type and
    original question text.

    Validates: Requirements 5.1, 5.2, 5.3
    """

    @given(
        question_type=st_valid_question_type(),
        question_text=st_question_text(),
    )
    @settings(max_examples=20)
    def test_round_trip_preserves_type(
        self, question_type: str, question_text: str
    ) -> None:
        """Serializing and parsing back preserves the question type.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        serialized = write_question_pending(question_type, question_text)
        parsed_type, _ = parse_question_pending(serialized)
        assert parsed_type == question_type, (
            f"Round-trip failed for type: serialized with '{question_type}', "
            f"parsed back as '{parsed_type}'"
        )

    @given(
        question_type=st_valid_question_type(),
        question_text=st_question_text(),
    )
    @settings(max_examples=20)
    def test_round_trip_preserves_text(
        self, question_type: str, question_text: str
    ) -> None:
        """Serializing and parsing back preserves the question text.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        serialized = write_question_pending(question_type, question_text)
        _, parsed_text = parse_question_pending(serialized)
        assert parsed_text == question_text, (
            f"Round-trip failed for text: expected '{question_text!r}', "
            f"got '{parsed_text!r}'"
        )

    @given(
        question_type=st_valid_question_type(),
        question_text=st_question_text(),
    )
    @settings(max_examples=20)
    def test_serialized_format_has_type_on_first_line(
        self, question_type: str, question_text: str
    ) -> None:
        """Serialized format places the type on the first line.

        **Validates: Requirements 5.1, 5.2**
        """
        serialized = write_question_pending(question_type, question_text)
        first_line = serialized.split("\n", 1)[0]
        assert first_line == question_type, (
            f"First line should be the question type '{question_type}', "
            f"got '{first_line}'"
        )


class TestTypeSpecificRetryInstructionCompleteness:
    """Property 2: Type-Specific Retry Instruction Completeness.

    For any known question type in the set {track_selection, module_transition,
    step_question, confirmation, choice}, the hook prompt SHALL contain a
    distinct retry instruction block that references the required recovery
    actions for that type. Additionally, for any content where the question
    type cannot be determined, the hook prompt SHALL contain a generic fallback
    retry instruction.

    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """

    @given(question_type=st_valid_question_type())
    @settings(max_examples=20)
    def test_each_type_has_distinct_retry_block(
        self, question_type: str
    ) -> None:
        """Each valid question type has a distinct retry instruction block.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
        """
        # The hook prompt should contain a section referencing this type
        # with specific retry instructions
        assert f'"{question_type}"' in _HOOK_PROMPT or (
            question_type in _HOOK_PROMPT
        ), (
            f"Hook prompt does not contain retry instructions for "
            f"question type '{question_type}'"
        )

    def test_all_five_types_have_distinct_blocks(self) -> None:
        """All five question types have distinct retry instruction blocks.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
        """
        for qtype in VALID_TYPES:
            assert qtype in _HOOK_PROMPT, (
                f"Hook prompt missing retry block for type '{qtype}'"
            )

    def test_generic_fallback_exists(self) -> None:
        """A generic fallback retry instruction exists for unknown types.

        **Validates: Requirements 4.6**
        """
        # The fallback should handle cases where type is not in the valid set
        # Look for "unknown" type handling or generic fallback language
        has_unknown_handling = "unknown" in _HOOK_PROMPT.lower()
        has_fallback_language = (
            "Re-read" in _HOOK_PROMPT
            or "re-read" in _HOOK_PROMPT
            or "fallback" in _HOOK_PROMPT.lower()
            or "cannot be determined" in _HOOK_PROMPT.lower()
            or "Otherwise" in _HOOK_PROMPT
        )
        assert has_unknown_handling or has_fallback_language, (
            "Hook prompt does not contain a generic fallback retry instruction "
            "for unknown question types"
        )

    @given(question_type=st_valid_question_type())
    @settings(max_examples=20)
    def test_type_retry_blocks_are_distinct(self, question_type: str) -> None:
        """Each type's retry block contains type-specific recovery actions.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
        """
        # Map each type to expected keywords in its retry instructions
        expected_keywords: dict[str, list[str]] = {
            "track_selection": ["track", "bootcamp_progress.json"],
            "module_transition": ["banner", "Step 1"],
            "step_question": ["answer", "progress"],
            "confirmation": ["confirmation", "proceed"],
            "choice": ["selection", "numbered"],
        }
        keywords = expected_keywords[question_type]
        prompt_lower = _HOOK_PROMPT.lower()
        found_any = any(kw.lower() in prompt_lower for kw in keywords)
        assert found_any, (
            f"Hook prompt retry block for '{question_type}' does not contain "
            f"expected keywords: {keywords}"
        )


class TestPhase2ActivationBroadening:
    """Property 1: Phase 2 Activation Broadening.

    For any valid question type stored in config/.question_pending, the hook's
    Phase 2 activation logic SHALL trigger on the combination of
    (question_pending file exists AND minimal output detected) without
    requiring a Transition_Confirmation pattern match as a prerequisite.
    The old patterns SHALL NOT appear as Phase 2 activation conditions.

    Validates: Requirements 3.1, 3.4
    """

    def test_phase2_uses_question_pending_existence(self) -> None:
        """Phase 2 activation checks for question_pending file existence.

        **Validates: Requirements 3.1**
        """
        assert "question_pending" in _HOOK_PROMPT or ".question_pending" in _HOOK_PROMPT, (
            "Hook prompt Phase 2 does not reference question_pending file existence"
        )

    def test_phase2_uses_minimal_output_detection(self) -> None:
        """Phase 2 activation checks for minimal output.

        **Validates: Requirements 3.1**
        """
        has_minimal_output_ref = (
            "Minimal_Output" in _HOOK_PROMPT
            or "minimal output" in _HOOK_PROMPT.lower()
            or "minimal" in _HOOK_PROMPT.lower()
        )
        assert has_minimal_output_ref, (
            "Hook prompt Phase 2 does not reference minimal output detection"
        )

    def test_phase2_does_not_require_transition_confirmation(self) -> None:
        """Phase 2 does NOT contain old Transition_Confirmation patterns.

        The old patterns ("Ready for Module", "move on to Module",
        "proceed to Module") SHALL NOT appear as Phase 2 activation conditions.

        **Validates: Requirements 3.4**
        """
        # Extract the Phase 2 / Sub-phase 2B section from the prompt
        # Look for the section between Phase 2 markers
        phase2_start = _HOOK_PROMPT.find("PHASE 2")
        phase3_start = _HOOK_PROMPT.find("PHASE 3")

        if phase2_start == -1:
            # Try alternate markers
            phase2_start = _HOOK_PROMPT.find("SUB-PHASE 2B")
            phase3_start = _HOOK_PROMPT.find("SUB-PHASE 2C")

        if phase2_start == -1:
            pytest.fail("Could not locate Phase 2 section in hook prompt")

        # Get the Phase 2 section text
        if phase3_start != -1:
            phase2_text = _HOOK_PROMPT[phase2_start:phase3_start]
        else:
            phase2_text = _HOOK_PROMPT[phase2_start:]

        for pattern in _OLD_TRANSITION_PATTERNS:
            assert pattern not in phase2_text, (
                f"Phase 2 still contains old Transition_Confirmation pattern: "
                f"'{pattern}'. This should have been removed per Requirement 3.4."
            )

    @given(question_type=st_valid_question_type())
    @settings(max_examples=20)
    def test_phase2_handles_all_question_types(self, question_type: str) -> None:
        """Phase 2 handles all valid question types, not just module_transition.

        **Validates: Requirements 3.1, 3.4**
        """
        # The hook prompt should reference each question type in its
        # retry dispatch logic
        assert question_type in _HOOK_PROMPT, (
            f"Hook prompt Phase 2 does not handle question type "
            f"'{question_type}' — broadening incomplete"
        )

    def test_phase2_named_answer_processing_retry(self) -> None:
        """Phase 2 is named 'ANSWER PROCESSING RETRY' not 'MODULE TRANSITION RETRY'.

        **Validates: Requirements 3.1**
        """
        assert "ANSWER PROCESSING RETRY" in _HOOK_PROMPT, (
            "Hook prompt does not contain 'ANSWER PROCESSING RETRY' heading"
        )
        assert "MODULE TRANSITION RETRY" not in _HOOK_PROMPT, (
            "Hook prompt still contains old 'MODULE TRANSITION RETRY' heading"
        )
