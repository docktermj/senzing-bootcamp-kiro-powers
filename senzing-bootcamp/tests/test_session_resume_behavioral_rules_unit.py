"""Unit tests for session-resume behavioral rules.

Verifies conversation style profile validation, fallback behavior,
Self-Answering Prohibition formatting, and Step 2b protocol confirmation
by reading and parsing the steering files.

Feature: session-resume-behavioral-rules
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
import pytest

# ---------------------------------------------------------------------------
# Paths to steering files under test
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_SESSION_RESUME: Path = _STEERING_DIR / "session-resume.md"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_VERBOSITY_PRESETS = {"concise", "standard", "detailed", "custom"}
VALID_QUESTION_FRAMINGS = {"minimal", "moderate", "full"}
VALID_TONES = {"concise", "conversational", "detailed"}
VALID_PACINGS = {"one_concept_per_turn", "grouped_concepts"}

DEFAULT_STYLE: dict[str, str] = {
    "verbosity_preset": "standard",
    "tone": "conversational",
    "question_framing": "moderate",
    "pacing": "one_concept_per_turn",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def validate_conversation_style(profile: dict) -> list[str]:
    """Validate a conversation style profile dict.

    Args:
        profile: Dictionary representing a conversation_style block.

    Returns:
        List of error messages. Empty list means valid.
    """
    errors: list[str] = []
    required_fields = {"verbosity_preset", "question_framing", "tone", "pacing"}

    for field in required_fields:
        if field not in profile:
            errors.append(f"Missing required field: {field}")

    if "verbosity_preset" in profile:
        if not isinstance(profile["verbosity_preset"], str):
            errors.append(
                f"verbosity_preset must be a string, got {type(profile['verbosity_preset']).__name__}"
            )
        elif profile["verbosity_preset"] not in VALID_VERBOSITY_PRESETS:
            errors.append(
                f"Unknown verbosity_preset: {profile['verbosity_preset']!r}"
            )

    if "question_framing" in profile:
        if not isinstance(profile["question_framing"], str):
            errors.append(
                f"question_framing must be a string, got {type(profile['question_framing']).__name__}"
            )
        elif profile["question_framing"] not in VALID_QUESTION_FRAMINGS:
            errors.append(
                f"Unknown question_framing: {profile['question_framing']!r}"
            )

    if "tone" in profile:
        if not isinstance(profile["tone"], str):
            errors.append(
                f"tone must be a string, got {type(profile['tone']).__name__}"
            )
        elif profile["tone"] not in VALID_TONES:
            errors.append(f"Unknown tone: {profile['tone']!r}")

    if "pacing" in profile:
        if not isinstance(profile["pacing"], str):
            errors.append(
                f"pacing must be a string, got {type(profile['pacing']).__name__}"
            )
        elif profile["pacing"] not in VALID_PACINGS:
            errors.append(f"Unknown pacing: {profile['pacing']!r}")

    return errors


def _read_file(path: Path) -> str:
    """Read a file and return its content as a string.

    Args:
        path: Path to the file.

    Returns:
        File content as a string.
    """
    return path.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract content under a ## heading until the next ## heading.

    Args:
        content: Full markdown content.
        heading: The heading text (without the ## prefix).

    Returns:
        The section content including the heading line.
    """
    pattern = rf"^(## {re.escape(heading)}.*)$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    # Find the next ## heading after this one
    next_heading = re.search(r"^## ", content[match.end():], re.MULTILINE)
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(content)
    return content[start:end]


def _apply_defaults_for_missing_style(
    preferences_data: dict | None,
) -> dict[str, str]:
    """Apply fallback defaults when conversation_style is missing or invalid.

    Args:
        preferences_data: Parsed YAML data from preferences file, or None.

    Returns:
        A valid conversation style dict with defaults applied.
    """
    if preferences_data is None:
        return dict(DEFAULT_STYLE)
    if not isinstance(preferences_data, dict):
        return dict(DEFAULT_STYLE)
    style = preferences_data.get("conversation_style")
    if style is None or not isinstance(style, dict):
        return dict(DEFAULT_STYLE)
    # Validate and fill missing fields with defaults
    result: dict[str, str] = {}
    for key, default_val in DEFAULT_STYLE.items():
        val = style.get(key)
        if val is None or not isinstance(val, str):
            result[key] = default_val
        else:
            result[key] = val
    return result


