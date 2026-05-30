"""Integration tests for session persistence end-to-end flows.

Covers:
- Task 10.1: Integration tests
  - Test full session resume flow: write preferences, load, verify round-trip
  - Test recovery flow: corrupt file, load, re-write, load succeeds
  - Test context reset message generation with real progress file
  - Test steering file content validation (no forbidden phrases in templates)

Requirements: 1.1, 2.1, 3.1, 4.1, 5.1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import (
    FORBIDDEN_TEMPORAL_PHRASES,
    format_context_reset,
    load_preferences,
    write_preference,
)

# Path to the steering directory (relative to this test file)
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"


class TestSessionPersistenceIntegration:
    """Integration tests exercising full session persistence flows."""

    def test_full_session_resume_flow(self, tmp_path: Path) -> None:
        """Write language, track, verbosity one by one, then load and verify all three.

        Simulates a full session resume: preferences are written incrementally
        during onboarding, then loaded in a new session.

        Validates: Requirements 1.1, 2.1
        """
        prefs_file = tmp_path / "config" / "bootcamp_preferences.yaml"
        prefs_path = str(prefs_file)

        # Write preferences one at a time (simulating onboarding flow)
        result1 = write_preference("language", "python", preferences_path=prefs_path)
        assert result1.success is True

        result2 = write_preference("track", "core_bootcamp", preferences_path=prefs_path)
        assert result2.success is True

        result3 = write_preference("verbosity", "standard", preferences_path=prefs_path)
        assert result3.success is True

        # Simulate new session: load preferences
        load_result = load_preferences(preferences_path=prefs_path)

        assert load_result.error is None
        assert load_result.preferences is not None
        assert load_result.missing_required == []
        assert load_result.preferences["language"] == "python"
        assert load_result.preferences["track"] == "core_bootcamp"
        assert load_result.preferences["verbosity"] == "standard"

    def test_recovery_flow(self, tmp_path: Path) -> None:
        """Create corrupt file, load (expect error), re-write valid prefs, load succeeds.

        Simulates the recovery flow: a corrupt preferences file is detected,
        the agent prompts for re-entry, writes valid values, and the next
        session loads successfully.

        Validates: Requirements 3.1, 1.1, 2.1
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        prefs_file = config_dir / "bootcamp_preferences.yaml"
        prefs_path = str(prefs_file)

        # Create a corrupt file with invalid YAML
        prefs_file.write_text(
            "  this is not valid yaml\n  indented without key\n",
            encoding="utf-8",
        )

        # Load should report an error
        load_result = load_preferences(preferences_path=prefs_path)
        assert load_result.error is not None
        assert "Invalid YAML" in load_result.error
        assert load_result.preferences is None
        assert "language" in load_result.missing_required
        assert "track" in load_result.missing_required
        assert "verbosity" in load_result.missing_required

        # Recovery: re-write valid preferences one by one
        result1 = write_preference("language", "java", preferences_path=prefs_path)
        assert result1.success is True

        result2 = write_preference("track", "advanced_track", preferences_path=prefs_path)
        assert result2.success is True

        result3 = write_preference("verbosity", "detailed", preferences_path=prefs_path)
        assert result3.success is True

        # Load again — should succeed
        load_result2 = load_preferences(preferences_path=prefs_path)
        assert load_result2.error is None
        assert load_result2.preferences is not None
        assert load_result2.missing_required == []
        assert load_result2.preferences["language"] == "java"
        assert load_result2.preferences["track"] == "advanced_track"
        assert load_result2.preferences["verbosity"] == "detailed"

    def test_context_reset_with_real_progress_file(self, tmp_path: Path) -> None:
        """Create a valid progress file with module=7 and step='exercise', verify message.

        Validates: Requirements 4.1, 5.1
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        progress_file = config_dir / "bootcamp_progress.json"
        progress_file.write_text(
            json.dumps({
                "current_module": 7,
                "current_step": "exercise",
                "modules_completed": [1, 2, 3, 4, 5, 6],
            }),
            encoding="utf-8",
        )

        result = format_context_reset(progress_path=str(progress_file))

        # Module number is correct
        assert result.module_number == 7
        assert result.step_identifier == "exercise"

        # Message contains module 7
        assert "7" in result.message

        # All required elements present
        msg_lower = result.message.lower()
        # Technical reason (memory/context)
        assert "memory" in msg_lower or "context" in msg_lower
        # Immediacy (right now / immediately / new chat)
        assert "right now" in msg_lower or "immediately" in msg_lower or "new chat" in msg_lower
        # Progress reassurance (saved / progress / project files)
        assert "saved" in msg_lower or "progress" in msg_lower
        # Continuation phrase in quotes
        assert f'"{result.continuation_phrase}"' in result.message

        # Constraints
        # No forbidden phrases
        for phrase in FORBIDDEN_TEMPORAL_PHRASES:
            assert phrase not in msg_lower, f"Forbidden phrase '{phrase}' found"
        # No question marks
        assert "?" not in result.message
        # At most 4 sentences
        sentences = [s.strip() for s in result.message.split(". ") if s.strip()]
        assert len(sentences) <= 4

    def test_steering_file_no_forbidden_phrases(self) -> None:
        """Read actual steering files and verify no forbidden temporal phrases in content.

        Excludes the documentation of the forbidden list itself (the section
        that enumerates the phrases for reference purposes).

        Validates: Requirements 4.1, 5.1
        """
        steering_files = [
            _STEERING_DIR / "session-resume.md",
            _STEERING_DIR / "agent-context-management.md",
        ]

        for steering_path in steering_files:
            assert steering_path.exists(), f"Steering file not found: {steering_path}"
            content = steering_path.read_text(encoding="utf-8")

            # Remove the "Forbidden Temporal Phrases" section entirely
            # (from the heading until the next heading of same or higher level).
            # This section documents the phrases as reference — we only want
            # to check that the phrases don't appear in instructional content.
            lines = content.split("\n")
            filtered_lines: list[str] = []
            in_forbidden_section = False
            forbidden_heading_level = 0

            for line in lines:
                stripped = line.strip()

                # Detect heading lines
                if stripped.startswith("#"):
                    heading_level = len(stripped) - len(stripped.lstrip("#"))
                    heading_text = stripped.lstrip("#").strip().lower()

                    if "forbidden temporal phrases" in heading_text:
                        # Enter the forbidden section — skip everything until
                        # next heading of same or higher level
                        in_forbidden_section = True
                        forbidden_heading_level = heading_level
                        continue

                    if in_forbidden_section and heading_level <= forbidden_heading_level:
                        # Reached a new section at same or higher level — exit
                        in_forbidden_section = False

                if in_forbidden_section:
                    continue

                filtered_lines.append(line)

            filtered_content = "\n".join(filtered_lines).lower()

            for phrase in FORBIDDEN_TEMPORAL_PHRASES:
                assert phrase not in filtered_content, (
                    f"Forbidden phrase '{phrase}' found in {steering_path.name} "
                    f"(outside documentation section)"
                )
