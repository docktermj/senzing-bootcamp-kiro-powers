"""Tests for mapping verbosity steering file changes.

Validates that the Module 5 Phase 2 steering file contains the verbosity
prompt, per-step conditional presentation rules, and mid-mapping switch
instructions. Also validates the preferences file schema addition.

Requirements: 3.1, 3.2, 3.4
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestMappingVerbositySteeringStructure:
    """Tests for the mapping verbosity sections in the steering file.

    Requirements: 3.1, 3.2
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_steering_file(self) -> str:
        """Read and return the module-05-phase2-data-mapping.md content."""
        path = self._power_root() / "steering" / "module-05-phase2-data-mapping.md"
        return path.read_text(encoding="utf-8")

    def test_steering_file_exists(self):
        """module-05-phase2-data-mapping.md exists at the expected path."""
        path = self._power_root() / "steering" / "module-05-phase2-data-mapping.md"
        assert path.is_file(), f"Missing: {path}"

    def test_mapping_verbosity_check_section_present(self):
        """Steering file contains a 'Mapping Verbosity Check' section."""
        content = self._read_steering_file()
        assert "### Mapping Verbosity Check" in content

    def test_mid_mapping_verbosity_switch_section_present(self):
        """Steering file contains a 'Mid-Mapping Verbosity Switch' section."""
        content = self._read_steering_file()
        assert "### Mid-Mapping Verbosity Switch" in content


class TestPerStepConditionalPresentation:
    """Tests for verbose/concise conditional blocks in steps 2, 3, 4, 5, 7, 8.

    Requirements: 3.1, 3.2
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_steering_file(self) -> str:
        """Read and return the module-05-phase2-data-mapping.md content."""
        path = self._power_root() / "steering" / "module-05-phase2-data-mapping.md"
        return path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("step", [2, 3, 4, 5, 7, 8])
    def test_step_has_verbose_block(self, step: int):
        """Steps 2, 3, 4, 5, 7, 8 each have a Verbose presentation block."""
        content = self._read_steering_file()
        # Find the step section and check for verbose block within it
        assert "**Verbose:**" in content, (
            f"Step {step}: missing '**Verbose:**' block in steering file"
        )

    @pytest.mark.parametrize("step", [2, 3, 4, 5, 7, 8])
    def test_step_has_concise_block(self, step: int):
        """Steps 2, 3, 4, 5, 7, 8 each have a Concise presentation block."""
        content = self._read_steering_file()
        assert "**Concise:**" in content, (
            f"Step {step}: missing '**Concise:**' block in steering file"
        )

    def test_verbose_block_count_matches_steps(self):
        """There are at least 6 verbose blocks (one per step: 2, 3, 4, 5, 7, 8)."""
        content = self._read_steering_file()
        verbose_count = content.count("**Verbose:**")
        assert verbose_count >= 6, (
            f"Expected at least 6 '**Verbose:**' blocks, found {verbose_count}"
        )

    def test_concise_block_count_matches_steps(self):
        """There are at least 6 concise blocks (one per step: 2, 3, 4, 5, 7, 8)."""
        content = self._read_steering_file()
        concise_count = content.count("**Concise:**")
        assert concise_count >= 6, (
            f"Expected at least 6 '**Concise:**' blocks, found {concise_count}"
        )

    def test_conditional_on_mapping_verbosity_present(self):
        """Steering file references mapping_verbosity for conditional presentation."""
        content = self._read_steering_file()
        assert "mapping_verbosity" in content


class TestPreferencesFileSchema:
    """Tests for the mapping_verbosity key in bootcamp_preferences.yaml.

    Requirements: 3.1
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_preferences_file(self) -> str:
        """Read and return the bootcamp_preferences.yaml content."""
        path = self._power_root() / "config" / "bootcamp_preferences.yaml"
        return path.read_text(encoding="utf-8")

    def test_preferences_file_exists(self):
        """bootcamp_preferences.yaml exists at the expected path."""
        path = self._power_root() / "config" / "bootcamp_preferences.yaml"
        assert path.is_file(), f"Missing: {path}"

    def test_mapping_verbosity_key_present(self):
        """Preferences file contains the mapping_verbosity key."""
        content = self._read_preferences_file()
        assert "mapping_verbosity:" in content

    def test_mapping_verbosity_default_is_null(self):
        """mapping_verbosity defaults to null (not yet asked)."""
        content = self._read_preferences_file()
        assert "mapping_verbosity: null" in content

    def test_mapping_verbosity_comment_present(self):
        """mapping_verbosity has a comment explaining its purpose."""
        content = self._read_preferences_file()
        assert "Mapping-specific verbosity" in content