# ---------------------------------------------------------------------------
# Tests: 8.1 Conversation Style Profile Validation
# ---------------------------------------------------------------------------


class TestConversationStyleProfileValidation:
    """Unit tests for conversation style profile validation.

    Validates: Requirements 4.2, 4.4
    """

    def test_valid_profile_all_fields_present(self) -> None:
        """A profile with all valid fields produces no errors."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "moderate",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert errors == []

    def test_valid_profile_concise_preset(self) -> None:
        """A profile with concise preset and minimal framing is valid."""
        profile = {
            "verbosity_preset": "concise",
            "question_framing": "minimal",
            "tone": "concise",
            "pacing": "grouped_concepts",
        }
        errors = validate_conversation_style(profile)
        assert errors == []

    def test_valid_profile_detailed_preset(self) -> None:
        """A profile with detailed preset and full framing is valid."""
        profile = {
            "verbosity_preset": "detailed",
            "question_framing": "full",
            "tone": "detailed",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert errors == []

    def test_valid_profile_custom_preset(self) -> None:
        """A profile with custom preset is valid."""
        profile = {
            "verbosity_preset": "custom",
            "question_framing": "moderate",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert errors == []

    def test_missing_verbosity_preset(self) -> None:
        """Missing verbosity_preset produces an error."""
        profile = {
            "question_framing": "moderate",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("verbosity_preset" in e for e in errors)

    def test_missing_question_framing(self) -> None:
        """Missing question_framing produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("question_framing" in e for e in errors)

    def test_missing_tone(self) -> None:
        """Missing tone produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "moderate",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("tone" in e for e in errors)

    def test_missing_pacing(self) -> None:
        """Missing pacing produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "moderate",
            "tone": "conversational",
        }
        errors = validate_conversation_style(profile)
        assert any("pacing" in e for e in errors)

    def test_invalid_verbosity_preset_type(self) -> None:
        """Non-string verbosity_preset produces an error."""
        profile = {
            "verbosity_preset": 42,
            "question_framing": "moderate",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("must be a string" in e for e in errors)

    def test_invalid_tone_type(self) -> None:
        """Non-string tone produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "moderate",
            "tone": ["conversational"],
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("tone must be a string" in e for e in errors)

    def test_unknown_verbosity_preset_value(self) -> None:
        """Unknown verbosity_preset value produces an error."""
        profile = {
            "verbosity_preset": "ultra",
            "question_framing": "moderate",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("Unknown verbosity_preset" in e for e in errors)

    def test_unknown_question_framing_value(self) -> None:
        """Unknown question_framing value produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "extreme",
            "tone": "conversational",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("Unknown question_framing" in e for e in errors)

    def test_unknown_tone_value(self) -> None:
        """Unknown tone value produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "moderate",
            "tone": "sarcastic",
            "pacing": "one_concept_per_turn",
        }
        errors = validate_conversation_style(profile)
        assert any("Unknown tone" in e for e in errors)

    def test_unknown_pacing_value(self) -> None:
        """Unknown pacing value produces an error."""
        profile = {
            "verbosity_preset": "standard",
            "question_framing": "moderate",
            "tone": "conversational",
            "pacing": "rapid_fire",
        }
        errors = validate_conversation_style(profile)
        assert any("Unknown pacing" in e for e in errors)

    @pytest.mark.parametrize("field", ["verbosity_preset", "question_framing", "tone", "pacing"])
    def test_each_required_field_individually_missing(self, field: str) -> None:
        """Removing any single required field produces exactly one error for that field."""
        profile = dict(DEFAULT_STYLE)
        del profile[field]
        errors = validate_conversation_style(profile)
        assert len(errors) == 1
        assert field in errors[0]


# ---------------------------------------------------------------------------
# Tests: 8.2 Fallback Behavior
# ---------------------------------------------------------------------------


class TestFallbackBehavior:
    """Unit tests for fallback behavior when preferences are missing/malformed.

    Validates: Requirements 3.3, 7.3
    """

    def test_missing_preferences_file_returns_defaults(self) -> None:
        """When preferences data is None (file missing), defaults apply."""
        result = _apply_defaults_for_missing_style(None)
        assert result == DEFAULT_STYLE

    def test_missing_conversation_style_key_returns_defaults(self) -> None:
        """When file exists but conversation_style key is absent, defaults apply."""
        preferences_data = {
            "language": "python",
            "track": "core_bootcamp",
            "verbosity": "standard",
        }
        result = _apply_defaults_for_missing_style(preferences_data)
        assert result == DEFAULT_STYLE

    def test_malformed_conversation_style_not_dict_returns_defaults(self) -> None:
        """When conversation_style is not a dict, defaults apply."""
        preferences_data = {
            "conversation_style": "invalid_string_value",
        }
        result = _apply_defaults_for_missing_style(preferences_data)
        assert result == DEFAULT_STYLE

    def test_malformed_preferences_not_dict_returns_defaults(self) -> None:
        """When preferences data is not a dict (e.g., a list), defaults apply."""
        result = _apply_defaults_for_missing_style(["not", "a", "dict"])
        assert result == DEFAULT_STYLE

    def test_malformed_yaml_conversation_style_returns_defaults(self) -> None:
        """When conversation_style contains invalid YAML data types, defaults apply."""
        # Simulate parsing a YAML file where conversation_style is malformed
        malformed_yaml = "conversation_style: [1, 2, 3]\n"
        parsed = yaml.safe_load(malformed_yaml)
        result = _apply_defaults_for_missing_style(parsed)
        assert result == DEFAULT_STYLE

    def test_partial_conversation_style_fills_missing_with_defaults(self) -> None:
        """When conversation_style has some fields, missing ones get defaults."""
        preferences_data = {
            "conversation_style": {
                "verbosity_preset": "concise",
                "tone": "concise",
                # question_framing and pacing missing
            },
        }
        result = _apply_defaults_for_missing_style(preferences_data)
        assert result["verbosity_preset"] == "concise"
        assert result["tone"] == "concise"
        assert result["question_framing"] == "moderate"  # default
        assert result["pacing"] == "one_concept_per_turn"  # default

    def test_conversation_style_with_invalid_field_type_uses_default(self) -> None:
        """When a field has wrong type (not string), default is used for that field."""
        preferences_data = {
            "conversation_style": {
                "verbosity_preset": "standard",
                "question_framing": 123,  # wrong type
                "tone": "conversational",
                "pacing": "one_concept_per_turn",
            },
        }
        result = _apply_defaults_for_missing_style(preferences_data)
        assert result["question_framing"] == "moderate"  # default applied
        assert result["verbosity_preset"] == "standard"  # kept

    def test_session_resume_documents_fallback_defaults(self) -> None:
        """session-resume.md documents the fallback default values."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2c: Restore Conversation Style")
        assert section, "Step 2c section not found"

        # Verify the defaults are documented
        assert "standard" in section
        assert "conversational" in section
        assert "moderate" in section
        assert "one_concept_per_turn" in section


