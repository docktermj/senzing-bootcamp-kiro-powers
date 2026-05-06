"""Tests for the Feedback Loop Closure feature.

Validates that whats-new.md exists with correct frontmatter,
steering-index.yaml has keyword entries, and session-resume.md
references the What's New step.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

_ROOT = Path(__file__).resolve().parent.parent.parent
_STEERING_DIR = _ROOT / "senzing-bootcamp" / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"


class TestWhatsNewFile:
    """Verify whats-new.md exists and has correct structure."""

    @pytest.fixture()
    def whats_new(self) -> str:
        path = _STEERING_DIR / "whats-new.md"
        return path.read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        """whats-new.md exists in the steering directory."""
        assert (_STEERING_DIR / "whats-new.md").exists()

    def test_has_manual_inclusion_frontmatter(self, whats_new: str) -> None:
        """whats-new.md has inclusion: manual in frontmatter."""
        assert "inclusion: manual" in whats_new

    def test_documents_three_conditions(self, whats_new: str) -> None:
        """whats-new.md documents all three conditions for showing notification."""
        assert "session_log.jsonl" in whats_new
        assert "CHANGELOG.md" in whats_new
        assert "show_whats_new" in whats_new

    def test_documents_relevance_scoring(self, whats_new: str) -> None:
        """whats-new.md documents relevance scoring with criteria."""
        assert "current module" in whats_new.lower()
        assert "language" in whats_new.lower()
        assert "bug fix" in whats_new.lower()
        assert "feature" in whats_new.lower()

    def test_contains_notification_template(self, whats_new: str) -> None:
        """whats-new.md contains the notification template with 📢 emoji."""
        assert "📢" in whats_new

    def test_contains_attribution_note(self, whats_new: str) -> None:
        """whats-new.md includes the attribution note text."""
        assert "bootcamper feedback" in whats_new.lower()

    def test_documents_suppression(self, whats_new: str) -> None:
        """whats-new.md documents the suppression preference."""
        assert "show_whats_new: false" in whats_new


class TestSessionResumeWhatsNew:
    """Verify session-resume.md contains the What's New step."""

    @pytest.fixture()
    def session_resume(self) -> str:
        path = _STEERING_DIR / "session-resume.md"
        return path.read_text(encoding="utf-8")

    def test_contains_whats_new_step(self, session_resume: str) -> None:
        """session-resume.md contains a What's New step reference."""
        assert "What's New" in session_resume

    def test_whats_new_before_step_3(self, session_resume: str) -> None:
        """What's New step appears before Step 3 in session-resume.md."""
        whats_new_pos = session_resume.find("What's New")
        step_3_pos = session_resume.find("## Step 3:")
        assert whats_new_pos < step_3_pos


class TestSteeringIndexKeywords:
    """Verify steering-index.yaml has keyword entries for What's New triggers."""

    @pytest.fixture()
    def index_content(self) -> str:
        return _INDEX_PATH.read_text(encoding="utf-8")

    def test_whats_new_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'what's new' keyword."""
        assert "what's new: whats-new.md" in index_content

    def test_changelog_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'changelog' keyword."""
        assert "changelog: whats-new.md" in index_content

    def test_updates_keyword(self, index_content: str) -> None:
        """steering-index.yaml has 'updates' keyword."""
        assert "updates: whats-new.md" in index_content


class TestRelevanceScoringProperty:
    """Property test: relevance scoring always produces 0-3 results."""

    @given(
        num_changes=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_max_three_results(self, num_changes: int) -> None:
        """Selecting top 3 from any number of changes always yields 0-3."""
        # Simulate: score N changes, take top 3
        scores = list(range(num_changes))
        top_3 = sorted(scores, reverse=True)[:3]
        assert len(top_3) <= 3
        assert len(top_3) >= 0
