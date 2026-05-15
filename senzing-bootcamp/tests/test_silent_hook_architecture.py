"""Tests for the Silent Hook Architecture Fix.

Validates that the ask-bootcamper hook uses the minimal-token response
pattern instead of "PRODUCE NO OUTPUT" instructions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"


class TestAskBootcamperSilencePattern:
    """Verify ask-bootcamper hook uses DEFAULT OUTPUT: . pattern."""

    @pytest.fixture()
    def hook_data(self) -> dict:
        path = _HOOKS_DIR / "ask-bootcamper.kiro.hook"
        return json.loads(path.read_text(encoding="utf-8"))

    @pytest.fixture()
    def hook_prompt(self, hook_data: dict) -> str:
        return hook_data["then"]["prompt"]

    def test_contains_default_output_instruction(self, hook_prompt: str) -> None:
        """Hook prompt contains 'DEFAULT OUTPUT: .' instruction."""
        assert "DEFAULT OUTPUT: ." in hook_prompt

    def test_does_not_contain_produce_no_output(self, hook_prompt: str) -> None:
        """Hook prompt does NOT contain 'PRODUCE NO OUTPUT'."""
        assert "PRODUCE NO OUTPUT" not in hook_prompt

    def test_does_not_contain_zero_tokens(self, hook_prompt: str) -> None:
        """Hook prompt does NOT contain 'ZERO TOKENS'."""
        assert "ZERO TOKENS" not in hook_prompt

    def test_contains_anti_fabrication(self, hook_prompt: str) -> None:
        """Hook prompt contains anti-fabrication instruction mentioning 'Human:'."""
        assert "Human:" in hook_prompt
        assert "NEVER generate text beginning with" in hook_prompt

    def test_hook_is_valid_json(self) -> None:
        """Hook file is valid JSON with all required fields."""
        path = _HOOKS_DIR / "ask-bootcamper.kiro.hook"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "name" in data
        assert "version" in data
        assert "when" in data
        assert "then" in data
        assert data["when"]["type"] == "agentStop"
        assert data["then"]["type"] == "askAgent"
        assert len(data["then"]["prompt"]) > 100

    def test_registry_matches_hook_file(self) -> None:
        """hook-registry-detail.md entry for ask-bootcamper contains DEFAULT OUTPUT."""
        registry = (_STEERING_DIR / "hook-registry-detail.md").read_text(encoding="utf-8")
        # Find the ask-bootcamper section
        start = registry.find("**ask-bootcamper**")
        assert start != -1
        section = registry[start:start + 500]
        assert "DEFAULT OUTPUT" in section