# ---------------------------------------------------------------------------
# Tests: 8.3 Self-Answering Prohibition Examples Formatting
# ---------------------------------------------------------------------------


class TestSelfAnsweringProhibitionFormatting:
    """Unit tests for Self-Answering Prohibition example formatting.

    Verifies that each WRONG example has a paired CORRECT example.

    Validates: Requirements 2.1, 2.2
    """

    def test_wrong_and_correct_examples_are_paired(self) -> None:
        """Each WRONG example has a corresponding CORRECT example."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        assert section, "Step 2b section not found"

        # Find the Self-Answering Prohibition subsection
        prohibition_start = section.find("Self-Answering Prohibition")
        assert prohibition_start != -1, "Self-Answering Prohibition not found"
        prohibition_text = section[prohibition_start:]

        wrong_count = len(re.findall(r"\*\*WRONG", prohibition_text))
        correct_count = len(re.findall(r"\*\*CORRECT", prohibition_text))

        assert wrong_count > 0, "No WRONG examples found"
        assert correct_count > 0, "No CORRECT examples found"
        assert wrong_count == correct_count, (
            f"WRONG examples ({wrong_count}) must equal "
            f"CORRECT examples ({correct_count})"
        )

    def test_wrong_examples_contain_violation_text(self) -> None:
        """WRONG examples show the agent generating text after a 👉 question."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        prohibition_start = section.find("Self-Answering Prohibition")
        prohibition_text = section[prohibition_start:]

        # Each WRONG block should contain a 👉 question followed by extra text
        wrong_blocks = re.split(r"\*\*WRONG", prohibition_text)[1:]
        for i, block in enumerate(wrong_blocks):
            # Trim to the next CORRECT marker
            end = block.find("**CORRECT")
            if end != -1:
                block = block[:end]
            assert "👉" in block, (
                f"WRONG example {i + 1} must contain a 👉 question"
            )

    def test_correct_examples_end_with_stop(self) -> None:
        """CORRECT examples show the agent stopping after the 👉 question."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        prohibition_start = section.find("Self-Answering Prohibition")
        prohibition_text = section[prohibition_start:]

        # Each CORRECT block should contain STOP
        correct_blocks = re.split(r"\*\*CORRECT", prohibition_text)[1:]
        for i, block in enumerate(correct_blocks):
            # Trim to the next WRONG marker or end
            end = block.find("**WRONG")
            if end != -1:
                block = block[:end]
            assert "STOP" in block, (
                f"CORRECT example {i + 1} must contain a STOP marker"
            )

    def test_at_least_three_wrong_correct_pairs(self) -> None:
        """There are at least 3 WRONG/CORRECT example pairs."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        prohibition_start = section.find("Self-Answering Prohibition")
        prohibition_text = section[prohibition_start:]

        wrong_count = len(re.findall(r"\*\*WRONG", prohibition_text))
        assert wrong_count >= 3, (
            f"Expected at least 3 WRONG/CORRECT pairs, found {wrong_count}"
        )


