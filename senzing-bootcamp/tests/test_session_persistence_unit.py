"""Unit tests for session persistence preference writing and loading.

Covers:
- Task 8.1: Preference writing unit tests
  - Test file creation when preferences file does not exist
  - Test filesystem error handling with mocked I/O (returns WriteResult with error)
  - Test write preserves existing fields when adding new field
  - Test write rejects unknown keys
  - Test write rejects file exceeding 10 KB
- Task 8.2: Preference loading and recovery unit tests
  - Test loading from valid complete file returns all preferences
  - Test loading from missing file returns appropriate error
  - Test loading from invalid YAML returns parse error
  - Test loading from file with missing required fields lists them correctly
  - Test empty preferences file handling

Requirements: 1.7, 1.8, 2.1, 3.1, 3.2, 3.3, 6.3, 6.6
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import (
    FORBIDDEN_TEMPORAL_PHRASES,
    format_context_reset,
    format_resume_summary,
    load_preferences,
    parse_yaml,
    resolve_language_steering,
    write_preference,
)

# ═══════════════════════════════════════════════════════════════════════════
# Task 8.1 — Preference writing unit tests
# Requirements: 1.7, 1.8, 6.3, 6.6
# ═══════════════════════════════════════════════════════════════════════════


class TestPreferenceWriting:
    """Verify write_preference() behavior for file creation, errors, and validation."""

    def test_creates_file_when_not_exists(self, tmp_path: Path) -> None:
        """Write a preference when no file exists; verify file is created with correct content.

        Validates: Requirement 1.7
        """
        prefs_file = tmp_path / "config" / "bootcamp_preferences.yaml"
        assert not prefs_file.exists()

        result = write_preference("language", "python", preferences_path=str(prefs_file))

        assert result.success is True
        assert result.error is None
        assert prefs_file.exists()

        content = prefs_file.read_text(encoding="utf-8")
        parsed = parse_yaml(content)
        assert parsed["language"] == "python"

    def test_filesystem_error_returns_write_result_with_error(self, tmp_path: Path) -> None:
        """Mock os.replace to raise OSError; verify WriteResult has success=False and error.

        Validates: Requirements 1.8, 6.6
        """
        prefs_file = tmp_path / "config" / "bootcamp_preferences.yaml"

        with patch("preferences_utils.os.replace", side_effect=OSError("disk full")):
            result = write_preference(
                "language", "python", preferences_path=str(prefs_file)
            )

        assert result.success is False
        assert result.error is not None
        assert "disk full" in result.error

    def test_preserves_existing_fields(self, tmp_path: Path) -> None:
        """Write one field, then write another; verify both are present.

        Validates: Requirement 6.3
        """
        prefs_file = tmp_path / "config" / "bootcamp_preferences.yaml"

        # Write first field
        result1 = write_preference("language", "python", preferences_path=str(prefs_file))
        assert result1.success is True

        # Write second field
        result2 = write_preference(
            "track", "core_bootcamp", preferences_path=str(prefs_file)
        )
        assert result2.success is True

        # Verify both fields are present
        content = prefs_file.read_text(encoding="utf-8")
        parsed = parse_yaml(content)
        assert parsed["language"] == "python"
        assert parsed["track"] == "core_bootcamp"

    def test_rejects_unknown_keys(self, tmp_path: Path) -> None:
        """Try to write a key not in KNOWN_TOP_LEVEL_KEYS; verify WriteResult has success=False.

        Validates: Requirement 6.3
        """
        prefs_file = tmp_path / "config" / "bootcamp_preferences.yaml"

        result = write_preference(
            "unknown_bogus_key", "value", preferences_path=str(prefs_file)
        )

        assert result.success is False
        assert result.error is not None
        assert "Unknown key" in result.error
        assert "unknown_bogus_key" in result.error

    def test_rejects_file_exceeding_10kb(self, tmp_path: Path) -> None:
        """Try to write a value that would make the file exceed 10 KB; verify rejection.

        Validates: Requirement 6.6
        """
        prefs_file = tmp_path / "config" / "bootcamp_preferences.yaml"

        # Create a value large enough to exceed 10 KB
        large_value = "x" * (11 * 1024)

        result = write_preference(
            "language", large_value, preferences_path=str(prefs_file)
        )

        assert result.success is False
        assert result.error is not None
        assert "10 KB" in result.error


# ═══════════════════════════════════════════════════════════════════════════
# Task 8.2 — Preference loading and recovery unit tests
# Requirements: 2.1, 3.1, 3.2, 3.3
# ═══════════════════════════════════════════════════════════════════════════


class TestPreferenceLoading:
    """Verify load_preferences() handles valid, missing, invalid, and partial files."""

    def test_load_valid_complete_file(self, tmp_path: Path) -> None:
        """Loading a valid YAML file with all required fields returns all preferences.

        Validates: Requirements 2.1, 3.3
        """
        prefs_file = tmp_path / "bootcamp_preferences.yaml"
        prefs_file.write_text(
            "language: python\ntrack: core_bootcamp\nverbosity: standard\n",
            encoding="utf-8",
        )

        result = load_preferences(preferences_path=str(prefs_file))

        assert result.preferences is not None
        assert result.preferences["language"] == "python"
        assert result.preferences["track"] == "core_bootcamp"
        assert result.preferences["verbosity"] == "standard"
        assert result.missing_required == []
        assert result.error is None

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """Loading from a non-existent path returns error and lists all required fields.

        Validates: Requirements 3.1
        """
        missing_path = str(tmp_path / "nonexistent.yaml")

        result = load_preferences(preferences_path=missing_path)

        assert result.preferences is None
        assert result.error is not None
        assert "not found" in result.error.lower() or "not found" in result.error
        assert "language" in result.missing_required
        assert "track" in result.missing_required
        assert "verbosity" in result.missing_required

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Loading a file with invalid YAML content returns a parse error.

        Validates: Requirements 3.2
        """
        invalid_file = tmp_path / "bad_prefs.yaml"
        invalid_file.write_text(
            "  indented_without_key\n  another bad line\n",
            encoding="utf-8",
        )

        result = load_preferences(preferences_path=str(invalid_file))

        assert result.preferences is None
        assert result.error is not None
        assert "Invalid YAML" in result.error
        assert "language" in result.missing_required
        assert "track" in result.missing_required
        assert "verbosity" in result.missing_required

    def test_load_missing_required_fields(self, tmp_path: Path) -> None:
        """Loading a file with only 'language' reports 'track' and 'verbosity' as missing.

        Validates: Requirements 3.3
        """
        partial_file = tmp_path / "partial_prefs.yaml"
        partial_file.write_text("language: java\n", encoding="utf-8")

        result = load_preferences(preferences_path=str(partial_file))

        assert result.preferences is not None
        assert result.preferences["language"] == "java"
        assert result.error is None
        assert "track" in result.missing_required
        assert "verbosity" in result.missing_required
        assert "language" not in result.missing_required

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Loading an empty file reports all required fields as missing.

        Validates: Requirements 3.1, 3.3
        """
        empty_file = tmp_path / "empty_prefs.yaml"
        empty_file.write_text("", encoding="utf-8")

        result = load_preferences(preferences_path=str(empty_file))

        # Empty file should parse successfully but have no fields
        assert "language" in result.missing_required
        assert "track" in result.missing_required
        assert "verbosity" in result.missing_required


# ═══════════════════════════════════════════════════════════════════════════
# Task 8.3 — Language steering mapping and resume summary unit tests
# Requirements: 2.2, 2.4, 2.5
# ═══════════════════════════════════════════════════════════════════════════


class TestLanguageSteeringAndResumeSummary:
    """Unit tests for language steering mapping and resume summary formatting.

    Validates: Requirements 2.2, 2.4, 2.5
    """

    def test_python_maps_to_lang_python_md(self) -> None:
        """Verify 'python' maps to 'lang-python.md'.

        Validates: Requirement 2.4
        """
        result = resolve_language_steering("python")
        assert result == "lang-python.md"

    def test_csharp_maps_to_lang_csharp_md(self) -> None:
        """Verify 'csharp' maps to 'lang-csharp.md'.

        Validates: Requirement 2.4
        """
        result = resolve_language_steering("csharp")
        assert result == "lang-csharp.md"

    def test_case_insensitive_matching(self) -> None:
        """Verify Python, PYTHON, python all map to lang-python.md.

        Validates: Requirement 2.4
        """
        assert resolve_language_steering("Python") == "lang-python.md"
        assert resolve_language_steering("PYTHON") == "lang-python.md"
        assert resolve_language_steering("python") == "lang-python.md"

    def test_unrecognized_language_returns_none(self) -> None:
        """Verify an unrecognized language returns None.

        Validates: Requirement 2.5
        """
        result = resolve_language_steering("cobol")
        assert result is None

    def test_resume_summary_contains_all_values(self) -> None:
        """Verify resume summary contains language, track, and verbosity.

        Validates: Requirement 2.2
        """
        summary = format_resume_summary("python", "core_bootcamp", "standard")
        assert "python" in summary
        assert "core_bootcamp" in summary
        assert "standard" in summary

    def test_resume_summary_at_most_two_sentences(self) -> None:
        """Verify resume summary is at most 2 sentences.

        Validates: Requirement 2.2
        """
        summary = format_resume_summary("java", "advanced_track", "detailed")
        # Count sentences by splitting on period followed by space or end
        sentence_count = summary.strip().count(". ") + (
            1 if summary.strip().endswith(".") else 0
        )
        assert sentence_count <= 2


# ═══════════════════════════════════════════════════════════════════════════
# Task 8.4 — Context reset message formatting unit tests
# Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4
# ═══════════════════════════════════════════════════════════════════════════


class TestContextResetMessage:
    """Unit tests for context reset message formatting.

    Validates: Requirements 4.1-4.7, 5.1-5.4
    """

    def test_message_with_valid_progress_file(self, tmp_path: Path) -> None:
        """Create a progress JSON file, call format_context_reset, verify all elements.

        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 5.1, 5.3
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        progress_file = config_dir / "bootcamp_progress.json"
        progress_file.write_text(
            '{"current_module": 5, "current_step": "exercise"}',
            encoding="utf-8",
        )

        result = format_context_reset(progress_path=str(progress_file))

        # Contains technical reason (memory/context)
        assert "memory" in result.message.lower() or "context" in result.message.lower()
        # Contains immediacy (right now / immediately / new chat)
        assert "right now" in result.message.lower() or "new chat" in result.message.lower()
        # Contains progress reassurance (saved / progress)
        assert "saved" in result.message.lower() or "progress" in result.message.lower()
        # Contains continuation phrase in quotes
        assert result.continuation_phrase in result.message
        assert f'"{result.continuation_phrase}"' in result.message
        # Module number is correct
        assert result.module_number == 5
        assert "5" in result.message

    def test_message_with_missing_progress_file(self, tmp_path: Path) -> None:
        """Call with non-existent path, verify fallback module=1.

        Validates: Requirements 4.5, 5.3
        """
        missing_path = str(tmp_path / "nonexistent" / "progress.json")

        result = format_context_reset(progress_path=missing_path)

        assert result.module_number == 1
        assert "1" in result.message

    def test_no_forbidden_temporal_phrases(self, tmp_path: Path) -> None:
        """Verify message contains no forbidden temporal phrases.

        Validates: Requirement 4.6
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        progress_file = config_dir / "bootcamp_progress.json"
        progress_file.write_text(
            '{"current_module": 3, "current_step": "intro"}',
            encoding="utf-8",
        )

        result = format_context_reset(progress_path=str(progress_file))

        message_lower = result.message.lower()
        for phrase in FORBIDDEN_TEMPORAL_PHRASES:
            assert phrase not in message_lower, (
                f"Forbidden phrase '{phrase}' found in message"
            )

    def test_at_most_four_sentences(self, tmp_path: Path) -> None:
        """Verify message is at most 4 sentences.

        Validates: Requirement 5.2
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        progress_file = config_dir / "bootcamp_progress.json"
        progress_file.write_text(
            '{"current_module": 7, "current_step": 2}',
            encoding="utf-8",
        )

        result = format_context_reset(progress_path=str(progress_file))

        # Count sentences: split on '. ' and account for final period
        sentences = [s.strip() for s in result.message.split(". ") if s.strip()]
        assert len(sentences) <= 4

    def test_no_question_marks(self, tmp_path: Path) -> None:
        """Verify message contains no question marks.

        Validates: Requirement 5.4
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        progress_file = config_dir / "bootcamp_progress.json"
        progress_file.write_text(
            '{"current_module": 9, "current_step": "review"}',
            encoding="utf-8",
        )

        result = format_context_reset(progress_path=str(progress_file))

        assert "?" not in result.message

    def test_continuation_phrase_in_quotation_marks(self, tmp_path: Path) -> None:
        """Verify the continuation phrase appears in quotation marks in the message.

        Validates: Requirement 4.4
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        progress_file = config_dir / "bootcamp_progress.json"
        progress_file.write_text(
            '{"current_module": 4, "current_step": "exercise"}',
            encoding="utf-8",
        )

        result = format_context_reset(progress_path=str(progress_file))

        # The continuation phrase must be enclosed in quotation marks
        assert f'"{result.continuation_phrase}"' in result.message
