#!/usr/bin/env python3
"""Tests for MCP health check integration.

Validates:
- preflight.py accepts --mcp flag without error
- session-resume.md contains MCP Health Check section
- onboarding-flow.md contains MCP Health Check section
- Warning message template contains required elements
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_REPO_ROOT / "scripts")
_STEERING_DIR = _REPO_ROOT / "steering"

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


class TestPreflightMCPFlag:
    """Unit tests: preflight.py accepts --mcp flag without error."""

    def test_mcp_flag_accepted_via_subprocess(self):
        """preflight.py --mcp runs without error (exit code 0)."""
        result = subprocess.run(
            [sys.executable, os.path.join(_SCRIPTS_DIR, "preflight.py"), "--mcp"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"preflight.py --mcp exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_mcp_flag_output_contains_server_info(self):
        """preflight.py --mcp output mentions the MCP server name."""
        result = subprocess.run(
            [sys.executable, os.path.join(_SCRIPTS_DIR, "preflight.py"), "--mcp"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "senzing-mcp-server" in result.stdout, (
            f"Expected server name in output.\nstdout: {result.stdout}"
        )

    def test_mcp_flag_mentions_agent_requirement(self):
        """preflight.py --mcp output explains that full health check requires the agent."""
        result = subprocess.run(
            [sys.executable, os.path.join(_SCRIPTS_DIR, "preflight.py"), "--mcp"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "agent" in result.stdout.lower(), (
            f"Expected mention of agent requirement.\nstdout: {result.stdout}"
        )

    def test_mcp_flag_via_main_function(self):
        """preflight.main(['--mcp']) returns 0."""
        from preflight import main
        exit_code = main(["--mcp"])
        assert exit_code == 0


class TestSessionResumeMCPSection:
    """Steering structure test: session-resume.md contains MCP Health Check section."""

    @pytest.fixture()
    def session_resume_content(self) -> str:
        path = _STEERING_DIR / "session-resume.md"
        return path.read_text(encoding="utf-8")

    def test_contains_mcp_health_check_heading(self, session_resume_content: str):
        """session-resume.md has a 'Step 2d: MCP Health Check' heading."""
        assert "## Step 2d: MCP Health Check" in session_resume_content

    def test_contains_search_docs_probe(self, session_resume_content: str):
        """session-resume.md references the search_docs probe call."""
        assert 'search_docs(query="health check", version="current")' in session_resume_content

    def test_contains_mcp_status_file_reference(self, session_resume_content: str):
        """session-resume.md references config/.mcp_status."""
        assert "config/.mcp_status" in session_resume_content

    def test_contains_timeout_specification(self, session_resume_content: str):
        """session-resume.md specifies a 10-second timeout."""
        assert "10-second timeout" in session_resume_content or "10 seconds" in session_resume_content

    def test_section_between_2c_and_2e(self, session_resume_content: str):
        """Step 2d appears after Step 2c and before Step 2e."""
        pos_2c = session_resume_content.find("## Step 2c:")
        pos_2d = session_resume_content.find("## Step 2d: MCP Health Check")
        pos_2e = session_resume_content.find("## Step 2e:")
        assert pos_2c < pos_2d < pos_2e, (
            f"Expected Step 2c ({pos_2c}) < Step 2d ({pos_2d}) < Step 2e ({pos_2e})"
        )


class TestOnboardingFlowMCPSection:
    """Steering structure test: onboarding-flow.md contains MCP Health Check section."""

    @pytest.fixture()
    def onboarding_content(self) -> str:
        path = _STEERING_DIR / "onboarding-flow.md"
        return path.read_text(encoding="utf-8")

    def test_contains_mcp_health_check_heading(self, onboarding_content: str):
        """onboarding-flow.md has a '0b. MCP Health Check' heading."""
        assert "## 0b. MCP Health Check" in onboarding_content

    def test_contains_search_docs_probe(self, onboarding_content: str):
        """onboarding-flow.md references the search_docs probe call."""
        assert 'search_docs(query="health check", version="current")' in onboarding_content

    def test_contains_first_time_user_explanation(self, onboarding_content: str):
        """onboarding-flow.md explains what MCP provides for first-time users."""
        assert "generates SDK code" in onboarding_content or "generate working Senzing code" in onboarding_content

    def test_section_before_step_1(self, onboarding_content: str):
        """Step 0b appears before Step 1 (Directory Structure)."""
        pos_0b = onboarding_content.find("## 0b. MCP Health Check")
        pos_1 = onboarding_content.find("## 1. Directory Structure")
        assert pos_0b < pos_1, (
            f"Expected Step 0b ({pos_0b}) before Step 1 ({pos_1})"
        )


class TestWarningMessageTemplate:
    """Unit test: warning message in session-resume.md contains required elements."""

    @pytest.fixture()
    def session_resume_content(self) -> str:
        path = _STEERING_DIR / "session-resume.md"
        return path.read_text(encoding="utf-8")

    def test_contains_offline_mode_reference(self, session_resume_content: str):
        """Warning message references docs/guides/OFFLINE_MODE.md."""
        assert "docs/guides/OFFLINE_MODE.md" in session_resume_content

    def test_contains_unavailable_features(self, session_resume_content: str):
        """Warning message lists unavailable features."""
        assert "Code generation" in session_resume_content
        assert "fact lookup" in session_resume_content
        assert "example search" in session_resume_content

    def test_contains_available_alternatives(self, session_resume_content: str):
        """Warning message lists what the bootcamper can still do."""
        assert "Review existing artifacts" in session_resume_content
        assert "documentation" in session_resume_content
        assert "plan" in session_resume_content.lower()

    def test_contains_offline_mode_question(self, session_resume_content: str):
        """Warning message asks about continuing in offline mode."""
        assert "continue in offline mode" in session_resume_content

    def test_contains_mid_session_recovery(self, session_resume_content: str):
        """session-resume.md includes mid-session recovery instructions."""
        assert "Mid-Session Recovery" in session_resume_content
        assert "MCP server is back online" in session_resume_content
