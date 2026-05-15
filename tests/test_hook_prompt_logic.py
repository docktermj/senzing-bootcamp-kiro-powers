"""Prompt logic tests for the 7 critical hooks.

Verifies that each critical hook's prompt contains the required behavioral
instructions, keywords, and patterns appropriate to its purpose.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    CRITICAL_HOOKS,
    HOOKS_DIR,
    TOOL_EVENT_TYPES,
    has_silent_processing,
    load_hook,
)

# ---------------------------------------------------------------------------
# Helper to load a critical hook's prompt
# ---------------------------------------------------------------------------


def _load_prompt(hook_id: str) -> str:
    """Load the prompt text for a given hook identifier."""
    path = HOOKS_DIR / f"{hook_id}.kiro.hook"
    assert path.exists(), f"Hook file not found: {path}"
    data = load_hook(path)
    return data["then"]["prompt"]


def _load_hook_data(hook_id: str) -> dict:
    """Load the full hook data for a given hook identifier."""
    path = HOOKS_DIR / f"{hook_id}.kiro.hook"
    assert path.exists(), f"Hook file not found: {path}"
    return load_hook(path)


# ===========================================================================
# TestEnforceFilePathPolicies — Req 3.2, 3.4 (consolidated hook)
# ===========================================================================

class TestEnforceFilePathPolicies:
    """Verify enforce-file-path-policies prompt covers both path policies:
    (1) feedback path and (2) working-directory restrictions.
    """

    FORBIDDEN_PATHS = ["/tmp/", "%TEMP%", "~/Downloads"]
    CANONICAL_FEEDBACK_PATH = "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"

    def test_prompt_references_forbidden_paths(self):
        """Prompt references at least one forbidden path pattern (Req 3.2)."""
        prompt = _load_prompt("enforce-file-path-policies")
        found = [p for p in self.FORBIDDEN_PATHS if p in prompt]
        assert len(found) >= 1, (
            f"enforce-file-path-policies prompt does not reference any forbidden "
            f"path. Expected at least one of: {self.FORBIDDEN_PATHS}"
        )

    def test_prompt_references_all_forbidden_paths(self):
        """Prompt references all three forbidden path patterns."""
        prompt = _load_prompt("enforce-file-path-policies")
        for path in self.FORBIDDEN_PATHS:
            assert path in prompt, (
                f"enforce-file-path-policies prompt missing forbidden path: {path}"
            )

    def test_prompt_contains_canonical_feedback_path(self):
        """Prompt contains the canonical feedback file path (Req 3.4)."""
        prompt = _load_prompt("enforce-file-path-policies")
        assert self.CANONICAL_FEEDBACK_PATH in prompt, (
            f"enforce-file-path-policies prompt does not contain canonical "
            f"feedback path: {self.CANONICAL_FEEDBACK_PATH}"
        )


# ===========================================================================
# TestReviewBootcamperInput — Req 3.3
# ===========================================================================

class TestReviewBootcamperInput:
    """Verify review-bootcamper-input prompt contains feedback trigger phrases."""

    FEEDBACK_TRIGGERS = [
        "bootcamp feedback",
        "power feedback",
        "submit feedback",
        "provide feedback",
        "I have feedback",
        "report an issue",
    ]

    def test_prompt_contains_at_least_3_triggers(self):
        """Prompt contains at least 3 feedback trigger phrases (Req 3.3)."""
        prompt = _load_prompt("review-bootcamper-input").lower()
        found = [t for t in self.FEEDBACK_TRIGGERS if t.lower() in prompt]
        assert len(found) >= 3, (
            f"review-bootcamper-input prompt contains only {len(found)} trigger phrases: "
            f"{found}. Expected at least 3 of: {self.FEEDBACK_TRIGGERS}"
        )

    def test_prompt_contains_all_triggers(self):
        """Prompt contains all 6 feedback trigger phrases."""
        prompt = _load_prompt("review-bootcamper-input").lower()
        missing = [t for t in self.FEEDBACK_TRIGGERS if t.lower() not in prompt]
        assert not missing, (
            f"review-bootcamper-input prompt missing trigger phrases: {missing}"
        )


# ===========================================================================
# TestCodeStyleCheck — Req 3.5
# ===========================================================================

class TestCodeStyleCheck:
    """Verify code-style-check prompt references at least one coding standard."""

    CODING_STANDARDS = ["PEP-8", "rustfmt", "clippy", "ESLint"]

    def test_prompt_references_coding_standard(self):
        """Prompt references at least one coding standard (Req 3.5)."""
        prompt = _load_prompt("code-style-check")
        found = [s for s in self.CODING_STANDARDS if s.lower() in prompt.lower()]
        assert len(found) >= 1, (
            f"code-style-check prompt does not reference any coding standard. "
            f"Expected at least one of: {self.CODING_STANDARDS}"
        )

    def test_prompt_references_multiple_standards(self):
        """Prompt references multiple coding standards for multi-language support."""
        prompt = _load_prompt("code-style-check")
        found = [s for s in self.CODING_STANDARDS if s.lower() in prompt.lower()]
        assert len(found) >= 2, (
            f"code-style-check prompt only references {len(found)} standards: {found}. "
            f"Expected at least 2 for multi-language support."
        )


# ===========================================================================
# TestCommonmarkValidation — Req 3.6
# ===========================================================================

class TestCommonmarkValidation:
    """Verify commonmark-validation prompt references CommonMark rule identifiers."""

    COMMONMARK_RULES = ["MD022", "MD031", "MD032", "MD040"]

    def test_prompt_references_commonmark_rule(self):
        """Prompt references at least one CommonMark rule identifier (Req 3.6)."""
        prompt = _load_prompt("commonmark-validation")
        found = [r for r in self.COMMONMARK_RULES if r in prompt]
        assert len(found) >= 1, (
            f"commonmark-validation prompt does not reference any CommonMark rule. "
            f"Expected at least one of: {self.COMMONMARK_RULES}"
        )

    def test_prompt_references_all_rules(self):
        """Prompt references all 4 required CommonMark rule identifiers."""
        prompt = _load_prompt("commonmark-validation")
        missing = [r for r in self.COMMONMARK_RULES if r not in prompt]
        assert not missing, (
            f"commonmark-validation prompt missing CommonMark rules: {missing}"
        )


# ===========================================================================
# TestAskBootcamper — Req 3.7
# ===========================================================================

class TestAskBootcamper:
    """Verify ask-bootcamper prompt contains .question_pending and closing question emoji."""

    def test_prompt_contains_question_pending(self):
        """Prompt contains .question_pending file reference (Req 3.7)."""
        prompt = _load_prompt("ask-bootcamper")
        assert ".question_pending" in prompt, (
            "ask-bootcamper prompt does not contain '.question_pending' reference"
        )

    def test_prompt_contains_closing_question_emoji(self):
        """Prompt contains the closing question emoji character (Req 3.7)."""
        prompt = _load_prompt("ask-bootcamper")
        # The hook uses 👉 as the closing question emoji
        assert "👉" in prompt, (
            "ask-bootcamper prompt does not contain the closing question emoji '👉'"
        )


# ===========================================================================
# TestCriticalHookSilentProcessing — Req 3.8
# ===========================================================================

class TestCriticalHookSilentProcessing:
    """Verify preToolUse/promptSubmit critical hooks contain silent processing instruction."""

    # Critical hooks that use preToolUse or promptSubmit event types
    PASS_THROUGH_EVENT_TYPES = {"preToolUse", "promptSubmit"}

    def test_pass_through_critical_hooks_have_silent_processing(self):
        """All critical hooks with preToolUse/promptSubmit have silent processing (Req 3.8)."""
        for hook_id in CRITICAL_HOOKS:
            data = _load_hook_data(hook_id)
            event_type = data.get("when", {}).get("type", "")
            if event_type not in self.PASS_THROUGH_EVENT_TYPES:
                continue
            prompt = data["then"]["prompt"]
            assert has_silent_processing(prompt), (
                f'Critical hook "{hook_id}" (event type: {event_type}) '
                f"missing silent processing instruction in prompt"
            )

    @pytest.mark.parametrize("hook_id", CRITICAL_HOOKS)
    def test_individual_critical_hook_silent_processing(self, hook_id: str):
        """Each critical hook with pass-through event type has silent processing."""
        data = _load_hook_data(hook_id)
        event_type = data.get("when", {}).get("type", "")
        if event_type not in self.PASS_THROUGH_EVENT_TYPES:
            pytest.skip(f"{hook_id} uses event type '{event_type}', not pass-through")
        prompt = data["then"]["prompt"]
        assert has_silent_processing(prompt), (
            f'Critical hook "{hook_id}" missing silent processing instruction'
        )
