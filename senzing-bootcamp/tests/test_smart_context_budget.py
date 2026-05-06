#!/usr/bin/env python3
"""Tests for the Smarter Context Budget Warnings feature.

Validates that agent-instructions.md contains the Context Budget Management
section and that measure_steering.py supports the --simulate flag.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_STEERING_DIR = _ROOT / "senzing-bootcamp" / "steering"
_SCRIPTS_DIR = _ROOT / "senzing-bootcamp" / "scripts"


class TestAgentInstructionsContextBudget:
    """Verify context budget management content exists in steering files."""

    @pytest.fixture()
    def context_management(self) -> str:
        path = _STEERING_DIR / "agent-context-management.md"
        return path.read_text(encoding="utf-8")

    @pytest.fixture()
    def agent_instructions(self) -> str:
        path = _STEERING_DIR / "agent-instructions.md"
        return path.read_text(encoding="utf-8")

    def test_contains_context_budget_management_section(self, context_management: str) -> None:
        assert "## Context Budget Management" in context_management

    def test_documents_six_retention_priority_tiers(self, context_management: str) -> None:
        # Check all 6 tiers are mentioned
        assert "`agent-instructions.md` — never unload" in context_management
        assert "Current module steering" in context_management
        assert "Language file" in context_management
        assert "`conversation-protocol.md` — never unload" in context_management
        assert "troubleshooting" in context_management.lower()
        assert "Completed module steering" in context_management

    def test_documents_warn_threshold_behavior(self, context_management: str) -> None:
        assert "warn threshold (60%)" in context_management.lower() or \
               "At warn threshold (60%)" in context_management

    def test_documents_critical_threshold_behavior(self, context_management: str) -> None:
        assert "critical threshold (80%)" in context_management.lower() or \
               "At critical threshold (80%)" in context_management

    def test_uses_percentage_not_absolute_in_budget_section(self, agent_instructions: str) -> None:
        # The Context Budget section should use percentages, not absolute values
        budget_section_start = agent_instructions.find("## Context Budget")
        budget_section = agent_instructions[budget_section_start:]
        assert "60% of context budget" in budget_section
        assert "80% of context budget" in budget_section
        # Should NOT contain old absolute references
        assert "120k" not in budget_section
        assert "160k" not in budget_section


class TestMeasureSteeringSimulate:
    """Verify measure_steering.py supports --simulate flag."""

    def test_simulate_flag_accepted(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "measure_steering.py"), "--simulate"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        assert result.returncode == 0

    def test_simulate_output_contains_peak_without_unloading(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "measure_steering.py"), "--simulate"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        assert "Peak without unloading" in result.stdout

    def test_simulate_output_contains_peak_with_unloading(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "measure_steering.py"), "--simulate"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        assert "Peak with unloading" in result.stdout

    def test_simulate_peak_with_unloading_leq_without(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "measure_steering.py"), "--simulate"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        import re
        peaks = re.findall(r"Peak (?:without|with) unloading:\s+([\d,]+) tokens", result.stdout)
        assert len(peaks) == 2
        peak_without = int(peaks[0].replace(",", ""))
        peak_with = int(peaks[1].replace(",", ""))
        assert peak_with <= peak_without

    def test_simulate_token_counts_non_negative(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "measure_steering.py"), "--simulate"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        import re
        # Extract all percentage values
        pcts = re.findall(r"([\d.]+)%", result.stdout)
        for pct in pcts:
            assert float(pct) >= 0
