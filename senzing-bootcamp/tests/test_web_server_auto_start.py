"""Tests for web server auto-start steering file changes.

Validates that the visualization steering files correctly instruct the agent
to start the web server as a background process using controlBashProcess,
rather than telling the bootcamper to start it manually.

Feature: workflow-improvements (web server auto-start)
Validates: Requirements 1.6, 1.7
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

_VIZ_WEB_SERVICE = _POWER_ROOT / "steering" / "visualization-web-service.md"
_VIZ_GUIDE = _POWER_ROOT / "steering" / "visualization-guide.md"


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


# ═══════════════════════════════════════════════════════════════════════════
# 1.3a — visualization-web-service.md auto-start content
# Validates: Requirement 1.6
# ═══════════════════════════════════════════════════════════════════════════


class TestVizWebServiceAutoStart:
    """Verify visualization-web-service.md has auto-start instructions."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_VIZ_WEB_SERVICE)

    def test_contains_control_bash_process(self) -> None:
        """File contains controlBashProcess instruction for starting the server."""
        assert "controlBashProcess" in self.content

    def test_contains_server_auto_start_section(self) -> None:
        """File contains a 'Server Auto-Start' section header."""
        assert "Server Auto-Start" in self.content

    def test_no_background_process_prohibition(self) -> None:
        """File does NOT contain the old prohibition against background processes."""
        lower = self.content.lower()
        assert "shall not start the server as a background process" not in lower

    def test_fallback_port_conflict(self) -> None:
        """File documents fallback behavior for port conflicts."""
        lower = self.content.lower()
        assert "port conflict" in lower or "address already in use" in lower

    def test_fallback_missing_dependencies(self) -> None:
        """File documents fallback behavior for missing dependencies."""
        lower = self.content.lower()
        assert "missing dependencies" in lower or "modulenotfounderror" in lower

    def test_get_process_output_verification(self) -> None:
        """File mentions getProcessOutput for verifying server startup."""
        assert "getProcessOutput" in self.content

    def test_presents_url_after_start(self) -> None:
        """File instructs presenting the localhost URL after auto-start."""
        assert "http://localhost:" in self.content or "http://localhost:8080" in self.content

    def test_manual_restart_command_for_reference(self) -> None:
        """File includes manual restart command for bootcamper reference."""
        lower = self.content.lower()
        assert "manual" in lower and ("restart" in lower or "start command" in lower)


# ═══════════════════════════════════════════════════════════════════════════
# 1.3b — visualization-guide.md delivery sequence auto-start
# Validates: Requirement 1.7
# ═══════════════════════════════════════════════════════════════════════════


class TestVizGuideDeliverySequence:
    """Verify visualization-guide.md delivery sequence includes auto-start."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_VIZ_GUIDE)

    def test_delivery_sequence_mentions_control_bash_process(self) -> None:
        """Web Service Delivery Sequence mentions controlBashProcess."""
        # Find the delivery sequence section
        seq_pos = self.content.find("Web Service Delivery Sequence")
        assert seq_pos != -1, "Web Service Delivery Sequence section not found"
        section = self.content[seq_pos:]
        assert "controlBashProcess" in section

    def test_delivery_sequence_mentions_auto_start(self) -> None:
        """Delivery sequence mentions auto-start or background process."""
        seq_pos = self.content.find("Web Service Delivery Sequence")
        assert seq_pos != -1
        section = self.content[seq_pos:]
        lower = section.lower()
        assert "background process" in lower or "auto" in lower

    def test_delivery_sequence_fallback_on_failure(self) -> None:
        """Delivery sequence mentions fallback on failure."""
        seq_pos = self.content.find("Web Service Delivery Sequence")
        assert seq_pos != -1
        section = self.content[seq_pos:]
        lower = section.lower()
        assert "fallback" in lower or "fail" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 1.3c — YAML frontmatter and inclusion mode integrity
# Validates: Requirements 1.6, 1.7 (structural integrity)
# ═══════════════════════════════════════════════════════════════════════════


class TestFrontmatterIntegrity:
    """Verify both files retain valid YAML frontmatter and inclusion mode."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.web_service_content = _read(_VIZ_WEB_SERVICE)
        self.guide_content = _read(_VIZ_GUIDE)

    def test_web_service_has_yaml_frontmatter(self) -> None:
        """visualization-web-service.md has valid YAML frontmatter."""
        frontmatter = _extract_frontmatter(self.web_service_content)
        assert frontmatter is not None, "No YAML frontmatter found"

    def test_web_service_inclusion_manual(self) -> None:
        """visualization-web-service.md has inclusion: manual."""
        frontmatter = _extract_frontmatter(self.web_service_content)
        assert frontmatter is not None
        assert "inclusion: manual" in frontmatter

    def test_guide_has_yaml_frontmatter(self) -> None:
        """visualization-guide.md has valid YAML frontmatter."""
        frontmatter = _extract_frontmatter(self.guide_content)
        assert frontmatter is not None, "No YAML frontmatter found"

    def test_guide_inclusion_manual(self) -> None:
        """visualization-guide.md has inclusion: manual."""
        frontmatter = _extract_frontmatter(self.guide_content)
        assert frontmatter is not None
        assert "inclusion: manual" in frontmatter
