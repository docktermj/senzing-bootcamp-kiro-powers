"""Unit tests for mapping checkpoint resume steering content.

Verifies that session-resume.md contains mapping checkpoint detection,
three-option resume offers, checkpoint validation logic, and that
agent-instructions.md cross-references the checkpoint resume behavior.

Feature: mapping-checkpoint-resume
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths to steering files under test
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
SESSION_RESUME_PATH: Path = _STEERING_DIR / "session-resume.md"
AGENT_INSTRUCTIONS_PATH: Path = _STEERING_DIR / "agent-instructions.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _extract_subsection(content: str, heading: str) -> str:
    """Extract content under a ### heading until the next heading of same or higher level.

    Args:
        content: Full markdown content.
        heading: The heading text (without the ### prefix).

    Returns:
        The subsection content including the heading line.
    """
    pattern = rf"^(### {re.escape(heading)}.*)$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    # Find the next ## or ### heading after this one
    next_heading = re.search(r"^#{2,3} ", content[match.end():], re.MULTILINE)
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(content)
    return content[start:end]


# ---------------------------------------------------------------------------
# Tests: 4.2 Step 1 Checkpoint Detection
# ---------------------------------------------------------------------------


class TestStep1CheckpointDetection:
    """Tests that Step 1 mentions mapping_state file detection.

    Validates: Requirements 1, 8
    """

    def test_step1_mentions_mapping_state_files(self) -> None:
        """Step 1 references mapping_state checkpoint files."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 1: Read All State Files")
        assert section, "Step 1: Read All State Files section not found"
        assert "mapping_state" in section, (
            "Step 1 must mention mapping_state file detection"
        )

    def test_step1_mentions_mapping_state_glob_pattern(self) -> None:
        """Step 1 references the mapping_state_*.json glob pattern."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 1: Read All State Files")
        assert section, "Step 1: Read All State Files section not found"
        assert "mapping_state_*.json" in section, (
            "Step 1 must mention the mapping_state_*.json glob pattern"
        )

    def test_step1_indicates_mid_mapping_detection(self) -> None:
        """Step 1 indicates that finding mapping_state means mid-mapping."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 1: Read All State Files")
        assert section, "Step 1: Read All State Files section not found"
        assert "mid-mapping" in section.lower() or "in-progress" in section.lower(), (
            "Step 1 must indicate that mapping_state files mean "
            "the user was mid-mapping"
        )


# ---------------------------------------------------------------------------
# Tests: 4.3 Step 3 Resume Options
# ---------------------------------------------------------------------------


class TestStep3ResumeOptions:
    """Tests that Step 3 contains mapping checkpoint display and resume options.

    Validates: Requirements 2, 3, 6
    """

    def test_step3_contains_mapping_checkpoint_display_instructions(self) -> None:
        """Step 3 contains instructions for displaying mapping checkpoint info."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 3: Summarize and Confirm")
        assert section, "Step 3: Summarize and Confirm section not found"
        section_lower = section.lower()
        assert "mapping checkpoint" in section_lower or "mapping_state" in section_lower, (
            "Step 3 must contain mapping checkpoint display instructions"
        )

    def test_step3_contains_all_three_options(self) -> None:
        """Step 3 presents all three options: resume, restart, skip."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 3: Summarize and Confirm")
        assert section, "Step 3: Summarize and Confirm section not found"
        section_lower = section.lower()
        assert "resume" in section_lower, (
            "Step 3 must contain a 'Resume' option"
        )
        assert "restart" in section_lower, (
            "Step 3 must contain a 'Restart' option"
        )
        assert "skip" in section_lower, (
            "Step 3 must contain a 'Skip' option"
        )

    def test_step3_mentions_multiple_data_sources_handling(self) -> None:
        """Step 3 mentions handling multiple data sources/checkpoints."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 3: Summarize and Confirm")
        assert section, "Step 3: Summarize and Confirm section not found"
        section_lower = section.lower()
        assert "multiple" in section_lower and (
            "checkpoint" in section_lower or "data source" in section_lower
        ), (
            "Step 3 must mention handling multiple data sources/checkpoints"
        )


# ---------------------------------------------------------------------------
# Tests: 4.4 Step 4 Validation
# ---------------------------------------------------------------------------


class TestStep4Validation:
    """Tests that Step 4 contains checkpoint validation logic.

    Validates: Requirements 4, 5
    """

    def test_step4_contains_mapping_workflow_status_action(self) -> None:
        """Step 4 references mapping_workflow with action='status'."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 4: Load the Right Module Steering")
        assert section, "Step 4: Load the Right Module Steering section not found"
        assert "mapping_workflow" in section, (
            "Step 4 must reference mapping_workflow"
        )
        assert "action='status'" in section or 'action="status"' in section, (
            "Step 4 must reference mapping_workflow with action='status'"
        )

    def test_step4_contains_corrupted_checkpoint_handling(self) -> None:
        """Step 4 contains corrupted checkpoint handling instructions."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 4: Load the Right Module Steering")
        assert section, "Step 4: Load the Right Module Steering section not found"
        section_lower = section.lower()
        assert "corrupted" in section_lower, (
            "Step 4 must mention corrupted checkpoint handling"
        )
        assert "cannot be read" in section_lower, (
            "Step 4 must mention that corrupted checkpoints cannot be read"
        )

    def test_step4_contains_invalid_state_handling_with_restart(self) -> None:
        """Step 4 contains invalid state handling with restart offer."""
        content = _read_file(SESSION_RESUME_PATH)
        section = _extract_section(content, "Step 4: Load the Right Module Steering")
        assert section, "Step 4: Load the Right Module Steering section not found"
        section_lower = section.lower()
        has_invalid_or_outdated = (
            "invalid" in section_lower or "outdated" in section_lower
        )
        assert has_invalid_or_outdated, (
            "Step 4 must mention invalid or outdated state handling"
        )
        assert "restart" in section_lower, (
            "Step 4 must offer to restart when state is invalid"
        )


# ---------------------------------------------------------------------------
# Tests: 4.5 Agent Instructions Cross-Reference
# ---------------------------------------------------------------------------


class TestAgentInstructionsCrossReference:
    """Tests that agent-instructions.md State & Progress section cross-references checkpoint resume.

    Validates: Requirements 7, 8
    """

    def test_state_progress_references_session_resume(self) -> None:
        """State & Progress section references session resume checkpoint behavior."""
        content = _read_file(AGENT_INSTRUCTIONS_PATH)
        section = _extract_section(content, "State & Progress")
        assert section, "## State & Progress section not found in agent-instructions.md"
        has_session_resume_ref = (
            "session resume" in section.lower() or "session-resume.md" in section
        )
        assert has_session_resume_ref, (
            "State & Progress section must reference session resume checkpoint behavior "
            "(mention 'session resume' or 'session-resume.md')"
        )

    def test_state_progress_references_mapping_workflow_status(self) -> None:
        """State & Progress section references mapping_workflow with action='status'."""
        content = _read_file(AGENT_INSTRUCTIONS_PATH)
        section = _extract_section(content, "State & Progress")
        assert section, "## State & Progress section not found in agent-instructions.md"
        has_status_ref = (
            "action='status'" in section or 'action="status"' in section
        )
        assert has_status_ref, (
            "State & Progress section must reference mapping_workflow(action='status')"
        )
