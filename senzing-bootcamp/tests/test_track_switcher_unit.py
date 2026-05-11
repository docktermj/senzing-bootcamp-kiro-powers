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
    "quick_demo": [2, 3],
    "core_bootcamp": [1, 2, 3, 4, 5, 6, 7],
    "advanced_topics": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}

MODULE_NAMES: dict[int, str] = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "Quick Demo",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Load Data",
    7: "Query & Visualize",
    8: "Performance",
    9: "Security",
    10: "Monitoring",
    11: "Deployment",
}


# ---------------------------------------------------------------------------
# Task 6.2: Test advanced_topics → quick_demo with modules 1–7 completed
# ---------------------------------------------------------------------------


class TestAdvancedToQuickDemo:
    """Validates Requirement 4.3: switching from advanced_topics to quick_demo
    with modules 1-7 completed."""

    def test_extra_modules(self):
        """Extra should be [1, 4, 5, 6, 7] — completed modules NOT in quick_demo."""
        result = compute_switch(
            current_track="advanced_topics",
            target_track="quick_demo",
            modules_completed=[1, 2, 3, 4, 5, 6, 7],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.extra_modules == [1, 4, 5, 6, 7]

    def test_remaining_modules(self):
        """Remaining should be [] — both quick_demo modules (2, 3) are completed."""
        result = compute_switch(
            current_track="advanced_topics",
            target_track="quick_demo",
            modules_completed=[1, 2, 3, 4, 5, 6, 7],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == []


# ---------------------------------------------------------------------------
# Task 6.3: Test quick_demo → core_bootcamp with modules 2, 3 completed
# ---------------------------------------------------------------------------


class TestQuickDemoToCoreBootcamp:
    """Test switching from quick_demo to core_bootcamp with modules 2, 3 completed."""

    def test_remaining_modules(self):
        """Remaining should be [1, 4, 5, 6, 7] — core_bootcamp modules not yet done."""
        result = compute_switch(
            current_track="quick_demo",
            target_track="core_bootcamp",
            modules_completed=[2, 3],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == [1, 4, 5, 6, 7]

    def test_extra_modules(self):
        """Extra should be [] — modules 2, 3 are both in core_bootcamp."""
        result = compute_switch(
            current_track="quick_demo",
            target_track="core_bootcamp",
            modules_completed=[2, 3],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.extra_modules == []


# ---------------------------------------------------------------------------
# Task 6.4: Test edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases for compute_switch."""

    def test_empty_modules_completed(self):
        """Empty modules_completed → remaining = all target modules."""
        result = compute_switch(
            current_track="quick_demo",
            target_track="core_bootcamp",
            modules_completed=[],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == [1, 2, 3, 4, 5, 6, 7]
        assert result.extra_modules == []

    def test_all_target_modules_completed(self):
        """All target modules already completed → remaining=[], is_noop=False."""
        result = compute_switch(
            current_track="advanced_topics",
            target_track="quick_demo",
            modules_completed=[2, 3],
            track_definitions=TRACK_DEFINITIONS,
            module_names=MODULE_NAMES,
        )

        assert result.remaining_modules == []
        assert result.is_noop is False


# ---------------------------------------------------------------------------
# Task 6.5: Test CLI dry-run JSON output and --apply behavior
# ---------------------------------------------------------------------------


class TestCLI:
    """CLI dry-run and --apply behavior tests."""

    def test_dry_run_json_output(self, tmp_path, capsys):
        """Dry-run mode prints valid JSON with expected structure."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "track": "quick_demo",
                "modules_completed": [2, 3],
                "current_module": None,
                "current_step": None,
                "last_activity": "2025-07-15T10:00:00+00:00",
            }),
            encoding="utf-8",
        )

        yaml_path = Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"

        main([
            "--from", "quick_demo",
            "--to", "core_bootcamp",
            "--progress", str(progress_file),
            "--yaml", str(yaml_path),
        ])

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["current_track"] == "quick_demo"
        assert output["target_track"] == "core_bootcamp"
        assert output["is_noop"] is False
        assert output["remaining_modules"] == [1, 4, 5, 6, 7]
        assert output["extra_modules"] == []
        assert output["modules_completed"] == [2, 3]
        assert "remaining_module_names" in output
        assert "extra_module_names" in output

    def test_apply_updates_progress_file(self, tmp_path, capsys):
        """--apply mode updates the progress file correctly."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "track": "quick_demo",
                "modules_completed": [2, 3],
                "current_module": None,
                "current_step": None,
                "step_history": {},
                "last_activity": "2025-07-15T10:00:00+00:00",
            }),
            encoding="utf-8",
        )

        yaml_path = Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"

        main([
            "--from", "quick_demo",
            "--to", "core_bootcamp",
            "--progress", str(progress_file),
            "--yaml", str(yaml_path),
            "--apply",
        ])

        updated = json.loads(progress_file.read_text(encoding="utf-8"))

        assert updated["track"] == "core_bootcamp"
        assert updated["current_module"] == 1
        assert updated["current_step"] is None
        assert "last_activity" in updated


# ---------------------------------------------------------------------------
# Task 6.6: Test error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Error handling tests for apply_switch and CLI."""

    def test_os_replace_failure_leaves_original_untouched(self, tmp_path):
        """Mock os.replace to raise OSError → verify original file is untouched."""
        progress_file = tmp_path / "progress.json"
        original_data = {
            "track": "quick_demo",
            "modules_completed": [2, 3],
            "current_module": None,
            "current_step": None,
            "step_history": {},
            "last_activity": "2025-07-15T10:00:00+00:00",
        }
        progress_file.write_text(json.dumps(original_data), encoding="utf-8")

        result = compute_switch(
            current_track="quick_demo",
            target_track="core_bootcamp",
            modules_completed=[2, 3],
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
        yaml_path = Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--from", "quick_demo",
                "--to", "core_bootcamp",
                "--progress", str(progress_file),
                "--yaml", str(yaml_path),
                "--apply",
            ])

        assert exc_info.value.code == 1

    def test_malformed_json_in_progress_file(self, tmp_path):
        """Malformed JSON in progress file → exit code 1."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text("{ not valid json !!!", encoding="utf-8")

        yaml_path = Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--from", "quick_demo",
                "--to", "core_bootcamp",
                "--progress", str(progress_file),
                "--yaml", str(yaml_path),
            ])

        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Task 6.7: Test steering file structure
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
# Task 6.8: Test agent-instructions.md
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
            "go back to quick demo",
        ]
        for phrase in trigger_phrases:
            assert phrase in instructions_content, (
                f"Missing trigger phrase: '{phrase}'"
            )

    def test_references_track_switching_steering(self, instructions_content):
        """agent-instructions.md references track-switching.md."""
        assert "track-switching.md" in instructions_content
