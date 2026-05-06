"""Tests for license step mandatory gate in Module 2 steering file.

Validates that module-02-sdk-setup.md correctly marks Step 5 (Configure License)
as a mandatory gate that is never skipped, even when the SDK is already installed.
The skip-ahead logic in Step 1 must explicitly require Step 5 as a mandatory stop.

Feature: workflow-improvements (license step mandatory gate)
Validates: Requirements 2.1, 2.2, 2.3
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

_MODULE_02 = _POWER_ROOT / "steering" / "module-02-sdk-setup.md"


def _read(path: Path) -> str:
    """Read a file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def _extract_frontmatter(content: str) -> str | None:
    """Extract YAML frontmatter from markdown content.

    Returns:
        The frontmatter string (without delimiters), or None if not found.
    """
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    return match.group(1) if match else None


def _extract_step_5_section(content: str) -> str:
    """Extract the Step 5 section from the module content.

    Returns:
        The text from the Step 5 heading to the next same-level heading.
    """
    match = re.search(r"(## Step 5:.*?)(?=\n## Step \d|$)", content, re.DOTALL)
    assert match is not None, "Step 5 section not found in module-02-sdk-setup.md"
    return match.group(1)


def _extract_step_1_section(content: str) -> str:
    """Extract the Step 1 section from the module content.

    Returns:
        The text from the Step 1 heading to the next same-level heading.
    """
    match = re.search(r"(## Step 1:.*?)(?=\n## Step \d|$)", content, re.DOTALL)
    assert match is not None, "Step 1 section not found in module-02-sdk-setup.md"
    return match.group(1)


# ═══════════════════════════════════════════════════════════════════════════
# 2.3a — Step 5 mandatory gate marker
# Validates: Requirement 2.1
# ═══════════════════════════════════════════════════════════════════════════


class TestStep5MandatoryGate:
    """Verify Step 5 contains the mandatory gate marker and retains existing markers."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_MODULE_02)
        self.step_5 = _extract_step_5_section(self.content)

    def test_mandatory_gate_marker_present(self) -> None:
        """Step 5 contains the ⛔ MANDATORY GATE marker."""
        assert "⛔ MANDATORY GATE" in self.step_5

    def test_never_skip_instruction(self) -> None:
        """Step 5 contains 'Never skip this step, even if the SDK is already installed'."""
        assert "Never skip this step, even if the SDK is already installed" in self.step_5

    def test_license_question_retained(self) -> None:
        """Step 5 still contains the 👉 question about license."""
        assert "👉" in self.step_5
        lower = self.step_5.lower()
        assert "license" in lower

    def test_stop_marker_retained(self) -> None:
        """Step 5 still contains a STOP marker requiring bootcamper response."""
        assert "STOP" in self.step_5


# ═══════════════════════════════════════════════════════════════════════════
# 2.3b — Step 1 skip-ahead logic requires Step 5 as mandatory
# Validates: Requirements 2.2, 2.3
# ═══════════════════════════════════════════════════════════════════════════


class TestStep1SkipAheadLogic:
    """Verify Step 1 skip-ahead logic explicitly requires Step 5 as mandatory."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_MODULE_02)
        self.step_1 = _extract_step_1_section(self.content)

    def test_step_5_marked_mandatory_in_skip_logic(self) -> None:
        """Step 1 skip-ahead logic contains 'MANDATORY' in reference to Step 5."""
        assert "MANDATORY" in self.step_1

    def test_required_stops_callout_present(self) -> None:
        """Step 1 contains a 'Required Stops' callout."""
        assert "Required Stops" in self.step_1

    def test_required_stops_lists_step_4(self) -> None:
        """'Required Stops' callout lists Step 4."""
        # Find the Required Stops section within Step 1
        stops_pos = self.step_1.find("Required Stops")
        assert stops_pos != -1
        stops_section = self.step_1[stops_pos:]
        assert "Step 4" in stops_section

    def test_required_stops_lists_step_5(self) -> None:
        """'Required Stops' callout lists Step 5."""
        # Find the Required Stops section within Step 1
        stops_pos = self.step_1.find("Required Stops")
        assert stops_pos != -1
        stops_section = self.step_1[stops_pos:]
        assert "Step 5" in stops_section


# ═══════════════════════════════════════════════════════════════════════════
# 2.3c — YAML frontmatter and inclusion mode integrity
# Validates: Requirement 2.3 (structural integrity)
# ═══════════════════════════════════════════════════════════════════════════


class TestModule02FrontmatterIntegrity:
    """Verify module-02-sdk-setup.md retains valid YAML frontmatter and inclusion mode."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_MODULE_02)

    def test_has_yaml_frontmatter(self) -> None:
        """module-02-sdk-setup.md has valid YAML frontmatter."""
        frontmatter = _extract_frontmatter(self.content)
        assert frontmatter is not None, "No YAML frontmatter found"

    def test_inclusion_manual(self) -> None:
        """module-02-sdk-setup.md has inclusion: manual."""
        frontmatter = _extract_frontmatter(self.content)
        assert frontmatter is not None
        assert "inclusion: manual" in frontmatter
