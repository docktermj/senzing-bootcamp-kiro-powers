"""Tests for the Self-Answering Reinforcement feature.

Validates that forbidden output patterns are documented, STOP markers
exist after 👉 questions, and anti-fabrication instructions are in place.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"


class TestForbiddenPatterns:
    """Verify agent-instructions.md contains 'Human:' in forbidden patterns."""

    @pytest.fixture()
    def agent_instructions(self) -> str:
        return (_STEERING_DIR / "agent-instructions.md").read_text(encoding="utf-8")

    def test_contains_human_colon_forbidden(self, agent_instructions: str) -> None:
        """agent-instructions.md lists 'Human:' as a forbidden output pattern."""
        assert '"Human:"' in agent_instructions or "'Human:'" in agent_instructions

    def test_contains_forbidden_output_patterns_section(self, agent_instructions: str) -> None:
        """agent-instructions.md has a FORBIDDEN output patterns rule."""
        assert "FORBIDDEN output patterns" in agent_instructions


class TestOnboardingStopMarkers:
    """Verify onboarding-flow.md has 🛑 STOP after 👉 questions."""

    @pytest.fixture()
    def onboarding(self) -> str:
        return (_STEERING_DIR / "onboarding-flow.md").read_text(encoding="utf-8")

    def test_stop_after_verbosity_question(self, onboarding: str) -> None:
        """🛑 STOP exists after the verbosity preference 👉 question."""
        idx = onboarding.find("how much detail they want")
        assert idx != -1
        after = onboarding[idx:idx + 500]
        assert "🛑" in after

    def test_stop_after_comprehension_check(self, onboarding: str) -> None:
        """🛑 STOP exists after the comprehension check 👉 question."""
        idx = onboarding.find("Does everything so far makes sense")
        assert idx != -1
        after = onboarding[idx:idx + 200]
        assert "🛑" in after


class TestAskBootcamperAntiFabrication:
    """Verify ask-bootcamper hook contains anti-fabrication instruction."""

    @pytest.fixture()
    def hook_prompt(self) -> str:
        path = _HOOKS_DIR / "ask-bootcamper.kiro.hook"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["then"]["prompt"]

    def test_contains_human_colon_prohibition(self, hook_prompt: str) -> None:
        """Hook prompt prohibits generating 'Human:' text."""
        assert "Human:" in hook_prompt
        assert "NEVER" in hook_prompt


class TestStopMarkerProperty:
    """Property test: steering files with 👉 questions have 🛑 STOP nearby."""

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_pointing_questions_have_stop_markers(self, data: st.DataObject) -> None:
        """For key steering files, 👉 questions outside code blocks have 🛑 within 5 lines."""
        # Test against onboarding-flow.md (the primary affected file)
        content = (_STEERING_DIR / "onboarding-flow.md").read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find all 👉 questions outside code blocks
        in_code_block = False
        pointing_questions: list[int] = []
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if "👉" in line and "?" in line:
                pointing_questions.append(i)

        if not pointing_questions:
            return

        # Pick a random question
        idx = data.draw(st.sampled_from(pointing_questions))

        # Check for 🛑 or ⛔ within 5 non-blank lines after
        found_marker = False
        non_blank_seen = 0
        for scan_idx in range(idx + 1, min(len(lines), idx + 10)):
            scan_line = lines[scan_idx]
            if not scan_line.strip():
                continue
            non_blank_seen += 1
            if "🛑" in scan_line or "⛔" in scan_line:
                found_marker = True
                break
            if non_blank_seen >= 5:
                break

        assert found_marker, (
            f"Line {idx + 1} has a 👉 question without 🛑/⛔ within 5 lines:\n"
            f"  {lines[idx].strip()[:80]}"
        )
