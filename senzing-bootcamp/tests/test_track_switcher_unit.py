"""Unit tests for track_switcher.py — example-based and edge-case tests.

Feature: track-switching-support
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from track_switcher import (
    compute_switch,
    apply_switch,
    SwitchResult,
    load_track_definitions,
    load_module_names,
    main,
)


# ---------------------------------------------------------------------------
# Constants (from module-dependencies.yaml)
# ---------------------------------------------------------------------------

TRACK_DEFINITIONS: dict[str, list[int]] = {
    "core_bootcamp": [1, 2, 3, 4, 5, 6, 7],
    "advanced_topics": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}

MODULE_NAMES: dict[int, str] = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Data Processing",
    7: "Query & Visualize",
    8: "Performance",
    9: "Security",
    10: "Monitoring",
    11: "Deployment",
}


# ---------------------------------------------------------------------------
# Test core_bootcamp → advanced_topics switching
# ---------------------------------------------------------------------------


class TestCoreToAdvanced:
    """Validates switching from core_bootcamp to advanced_topics."""

    def test_remaining_modules(self):
        """Remaining should be [8, 9, 10, 11] — advanced modules not in core."""
        result = compute_switch(
            current_track="core_bootcamp",
            target_track="advanced_topics",
            modules_completed=[1, 2, 3, 4, 5, 6, 7],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == [8, 9, 10, 11]

    def test_extra_modules(self):
        """Extra should be [] — all core modules are in advanced_topics."""
        result = compute_switch(
            current_track="core_bootcamp",
            target_track="advanced_topics",
            modules_completed=[1, 2, 3, 4, 5, 6, 7],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.extra_modules == []


# ---------------------------------------------------------------------------
# Test advanced_topics → core_bootcamp switching
# ---------------------------------------------------------------------------


class TestAdvancedToCore:
    """Validates switching from advanced_topics to core_bootcamp."""

    def test_remaining_modules(self):
        """Remaining should be [] — all core modules already completed."""
        result = compute_switch(
            current_track="advanced_topics",
            target_track="core_bootcamp",
            modules_completed=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == []

    def test_extra_modules(self):
        """Extra should be [8, 9, 10, 11] — completed modules NOT in core_bootcamp."""
        result = compute_switch(
            current_track="advanced_topics",
            target_track="core_bootcamp",
            modules_completed=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.extra_modules == [8, 9, 10, 11]


# ---------------------------------------------------------------------------
# Test edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases for compute_switch."""

    def test_empty_modules_completed(self):
        """Empty modules_completed → remaining = all target modules."""
        result = compute_switch(
            current_track="core_bootcamp",
            target_track="advanced_topics",
            modules_completed=[],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        assert result.extra_modules == []

    def test_all_target_modules_completed(self):
        """All target modules already completed → remaining=[], is_noop=False."""
        result = compute_switch(
            current_track="advanced_topics",
            target_track="core_bootcamp",
            modules_completed=[1, 2, 3, 4, 5, 6, 7],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == []
        assert result.is_noop is False


# ---------------------------------------------------------------------------
# Test CLI rejects quick_demo with exit code 1 and stderr message
# ---------------------------------------------------------------------------


class TestQuickDemoRejection:
    """Validates Requirement 7.4, 7.5: CLI rejects quick_demo with exit code 1."""

    def test_cli_rejects_quick_demo_as_source(self, tmp_path, capsys):
        """CLI exits with code 1 and stderr message when quick_demo is --from."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "track": "core_bootcamp",
                "modules_completed": [1, 2],
                "current_module": 3,
                "current_step": None,
                "last_activity": "2025-07-15T10:00:00+00:00",
            }),
            encoding="utf-8",
        )

        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--from", "quick_demo",
                "--to", "core_bootcamp",
                "--progress", str(progress_file),
                "--yaml", str(yaml_path),
            ])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "quick_demo" in captured.err
        assert "Invalid track name" in captured.err or "invalid" in captured.err.lower()

    def test_cli_rejects_quick_demo_as_target(self, tmp_path, capsys):
        """CLI exits with code 1 and stderr message when quick_demo is --to."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "track": "core_bootcamp",
                "modules_completed": [1, 2],
                "current_module": 3,
                "current_step": None,
                "last_activity": "2025-07-15T10:00:00+00:00",
            }),
            encoding="utf-8",
        )

        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--from", "core_bootcamp",
                "--to", "quick_demo",
                "--progress", str(progress_file),
                "--yaml", str(yaml_path),
            ])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "quick_demo" in captured.err
        assert "Invalid track name" in captured.err or "invalid" in captured.err.lower()


# ---------------------------------------------------------------------------
# Test CLI dry-run JSON output and --apply behavior
# ---------------------------------------------------------------------------


