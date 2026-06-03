"""Property-based tests for detect-transition-retry hook logic.

Validates the core detection logic used by the detect-transition-retry agentStop hook:
- Minimal output classification (is_minimal_output)
- Transition confirmation recognition (is_transition_confirmation)
- Hook decision logic (hook_decision)
- Hook file schema validity

Requirements validated: 1.2, 1.3, 2.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.2, 5.4, 5.5
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants — mirror the hook prompt's detection logic
# ---------------------------------------------------------------------------

TRANSITION_QUESTION_PATTERNS: list[str] = [
    "Ready for Module",
    "move on to Module",
    "proceed to Module",
]

AFFIRMATIVE_PHRASES: list[str] = [
    "yes", "sure", "ready", "let's go", "let's do it",
    "yep", "yeah", "absolutely", "go ahead", "proceed",
    "ok", "okay", "sounds good", "let's", "do it",
    "I'm ready", "go for it",
]

MINIMAL_OUTPUT_THRESHOLD: int = 50  # characters

SINGLE_WORD_ACKS: set[str] = {
    "ok", "okay", "sure", "got it", "understood", "great", "thanks",
}

# ---------------------------------------------------------------------------
# Helper functions — pure-Python implementations of the hook's detection logic
# ---------------------------------------------------------------------------


def is_minimal_output(output: str) -> bool:
    """Classify agent output as minimal (violation) or substantive (acceptable).

    Args:
        output: The agent's response text.

    Returns:
        True if the output is minimal (a violation), False if substantive.
    """
    stripped = output.strip()
    if stripped == ".":
        return True
    if stripped == "":
        return True
    if len(stripped) < MINIMAL_OUTPUT_THRESHOLD:
        return True
    # Single-word acknowledgments
    if stripped.lower() in SINGLE_WORD_ACKS:
        return True
    return False


def is_transition_confirmation(message: str, prior_assistant_message: str) -> bool:
    """Detect if a message is an affirmative response to a module transition question.

    Args:
        message: The bootcamper's most recent message.
        prior_assistant_message: The agent's prior message (checked for transition
            question patterns).

    Returns:
        True if the message is an affirmative response to a transition question.
    """
    # Check if prior assistant message contained a transition question
    has_transition_question = any(
        pattern.lower() in prior_assistant_message.lower()
        for pattern in TRANSITION_QUESTION_PATTERNS
    )
    if not has_transition_question:
        return False

    # Check if the bootcamper's message is affirmative
    message_lower = message.lower().strip()
    return any(
        phrase in message_lower
        for phrase in AFFIRMATIVE_PHRASES
    )


def hook_decision(is_confirmation: bool, is_minimal: bool) -> str:
    """Determine hook output based on confirmation and minimal output status.

    Args:
        is_confirmation: Whether the bootcamper's message is a transition confirmation.
        is_minimal: Whether the agent's output is minimal.

    Returns:
        "retry" if both conditions are True (retry instructions should be issued),
        "." otherwise (pass-through, no action needed).
    """
    if is_confirmation and is_minimal:
        return "retry"
    return "."


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestMinimalOutputClassification:
    """Property tests for is_minimal_output classification correctness.

    **Validates: Requirements 1.2, 1.3, 2.1**

    Property 1: Minimal Output Classification Correctness
    For any string, is_minimal_output returns True iff the string is empty,
    whitespace-only, exactly ".", a single-word acknowledgment, or fewer than
    50 characters; and returns False for strings >= 50 chars that are not
    single-word acknowledgments.
    """

    @given(st.text(min_size=0, max_size=49))
    @settings(max_examples=20)
    def test_short_strings_are_minimal(self, output: str) -> None:
        """Strings shorter than 50 characters (after strip) are always minimal."""
        assert is_minimal_output(output) is True

    @given(st.text(min_size=50, max_size=200, alphabet=st.characters(blacklist_categories=("Cs",))))
    @settings(max_examples=20)
    def test_long_strings_not_in_acks_are_not_minimal(self, output: str) -> None:
        """Strings >= 50 chars that are not single-word acks are substantive."""
        # Only test strings whose stripped form is still >= 50 chars
        # and not in SINGLE_WORD_ACKS
        stripped = output.strip()
        if len(stripped) >= MINIMAL_OUTPUT_THRESHOLD and stripped.lower() not in SINGLE_WORD_ACKS:
            assert is_minimal_output(output) is False

    @given(st.sampled_from(["", " ", "  ", "\t", "\n", "  \n\t  "]))
    @settings(max_examples=20)
    def test_whitespace_only_is_minimal(self, output: str) -> None:
        """Empty and whitespace-only strings are always minimal."""
        assert is_minimal_output(output) is True

    @given(st.sampled_from(sorted(SINGLE_WORD_ACKS)))
    @settings(max_examples=20)
    def test_single_word_acks_are_minimal(self, output: str) -> None:
        """Single-word acknowledgments are always minimal regardless of length."""
        assert is_minimal_output(output) is True

    @given(st.just("."))
    @settings(max_examples=20)
    def test_period_is_minimal(self, output: str) -> None:
        """A single period is always minimal."""
        assert is_minimal_output(output) is True

    @given(
        st.text(
            min_size=50,
            max_size=300,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "S", "Z"),
                blacklist_categories=("Cs",),
            ),
        )
    )
    @settings(max_examples=20)
    def test_boundary_at_50_chars(self, output: str) -> None:
        """Strings at or above 50 chars boundary are not minimal (unless ack)."""
        stripped = output.strip()
        if len(stripped) >= MINIMAL_OUTPUT_THRESHOLD:
            if stripped.lower() in SINGLE_WORD_ACKS:
                assert is_minimal_output(output) is True
            else:
                assert is_minimal_output(output) is False


# ---------------------------------------------------------------------------
# Property 4: Hook File Schema Validity
# ---------------------------------------------------------------------------

# Path to the hook file relative to the test file location
_HOOK_FILE: Path = (
    Path(__file__).resolve().parent.parent
    / "senzing-bootcamp"
    / "hooks"
    / "ask-bootcamper.kiro.hook"
)


class TestHookFileSchemaValidity:
    """Validate the detect-transition-retry hook file schema.

    Parses the hook file as JSON and verifies structural requirements:
    - All required top-level fields exist
    - when.type is "agentStop"
    - then.type is "askAgent"
    - name follows the "to " prefix convention

    **Validates: Requirements 5.2, 5.4, 5.5**
    """

    def _load_hook(self) -> dict:
        """Load and parse the hook file as JSON.

        Returns:
            Parsed hook file content as a dictionary.
        """
        assert _HOOK_FILE.exists(), f"Hook file not found: {_HOOK_FILE}"
        return json.loads(_HOOK_FILE.read_text(encoding="utf-8"))

    def test_hook_file_is_valid_json(self) -> None:
        """Hook file must parse as valid JSON without errors."""
        hook = self._load_hook()
        assert isinstance(hook, dict)

    def test_required_fields_exist(self) -> None:
        """Hook file must contain all required top-level fields."""
        hook = self._load_hook()
        required_fields = {"name", "version", "description", "when", "then"}
        missing = required_fields - set(hook.keys())
        assert not missing, f"Missing required fields: {missing}"

    def test_when_type_is_agent_stop(self) -> None:
        """when.type must be 'agentStop'."""
        hook = self._load_hook()
        assert "when" in hook
        assert isinstance(hook["when"], dict)
        assert hook["when"].get("type") == "agentStop"

    def test_then_type_is_ask_agent(self) -> None:
        """then.type must be 'askAgent'."""
        hook = self._load_hook()
        assert "then" in hook
        assert isinstance(hook["then"], dict)
        assert hook["then"].get("type") == "askAgent"

    def test_name_starts_with_to(self) -> None:
        """name field must start with 'to ' following hook naming convention."""
        hook = self._load_hook()
        name = hook.get("name", "")
        assert name.startswith("to "), (
            f"Hook name must start with 'to ', got: {name!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Hook Decision Logic Completeness
# ---------------------------------------------------------------------------


class TestHookDecisionLogic:
    """Property-based tests for hook decision logic completeness.

    Validates that retry instructions are produced if and only if
    is_transition_confirmation=True AND is_minimal_output=True, and that "."
    is produced in all other boolean combinations.

    **Validates: Requirements 4.3, 4.4, 4.5**
    """

    @given(
        is_confirmation=st.booleans(),
        is_minimal=st.booleans(),
    )
    @settings(max_examples=20)
    def test_retry_only_when_both_true(
        self, is_confirmation: bool, is_minimal: bool
    ) -> None:
        """Hook produces 'retry' iff both confirmation and minimal are True.

        Args:
            is_confirmation: Whether the message is a transition confirmation.
            is_minimal: Whether the agent output is minimal.
        """
        result = hook_decision(is_confirmation, is_minimal)

        if is_confirmation and is_minimal:
            assert result == "retry", (
                f"Expected 'retry' when is_confirmation={is_confirmation} "
                f"and is_minimal={is_minimal}, got '{result}'"
            )
        else:
            assert result == ".", (
                f"Expected '.' when is_confirmation={is_confirmation} "
                f"and is_minimal={is_minimal}, got '{result}'"
            )

    @given(is_minimal=st.booleans())
    @settings(max_examples=20)
    def test_no_confirmation_always_passthrough(self, is_minimal: bool) -> None:
        """Hook produces '.' when there is no transition confirmation.

        Validates Requirement 4.4: If the most recent bootcamper message was NOT
        a Transition_Confirmation, the hook outputs only '.'.

        Args:
            is_minimal: Whether the agent output is minimal (irrelevant here).
        """
        result = hook_decision(is_confirmation=False, is_minimal=is_minimal)
        assert result == ".", (
            f"Expected '.' when is_confirmation=False, got '{result}'"
        )

    @given(is_confirmation=st.booleans())
    @settings(max_examples=20)
    def test_substantive_output_always_passthrough(
        self, is_confirmation: bool
    ) -> None:
        """Hook produces '.' when output is substantive (not minimal).

        Validates Requirement 4.5: If the agent output exceeds 50 characters
        with substantive content, the hook outputs only '.'.

        Args:
            is_confirmation: Whether the message is a transition confirmation.
        """
        result = hook_decision(is_confirmation=is_confirmation, is_minimal=False)
        assert result == ".", (
            f"Expected '.' when is_minimal=False, got '{result}'"
        )


# ---------------------------------------------------------------------------
# Property 2: Transition Confirmation Recognition
# ---------------------------------------------------------------------------

# Strategies for generating transition-related inputs
st_transition_pattern = st.sampled_from(TRANSITION_QUESTION_PATTERNS)
st_affirmative_phrase = st.sampled_from(AFFIRMATIVE_PHRASES)
st_random_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Z"), blacklist_categories=("Cs",)),
    min_size=1,
    max_size=80,
)


def st_non_transition_prior() -> st.SearchStrategy[str]:
    """Generate prior messages that do NOT contain any transition question pattern.

    Returns:
        A Hypothesis strategy producing strings without transition patterns.
    """
    return st_random_text.filter(
        lambda s: not any(
            pattern.lower() in s.lower() for pattern in TRANSITION_QUESTION_PATTERNS
        )
    )


def st_non_affirmative_response() -> st.SearchStrategy[str]:
    """Generate bootcamper responses that do NOT contain any affirmative phrase.

    Returns:
        A Hypothesis strategy producing strings without affirmative phrases.
    """
    return st_random_text.filter(
        lambda s: not any(
            phrase in s.lower() for phrase in AFFIRMATIVE_PHRASES
        )
    )


class TestTransitionConfirmationRecognition:
    """Property tests for transition confirmation recognition.

    **Validates: Requirements 4.2, 4.6**

    Property 2: Transition Confirmation Recognition
    For any pair of (prior_assistant_message, bootcamper_message), the transition
    confirmation detector returns True if and only if the prior assistant message
    contains a transition question pattern AND the bootcamper message contains an
    affirmative phrase from the recognized set; and returns False otherwise.
    """

    @given(
        pattern=st_transition_pattern,
        phrase=st_affirmative_phrase,
        prefix=st_random_text,
        suffix=st_random_text,
    )
    @settings(max_examples=20)
    def test_true_when_both_conditions_met(
        self, pattern: str, phrase: str, prefix: str, suffix: str
    ) -> None:
        """Returns True when prior message has transition pattern AND response is affirmative.

        Args:
            pattern: A transition question pattern to embed in the prior message.
            phrase: An affirmative phrase to embed in the bootcamper response.
            prefix: Random text to prepend for realism.
            suffix: Random text to append for realism.
        """
        prior_message = f"{prefix} {pattern} 3? {suffix}"
        bootcamper_message = f"{phrase}"

        result = is_transition_confirmation(bootcamper_message, prior_message)
        assert result is True, (
            f"Expected True for prior containing '{pattern}' and response '{phrase}', "
            f"got {result}"
        )

    @given(
        prior_message=st_non_transition_prior(),
        phrase=st_affirmative_phrase,
    )
    @settings(max_examples=20)
    def test_false_when_no_transition_pattern(
        self, prior_message: str, phrase: str
    ) -> None:
        """Returns False when prior message lacks a transition question pattern.

        Even if the bootcamper response is affirmative, the absence of a transition
        question in the prior message means this is not a transition confirmation.

        Args:
            prior_message: A message without any transition question pattern.
            phrase: An affirmative phrase (should not matter without the pattern).
        """
        result = is_transition_confirmation(phrase, prior_message)
        assert result is False, (
            f"Expected False when prior lacks transition pattern, got {result}. "
            f"Prior: {prior_message!r}, Response: {phrase!r}"
        )

    @given(
        pattern=st_transition_pattern,
        response=st_non_affirmative_response(),
        prefix=st_random_text,
    )
    @settings(max_examples=20)
    def test_false_when_no_affirmative_phrase(
        self, pattern: str, response: str, prefix: str
    ) -> None:
        """Returns False when bootcamper response lacks an affirmative phrase.

        Even if the prior message contains a transition question, a non-affirmative
        response means this is not a transition confirmation.

        Args:
            pattern: A transition question pattern in the prior message.
            response: A response without any recognized affirmative phrase.
            prefix: Random text to prepend to the prior message.
        """
        prior_message = f"{prefix} {pattern} 5?"
        result = is_transition_confirmation(response, prior_message)
        assert result is False, (
            f"Expected False when response lacks affirmative phrase, got {result}. "
            f"Prior: {prior_message!r}, Response: {response!r}"
        )

    @given(
        prior_message=st_non_transition_prior(),
        response=st_non_affirmative_response(),
    )
    @settings(max_examples=20)
    def test_false_when_neither_condition_met(
        self, prior_message: str, response: str
    ) -> None:
        """Returns False when neither condition is met.

        When the prior message has no transition pattern and the response has no
        affirmative phrase, the result must be False.

        Args:
            prior_message: A message without any transition question pattern.
            response: A response without any recognized affirmative phrase.
        """
        result = is_transition_confirmation(response, prior_message)
        assert result is False, (
            f"Expected False when neither condition met, got {result}. "
            f"Prior: {prior_message!r}, Response: {response!r}"
        )
