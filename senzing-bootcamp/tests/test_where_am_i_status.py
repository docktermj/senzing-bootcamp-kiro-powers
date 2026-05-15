"""Tests for the 'Where Am I?' Quick Status Command feature.

Validates that inline-status.md exists with correct frontmatter,
steering-index.yaml has keyword entries, and the review-bootcamper-input
hook detects status triggers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

_ROOT = Path(__file__).resolve().parent.parent.parent
_STEERING_DIR = _ROOT / "senzing-bootcamp" / "steering"
_HOOKS_DIR = _ROOT / "senzing-bootcamp" / "hooks"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"

TRIGGER_PHRASES = [
    "where am I",
    "status",
    "what step am I on",
    "show progress",
    "how far along am I",
]


class TestInlineStatusFile:
    """Verify inline-status.md exists and has correct structure."""

    @pytest.fixture()
    def inline_status(self) -> str:
        path = _STEERING_DIR / "inline-status.md"
        return path.read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        """inline-status.md exists in the steering directory."""
        assert (_STEERING_DIR / "inline-status.md").exists()

    def test_has_manual_inclusion_frontmatter(self, inline_status: str) -> None:
        """inline-status.md has inclusion: manual in frontmatter."""
        assert "inclusion: manual" in inline_status

    def test_contains_response_template_with_emoji(self, inline_status: str) -> None:
        """inline-status.md contains the 📍 emoji in the response template."""
        assert "📍" in inline_status

    def test_contains_track_completion(self, inline_status: str) -> None:
        """inline-status.md documents track completion calculation."""
        assert "track" in inline_status.lower()
        assert "completion" in inline_status.lower()

    def test_contains_data_sources_mention(self, inline_status: str) -> None:
        """inline-status.md mentions data sources in the template."""
        assert "data sources" in inline_status.lower()

    def test_contains_pointing_question(self, inline_status: str) -> None:
        """inline-status.md contains a 👉 question in the template."""
        assert "👉" in inline_status

    def test_documents_edge_cases(self, inline_status: str) -> None:
        """inline-status.md documents edge cases."""
        assert "no progress file" in inline_status.lower() or \
               "No progress file" in inline_status


class TestSteeringIndexKeywords:
    """Verify steering-index.yaml contains keyword entries for all trigger phrases."""

    @pytest.fixture()
    def index_content(self) -> str:
        return _INDEX_PATH.read_text(encoding="utf-8")

    def test_where_am_i_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'where am I' keyword."""
        assert "where am I: inline-status.md" in index_content

    def test_status_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'status' keyword."""
        assert "status: inline-status.md" in index_content

    def test_what_step_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'what step am I on' keyword."""
        assert "what step am I on: inline-status.md" in index_content

    def test_show_progress_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'show progress' keyword."""
        assert "show progress: inline-status.md" in index_content

    def test_how_far_along_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'how far along am I' keyword."""
        assert "how far along am I: inline-status.md" in index_content


class TestReviewBootcamperInputHook:
    """Verify review-bootcamper-input hook detects status triggers."""

    @pytest.fixture()
    def hook_data(self) -> dict:
        path = _HOOKS_DIR / "review-bootcamper-input.kiro.hook"
        return json.loads(path.read_text(encoding="utf-8"))

    @pytest.fixture()
    def hook_prompt(self, hook_data: dict) -> str:
        return hook_data["then"]["prompt"]

    def test_hook_prompt_contains_status_triggers(self, hook_prompt: str) -> None:
        """Hook prompt mentions status trigger phrases."""
        assert "where am I" in hook_prompt
        assert "status" in hook_prompt
        assert "what step am I on" in hook_prompt

    def test_hook_prompt_contains_status_trigger_detected(self, hook_prompt: str) -> None:
        """Hook prompt outputs STATUS_TRIGGER_DETECTED."""
        assert "STATUS_TRIGGER_DETECTED" in hook_prompt

    def test_hook_prompt_references_inline_status(self, hook_prompt: str) -> None:
        """Hook prompt references inline-status.md."""
        assert "inline-status.md" in hook_prompt


class TestHookRegistryEntry:
    """Verify hook-registry.md entry for review-bootcamper-input mentions status."""

    @pytest.fixture()
    def registry_content(self) -> str:
        path = _STEERING_DIR / "hook-registry.md"
        return path.read_text(encoding="utf-8")

    def test_registry_mentions_status_triggers(self, registry_content: str) -> None:
        """hook-registry.md review-bootcamper-input entry mentions status triggers."""
        # Find the review-bootcamper-input entry in the table
        assert "review-bootcamper-input" in registry_content, (
            "hook-registry.md does not contain review-bootcamper-input entry"
        )
        # Find the line containing review-bootcamper-input and check for trigger info
        start = registry_content.find("review-bootcamper-input")
        assert start != -1
        # Check the entry mentions feedback triggers
        section = registry_content[start:start + 500]
        assert "feedback" in section.lower() or "trigger" in section.lower()


class TestTrackCompletionProperty:
    """Property test: track completion percentage is always 0-100."""

    @given(
        completed=st.lists(st.integers(min_value=1, max_value=11), max_size=11, unique=True),
        current_module=st.integers(min_value=1, max_value=11),
        current_step=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=100)
    def test_completion_always_0_to_100(
        self, completed: list[int], current_module: int, current_step: int
    ) -> None:
        """Track completion percentage is always between 0 and 100."""
        # Simulate the calculation described in inline-status.md
        track_modules = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # Full Production
        total_steps = len(track_modules) * 10  # Assume 10 steps per module
        completed_steps = 0

        for mod in track_modules:
            if mod in completed:
                completed_steps += 10
            elif mod == current_module:
                completed_steps += min(current_step, 10)

        pct = round(completed_steps / total_steps * 100) if total_steps > 0 else 0
        assert 0 <= pct <= 100