class TestCLI:
    """CLI dry-run and --apply behavior tests."""

    def test_dry_run_json_output(self, tmp_path, capsys):
        """Dry-run mode prints valid JSON with expected structure."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "track": "core_bootcamp",
                "modules_completed": [1, 2, 3],
                "current_module": 4,
                "current_step": None,
                "last_activity": "2025-07-15T10:00:00+00:00",
            }),
            encoding="utf-8",
        )

        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )

        main([
            "--from", "core_bootcamp",
            "--to", "advanced_topics",
            "--progress", str(progress_file),
            "--yaml", str(yaml_path),
        ])

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["current_track"] == "core_bootcamp"
        assert output["target_track"] == "advanced_topics"
        assert output["is_noop"] is False
        assert output["remaining_modules"] == [4, 5, 6, 7, 8, 9, 10, 11]
        assert output["extra_modules"] == []
        assert output["modules_completed"] == [1, 2, 3]
        assert "remaining_module_names" in output
        assert "extra_module_names" in output

    def test_apply_updates_progress_file(self, tmp_path, capsys):
        """--apply mode updates the progress file correctly."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "track": "core_bootcamp",
                "modules_completed": [1, 2, 3, 4, 5, 6, 7],
                "current_module": None,
                "current_step": None,
                "step_history": {},
                "last_activity": "2025-07-15T10:00:00+00:00",
            }),
            encoding="utf-8",
        )

        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )

        main([
            "--from", "core_bootcamp",
            "--to", "advanced_topics",
            "--progress", str(progress_file),
            "--yaml", str(yaml_path),
            "--apply",
        ])

        updated = json.loads(progress_file.read_text(encoding="utf-8"))

        assert updated["track"] == "advanced_topics"
        assert updated["current_module"] == 8
        assert updated["current_step"] is None
        assert "last_activity" in updated


# ---------------------------------------------------------------------------
# Test error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Error handling tests for apply_switch and CLI."""

    def test_os_replace_failure_leaves_original_untouched(self, tmp_path):
        """Mock os.replace to raise OSError → verify original file is untouched."""
        progress_file = tmp_path / "progress.json"
        original_data = {
            "track": "core_bootcamp",
            "modules_completed": [1, 2, 3],
            "current_module": 4,
            "current_step": None,
            "step_history": {},
            "last_activity": "2025-07-15T10:00:00+00:00",
        }
        progress_file.write_text(json.dumps(original_data), encoding="utf-8")

        result = compute_switch(
            current_track="core_bootcamp",
            target_track="advanced_topics",
            modules_completed=[1, 2, 3],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        with patch("os.replace", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                apply_switch(progress_file, result)

        # Original file should be untouched
        after = json.loads(progress_file.read_text(encoding="utf-8"))
        assert after == original_data

    def test_missing_progress_file_with_apply(self, tmp_path):
        """Missing progress file with --apply → exit code 1."""
        progress_file = tmp_path / "nonexistent.json"
        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--from", "core_bootcamp",
                "--to", "advanced_topics",
                "--progress", str(progress_file),
                "--yaml", str(yaml_path),
                "--apply",
            ])

        assert exc_info.value.code == 1

    def test_malformed_json_in_progress_file(self, tmp_path):
        """Malformed JSON in progress file → exit code 1."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text("{ not valid json !!!", encoding="utf-8")

        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--from", "core_bootcamp",
                "--to", "advanced_topics",
                "--progress", str(progress_file),
                "--yaml", str(yaml_path),
            ])

        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Test steering file structure
# ---------------------------------------------------------------------------


class TestSteeringFileStructure:
    """Verify track-switching.md has correct structure."""

    @pytest.fixture()
    def steering_content(self) -> str:
        """Read the track-switching.md steering file."""
        path = Path(__file__).resolve().parent.parent / "steering" / "track-switching.md"
        return path.read_text(encoding="utf-8")

    def test_has_manual_inclusion_frontmatter(self, steering_content):
        """Steering file has 'inclusion: manual' in YAML frontmatter."""
        assert "inclusion: manual" in steering_content

    def test_contains_confirmation_gate(self, steering_content):
        """Steering file contains 👉 (confirmation gate)."""
        assert "\U0001f449" in steering_content

    def test_references_track_switcher_script(self, steering_content):
        """Steering file references track_switcher.py."""
        assert "track_switcher.py" in steering_content

    def test_contains_before_after_comparison(self, steering_content):
        """Steering file contains before/after comparison instructions."""
        assert "Before" in steering_content or "before" in steering_content
        assert "After" in steering_content or "after" in steering_content


# ---------------------------------------------------------------------------
# Test agent-instructions.md
# ---------------------------------------------------------------------------


class TestAgentInstructions:
    """Verify agent-instructions.md contains trigger phrases and steering reference."""

    @pytest.fixture()
    def instructions_content(self) -> str:
        """Read the agent-instructions.md file."""
        path = Path(__file__).resolve().parent.parent / "steering" / "agent-instructions.md"
        return path.read_text(encoding="utf-8")

    def test_contains_trigger_phrases(self, instructions_content):
        """agent-instructions.md contains all trigger phrases."""
        trigger_phrases = [
            "switch track",
            "change track",
            "move to core",
            "upgrade to advanced",
        ]
        for phrase in trigger_phrases:
            assert phrase in instructions_content, (
                f"Missing trigger phrase: '{phrase}'"
            )

    def test_references_track_switching_steering(self, instructions_content):
        """agent-instructions.md references track-switching.md."""
        assert "track-switching.md" in instructions_content