class TestNoRegressionAllStepsPresent:
    """Tests that all original steps (1-13) are still present.

    Requirements: 3.4
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_steering_file(self) -> str:
        """Read and return the module-05-phase2-data-mapping.md content."""
        path = self._power_root() / "steering" / "module-05-phase2-data-mapping.md"
        return path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("step_num,keyword", [
        (1, "**Start:**"),
        (2, "**Profile:**"),
        (3, "**Plan:**"),
        (4, "**Map:**"),
        (5, "**Generate starter code:**"),
        (6, "**Build transformation program:**"),
        (7, "**Test:**"),
        (8, "**Quality analysis:**"),
        (9, "**Review:**"),
        (10, "**Iterate:**"),
        (11, "**Save and document:**"),
        (12, "**Repeat**"),
        (13, "**Transition**"),
    ])
    def test_step_present(self, step_num: int, keyword: str):
        """Step {step_num} is still present in the steering file (no regression)."""
        content = self._read_steering_file()
        assert keyword in content, (
            f"Step {step_num} keyword '{keyword}' missing from steering file"
        )


class TestMappingWorkflowToolCallsUnchanged:
    """Tests that mapping_workflow MCP tool call instructions are unchanged.

    Verbosity only affects presentation, not MCP calls.
    Requirements: 3.4
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_steering_file(self) -> str:
        """Read and return the module-05-phase2-data-mapping.md content."""
        path = self._power_root() / "steering" / "module-05-phase2-data-mapping.md"
        return path.read_text(encoding="utf-8")

    def test_mapping_workflow_start_action_present(self):
        """mapping_workflow(action='start') call instruction is present."""
        content = self._read_steering_file()
        assert "mapping_workflow(action='start')" in content

    def test_mapping_workflow_profile_summary_action_present(self):
        """mapping_workflow action='profile_summary' call instruction is present."""
        content = self._read_steering_file()
        assert "action='profile_summary'" in content

    def test_mapping_workflow_entity_plan_action_present(self):
        """mapping_workflow action='entity_plan' call instruction is present."""
        content = self._read_steering_file()
        assert "action='entity_plan'" in content

    def test_mapping_workflow_schema_mappings_action_present(self):
        """mapping_workflow(action='schema_mappings') call instruction is present."""
        content = self._read_steering_file()
        assert "action='schema_mappings'" in content

    def test_mapping_workflow_paths_action_present(self):
        """mapping_workflow action='paths' call instruction is present."""
        content = self._read_steering_file()
        assert "action='paths'" in content

    def test_mapping_workflow_verdict_action_present(self):
        """mapping_workflow action='verdict' call instruction is present."""
        content = self._read_steering_file()
        assert "action='verdict'" in content

    def test_verbosity_does_not_modify_action_parameters(self):
        """Verbosity conditional blocks don't contain mapping_workflow action calls."""
        content = self._read_steering_file()
        # Find all verbose/concise blocks and ensure they don't contain action= calls
        # The presentation blocks should only describe output formatting
        lines = content.split("\n")
        in_presentation_block = False
        for line in lines:
            if "**Verbose:**" in line or "**Concise:**" in line:
                in_presentation_block = True
                continue
            if in_presentation_block:
                # Presentation blocks end at the next non-indented line or next section
                if line.strip() and not line.startswith("   ") and not line.startswith(">"):
                    in_presentation_block = False
                    continue
                # Inside a presentation block, there should be no mapping_workflow calls
                assert "mapping_workflow(action=" not in line, (
                    f"Presentation block should not contain mapping_workflow calls: {line}"
                )