# ---------------------------------------------------------------------------
# Tests: 8.4 Step 2b Re-Read Instruction
# ---------------------------------------------------------------------------


class TestStep2bProtocolConfirmation:
    """Unit test for Step 2b instruction to re-read conversation-protocol.md.

    Validates: Requirements 1.2, 5.3
    """

    def test_step_2b_contains_protocol_confirmation_instruction(self) -> None:
        """Step 2b instructs to confirm conversation-protocol.md is loaded/active."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        assert section, "Step 2b: Behavioral Rules Reload section not found"

        # Must reference conversation-protocol.md
        assert "conversation-protocol.md" in section, (
            "Step 2b must reference conversation-protocol.md"
        )

        # Must contain instruction to confirm it is loaded or active
        lower_section = section.lower()
        has_confirm = "confirm" in lower_section
        has_loaded = "loaded" in lower_section or "active" in lower_section
        assert has_confirm and has_loaded, (
            "Step 2b must contain instruction to confirm "
            "conversation-protocol.md is loaded and active"
        )

    def test_step_2b_mentions_auto_inclusion(self) -> None:
        """Step 2b references the auto-inclusion mechanism for the protocol."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        assert section, "Step 2b section not found"

        # Should mention the inclusion: auto mechanism
        assert "auto" in section.lower(), (
            "Step 2b should reference the auto-inclusion mechanism"
        )

    def test_step_2b_provides_fallback_if_protocol_unavailable(self) -> None:
        """Step 2b provides fallback rules if conversation-protocol.md is unavailable."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        assert section, "Step 2b section not found"

        # Should mention fallback behavior
        lower_section = section.lower()
        assert "fallback" in lower_section or "unavailable" in lower_section, (
            "Step 2b should provide fallback behavior if protocol is unavailable"
        )
