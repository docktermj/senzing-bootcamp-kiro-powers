"""Unit tests for agent behavior rules detection functions.

Verifies continuation request detection and pause language detection
with specific examples, edge cases, and boundary conditions.

Feature: agent-behavior-rules
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_behavior_rules import (
    AcknowledgmentResult,
    contains_pause_language,
    has_pointer_prefix,
    is_compound_question,
    is_continuation_request,
    validate_acknowledgment,
    validate_steering_file,
)


# ---------------------------------------------------------------------------
# Tests: Continuation Request Detection
# ---------------------------------------------------------------------------


class TestContinuationRequestDetection:
    """Unit tests for is_continuation_request().

    Validates: Requirements 1.1, 1.4, 1.5
    """

    def test_exact_phrases(self) -> None:
        """Exact continuation phrases are detected."""
        phrases = [
            "continue",
            "next",
            "proceed",
            "go on",
            "keep going",
            "move on",
            "carry on",
        ]
        for phrase in phrases:
            assert is_continuation_request(phrase), (
                f"Expected {phrase!r} to be detected as continuation request"
            )

    def test_phrases_in_context(self) -> None:
        """Continuation phrases embedded in longer messages are detected."""
        messages = [
            "Let's continue to module 3",
            "I want to keep going",
            "next module please",
            "Yes, let's proceed with the next step",
            "go on to the next topic",
            "I'd like to move on now",
            "let's carry on with the bootcamp",
        ]
        for msg in messages:
            assert is_continuation_request(msg), (
                f"Expected {msg!r} to be detected as continuation request"
            )

    def test_case_insensitive(self) -> None:
        """Detection is case-insensitive."""
        messages = [
            "CONTINUE",
            "Keep Going",
            "NEXT MODULE",
            "Proceed",
            "GO ON",
            "MOVE ON",
            "Carry On",
        ]
        for msg in messages:
            assert is_continuation_request(msg), (
                f"Expected {msg!r} to be detected as continuation request (case-insensitive)"
            )

    def test_negative_cases(self) -> None:
        """Messages without continuation phrases are not detected."""
        messages = [
            "hello",
            "what is entity resolution?",
            "I have a question",
            "tell me about Senzing",
            "how does this work?",
            "thanks for explaining that",
        ]
        for msg in messages:
            assert not is_continuation_request(msg), (
                f"Expected {msg!r} to NOT be detected as continuation request"
            )

    def test_empty_and_whitespace(self) -> None:
        """Empty and whitespace-only strings are not continuation requests."""
        messages = ["", "   ", "\t\n"]
        for msg in messages:
            assert not is_continuation_request(msg), (
                f"Expected {msg!r} to NOT be detected as continuation request"
            )

    def test_unicode(self) -> None:
        """Unicode messages without continuation phrases are not detected."""
        messages = [
            "\u3053\u3093\u306b\u3061\u306f",
            "\u00bfC\u00f3mo est\u00e1s?",
            "\u00d1o\u00f1o se\u00f1or",
            "\U0001f389 great job!",
            "caf\u00e9 r\u00e9sum\u00e9 na\u00efve",
        ]
        for msg in messages:
            assert not is_continuation_request(msg), (
                f"Expected {msg!r} to NOT be detected as continuation request"
            )

    def test_very_long_input(self) -> None:
        """A very long string without continuation phrases is not detected."""
        long_msg = "word " * 10000  # 50000 characters, no continuation phrases
        assert not is_continuation_request(long_msg)


# ---------------------------------------------------------------------------
# Tests: Pause Language Detection
# ---------------------------------------------------------------------------


class TestPauseLanguageDetection:
    """Unit tests for contains_pause_language().

    Validates: Requirements 1.1, 1.2, 1.4
    """

    def test_exact_pause_phrases(self) -> None:
        """Exact pause phrases are detected."""
        phrases = [
            "take a break",
            "pause",
            "stop here",
            "pick this up later",
        ]
        for phrase in phrases:
            assert contains_pause_language(phrase), (
                f"Expected {phrase!r} to be detected as pause language"
            )

    def test_continuation_defer(self) -> None:
        """Continuation-with-deferral phrases are detected as pause language."""
        phrases = [
            "continue later",
            "continue tomorrow",
            "continue next time",
            "continue in a new session",
        ]
        for phrase in phrases:
            assert contains_pause_language(phrase), (
                f"Expected {phrase!r} to be detected as pause language"
            )

    def test_other_pause_phrases(self) -> None:
        """Other pause/wrap-up phrases are detected."""
        phrases = [
            "call it a day",
            "wrap up for now",
            "save my progress for later",
        ]
        for phrase in phrases:
            assert contains_pause_language(phrase), (
                f"Expected {phrase!r} to be detected as pause language"
            )

    def test_case_insensitive(self) -> None:
        """Pause detection is case-insensitive."""
        phrases = [
            "TAKE A BREAK",
            "Pause",
            "STOP HERE",
            "Pick This Up Later",
            "CALL IT A DAY",
        ]
        for phrase in phrases:
            assert contains_pause_language(phrase), (
                f"Expected {phrase!r} to be detected as pause language (case-insensitive)"
            )

    def test_negative_cases(self) -> None:
        """Continuation phrases are NOT pause language."""
        messages = [
            "continue",
            "next",
            "keep going",
            "proceed",
            "move on",
            "let's go",
        ]
        for msg in messages:
            assert not contains_pause_language(msg), (
                f"Expected {msg!r} to NOT be detected as pause language"
            )

    def test_empty_and_whitespace(self) -> None:
        """Empty and whitespace-only strings are not pause language."""
        messages = ["", "   "]
        for msg in messages:
            assert not contains_pause_language(msg), (
                f"Expected {msg!r} to NOT be detected as pause language"
            )

    def test_pause_in_context(self) -> None:
        """Pause phrases embedded in longer sentences are detected."""
        messages = [
            "Maybe we should take a break here",
            "I think I'll pick this up later",
            "Let's call it a day and come back tomorrow",
            "Can we wrap up for now?",
            "I'd like to pause and think about this",
        ]
        for msg in messages:
            assert contains_pause_language(msg), (
                f"Expected {msg!r} to be detected as pause language in context"
            )


# ---------------------------------------------------------------------------
# Tests: Acknowledgment Validation
# ---------------------------------------------------------------------------


class TestAcknowledgmentValidation:
    """Unit tests for validate_acknowledgment().

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """

    def test_exactly_50_words_valid(self) -> None:
        """A substantive text with exactly 50 words and ≤2 sentences is valid."""
        # Build a 50-word, 2-sentence text with substantive content
        text = (
            "Your Senzing instance uses PostgreSQL as the backend database "
            "which provides excellent performance for entity resolution workloads "
            "and supports concurrent access patterns needed for production "
            "deployments with multiple data sources feeding records into the "
            "system here. The configuration looks correct for your environment "
            "and matches the recommended settings for deployments."
        )
        words = text.split()
        assert len(words) == 50, f"Expected 50 words, got {len(words)}"
        result = validate_acknowledgment(text)
        assert result.valid is True
        assert result.word_count == 50

    def test_exactly_2_sentences_valid(self) -> None:
        """A substantive text with exactly 2 sentences and ≤50 words is valid."""
        text = "You chose Python for your SDK language. That works well with Senzing."
        result = validate_acknowledgment(text)
        assert result.valid is True
        assert result.sentence_count == 2

    def test_51_words_invalid(self) -> None:
        """A text with 51 words exceeds the limit and is invalid."""
        text = (
            "Your Senzing instance uses PostgreSQL as the backend database "
            "which provides excellent performance for entity resolution workloads "
            "and supports concurrent access patterns needed for production "
            "deployments with multiple data sources feeding records into the "
            "system here now. The configuration looks correct for your environment "
            "and matches the recommended settings for deployments."
        )
        words = text.split()
        assert len(words) == 51, f"Expected 51 words, got {len(words)}"
        result = validate_acknowledgment(text)
        assert result.valid is False
        assert result.word_count == 51

    def test_3_sentences_invalid(self) -> None:
        """A text with 3 sentences exceeds the limit and is invalid."""
        text = "You chose Python. That works well. Let me set it up."
        result = validate_acknowledgment(text)
        assert result.valid is False
        assert result.sentence_count == 3

    def test_content_free_got_it(self) -> None:
        """'Got it' alone is not substantive and is invalid."""
        result = validate_acknowledgment("Got it")
        assert result.is_substantive is False
        assert result.valid is False

    def test_content_free_okay(self) -> None:
        """'Okay' alone is not substantive and is invalid."""
        result = validate_acknowledgment("Okay")
        assert result.is_substantive is False
        assert result.valid is False

    def test_content_free_sure_thanks(self) -> None:
        """'Sure, thanks' is not substantive and is invalid."""
        result = validate_acknowledgment("Sure, thanks")
        assert result.is_substantive is False
        assert result.valid is False

    def test_substantive_with_content(self) -> None:
        """'Got it, your Senzing instance uses PostgreSQL' is substantive and valid."""
        result = validate_acknowledgment("Got it, your Senzing instance uses PostgreSQL")
        assert result.is_substantive is True
        assert result.valid is True

    def test_substantive_reference(self) -> None:
        """'You chose Python for your SDK language' is substantive and valid."""
        result = validate_acknowledgment("You chose Python for your SDK language")
        assert result.is_substantive is True
        assert result.valid is True

    def test_empty_string(self) -> None:
        """Empty string is invalid with zero counts and not substantive."""
        result = validate_acknowledgment("")
        assert result.valid is False
        assert result.sentence_count == 0
        assert result.word_count == 0
        assert result.is_substantive is False

    def test_whitespace_only(self) -> None:
        """Whitespace-only string is invalid."""
        result = validate_acknowledgment("   ")
        assert result.valid is False

    def test_position_ok_standalone(self) -> None:
        """Standalone text always has position_ok=True."""
        result = validate_acknowledgment("You selected the Docker deployment option")
        assert result.position_ok is True


# ---------------------------------------------------------------------------
# Tests: Compound Question Detection
# ---------------------------------------------------------------------------


class TestCompoundQuestionDetection:
    """Unit tests for is_compound_question().

    Validates: Requirements 3.1, 3.2, 3.3, 3.5
    """

    def test_compound_with_or(self) -> None:
        """A question with 'or' joining alternatives is compound."""
        assert is_compound_question("Would you like Python or Java?") is True

    def test_compound_with_alternatively(self) -> None:
        """A question with 'alternatively' is compound."""
        assert is_compound_question(
            "Should we use Docker, or alternatively Kubernetes?"
        ) is True

    def test_compound_or_would_you_rather(self) -> None:
        """A question with 'or would you rather' is compound."""
        assert is_compound_question(
            "Do you want to continue or would you rather stop?"
        ) is True

    def test_compound_or_should_we(self) -> None:
        """A question with 'or should we' is compound."""
        assert is_compound_question(
            "Should we deploy now or should we wait?"
        ) is True

    def test_compound_or_would_you_prefer(self) -> None:
        """A question with 'or would you prefer' is compound."""
        assert is_compound_question(
            "Would you like option A or would you prefer option B?"
        ) is True

    def test_simple_yes_no(self) -> None:
        """A simple yes/no question without conjunctions is not compound."""
        assert is_compound_question("Ready to continue?") is False

    def test_simple_confirmation(self) -> None:
        """A simple confirmation question is not compound."""
        assert is_compound_question("Does that look correct?") is False

    def test_simple_shall_we(self) -> None:
        """A simple 'shall we' question is not compound."""
        assert is_compound_question("Shall we proceed?") is False

    def test_no_question_mark(self) -> None:
        """A statement without '?' is not detected as a compound question."""
        assert is_compound_question("Would you like Python or Java") is False

    def test_or_at_end_of_line(self) -> None:
        """'or' at end of line is excluded by the pattern."""
        assert is_compound_question("Is this the one or\n") is False


# ---------------------------------------------------------------------------
# Tests: Pointer Indicator
# ---------------------------------------------------------------------------


class TestPointerIndicator:
    """Unit tests for has_pointer_prefix().

    Validates: Requirements 4.1, 4.3, 4.5
    """

    def test_pointer_prefix_present(self) -> None:
        """Line starting with pointer emoji is detected."""
        assert has_pointer_prefix("\U0001f449 Ready to continue?") is True

    def test_pointer_prefix_missing(self) -> None:
        """Line without pointer emoji is not detected."""
        assert has_pointer_prefix("Ready to continue?") is False

    def test_pointer_with_list_marker_dash(self) -> None:
        """Pointer after dash list marker is detected."""
        assert has_pointer_prefix("- \U0001f449 Choose your language:") is True

    def test_pointer_with_list_marker_star(self) -> None:
        """Pointer after star list marker is detected."""
        assert has_pointer_prefix("* \U0001f449 Select an option:") is True

    def test_pointer_in_middle(self) -> None:
        """Pointer not at start (after stripping) is not detected."""
        assert has_pointer_prefix("Please respond \U0001f449 here") is False

    def test_empty_line(self) -> None:
        """Empty line is not detected."""
        assert has_pointer_prefix("") is False

    def test_pointer_with_leading_whitespace(self) -> None:
        """Leading whitespace is stripped before checking."""
        assert has_pointer_prefix("  \U0001f449 Ready?") is True

    def test_other_emoji_prefix(self) -> None:
        """Other emojis are not the pointer indicator."""
        assert has_pointer_prefix("\U0001f389 Great job!") is False


# ---------------------------------------------------------------------------
# Tests: Steering File Structure Validation
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_STEERING_FILE = _STEERING_DIR / "agent-behavior-rules.md"
_STEERING_INDEX = _STEERING_DIR / "steering-index.yaml"


class TestSteeringFileStructure:
    """Unit tests for steering file structure validation.

    Validates: Requirements 4.4
    """

    def test_steering_file_exists(self) -> None:
        """Verify agent-behavior-rules.md exists at the expected path."""
        assert _STEERING_FILE.exists(), (
            f"Expected steering file at {_STEERING_FILE}"
        )

    def test_yaml_frontmatter_present(self) -> None:
        """Verify the file starts with '---' and has a second '---' delimiter."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert lines[0].strip() == "---", (
            "Steering file must start with '---' YAML frontmatter delimiter"
        )
        # Find the closing delimiter (skip the first line)
        closing_found = any(line.strip() == "---" for line in lines[1:])
        assert closing_found, (
            "Steering file must have a closing '---' YAML frontmatter delimiter"
        )

    def test_yaml_frontmatter_inclusion_auto(self) -> None:
        """Parse the YAML frontmatter and verify inclusion: auto is set."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        lines = content.splitlines()
        # Extract frontmatter between first and second '---'
        assert lines[0].strip() == "---"
        frontmatter_lines: list[str] = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            frontmatter_lines.append(line)
        frontmatter = "\n".join(frontmatter_lines)
        assert "inclusion: auto" in frontmatter or "inclusion:auto" in frontmatter, (
            "YAML frontmatter must contain 'inclusion: auto'"
        )

    def test_yaml_frontmatter_has_description(self) -> None:
        """Parse the YAML frontmatter and verify description field exists and is non-empty."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert lines[0].strip() == "---"
        frontmatter_lines: list[str] = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            frontmatter_lines.append(line)
        # Find description key
        description_value = ""
        for line in frontmatter_lines:
            if line.startswith("description:"):
                description_value = line.split(":", 1)[1].strip().strip("\"'")
                break
        assert description_value, (
            "YAML frontmatter must contain a non-empty 'description' field"
        )

    def test_steering_index_contains_entry(self) -> None:
        """Verify steering-index.yaml contains 'agent-behavior-rules.md' entry."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")
        assert "agent-behavior-rules.md" in content, (
            "steering-index.yaml must contain an entry for agent-behavior-rules.md"
        )

    def test_steering_index_token_count(self) -> None:
        """Verify the entry has a numeric token_count value."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")
        lines = content.splitlines()
        # Find the agent-behavior-rules.md section and its token_count
        in_section = False
        token_count_found = False
        for line in lines:
            if "agent-behavior-rules.md" in line:
                in_section = True
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("token_count:"):
                    value = stripped.split(":", 1)[1].strip()
                    assert value.isdigit(), (
                        f"token_count must be numeric, got {value!r}"
                    )
                    token_count_found = True
                    break
                # If we hit another top-level key, stop searching
                if not line.startswith(" ") and not line.startswith("\t") and line.strip():
                    break
        assert token_count_found, (
            "agent-behavior-rules.md entry must have a token_count field"
        )

    def test_steering_index_size_category(self) -> None:
        """Verify the entry has size_category: medium."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")
        lines = content.splitlines()
        in_section = False
        size_category_found = False
        for line in lines:
            if "agent-behavior-rules.md" in line:
                in_section = True
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("size_category:"):
                    value = stripped.split(":", 1)[1].strip()
                    assert value == "medium", (
                        f"size_category must be 'medium', got {value!r}"
                    )
                    size_category_found = True
                    break
                if not line.startswith(" ") and not line.startswith("\t") and line.strip():
                    break
        assert size_category_found, (
            "agent-behavior-rules.md entry must have a size_category field"
        )

    def test_file_has_main_heading(self) -> None:
        """Verify the file contains '# Agent Behavior Rules' heading."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        assert "# Agent Behavior Rules" in content, (
            "Steering file must contain '# Agent Behavior Rules' heading"
        )

    def test_file_has_four_rule_sections(self) -> None:
        """Verify the file contains '## Rule 1', '## Rule 2', '## Rule 3', '## Rule 4'."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        for i in range(1, 5):
            assert f"## Rule {i}" in content, (
                f"Steering file must contain '## Rule {i}' section heading"
            )

    def test_validate_steering_file_no_violations(self) -> None:
        """Run validate_steering_file on the file and verify 0 violations."""
        violations = validate_steering_file(_STEERING_FILE)
        assert violations == [], (
            f"Expected 0 violations, got {len(violations)}: "
            f"{[v.message for v in violations]}"
        )
