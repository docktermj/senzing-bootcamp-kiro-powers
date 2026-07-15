"""Prompt logic tests for the critical hooks.

Verifies that each critical hook's prompt contains the required behavioral
instructions, keywords, and patterns appropriate to its purpose. Under Kiro
1.0 the critical set is the four hooks in ``CRITICAL_HOOKS``; the former
``commonmark-validation`` manual hook is now the ``/commonmark-validation``
slash command and is validated as such here.
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
    has_silent_processing,
    load_hook,
)

# ---------------------------------------------------------------------------
# Helper to load a critical hook's prompt
# ---------------------------------------------------------------------------


def _load_prompt(hook_id: str) -> str:
    """Load the action.prompt text for a given hook identifier."""
    path = HOOKS_DIR / f"{hook_id}.json"
    assert path.exists(), f"Hook file not found: {path}"
    data = load_hook(path)
    return data["action"]["prompt"]


def _load_hook_data(hook_id: str) -> dict:
    """Load the v1 hook entry for a given hook identifier."""
    path = HOOKS_DIR / f"{hook_id}.json"
    assert path.exists(), f"Hook file not found: {path}"
    return load_hook(path)


# ===========================================================================
# TestEnforceFilePathPolicies — Req 3.2, 3.4 (consolidated hook)
# ===========================================================================

class TestEnforceFilePathPolicies:
    """Verify write-policy-gate prompt covers both path policies:
    (1) feedback path and (2) working-directory restrictions.
    """

    FORBIDDEN_PATHS = ["/tmp/", "%TEMP%", "~/Downloads"]
    CANONICAL_FEEDBACK_PATH = "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"

    def test_prompt_references_forbidden_paths(self):
        """Prompt references at least one forbidden path pattern (Req 3.2)."""
        prompt = _load_prompt("write-policy-gate")
        found = [p for p in self.FORBIDDEN_PATHS if p in prompt]
        assert len(found) >= 1, (
            f"write-policy-gate prompt does not reference any forbidden "
            f"path. Expected at least one of: {self.FORBIDDEN_PATHS}"
        )

    def test_prompt_references_all_forbidden_paths(self):
        """Prompt references all three forbidden path patterns."""
        prompt = _load_prompt("write-policy-gate")
        for path in self.FORBIDDEN_PATHS:
            assert path in prompt, (
                f"write-policy-gate prompt missing forbidden path: {path}"
            )

    def test_prompt_contains_canonical_feedback_path(self):
        """Prompt contains the canonical feedback file path (Req 3.4)."""
        prompt = _load_prompt("write-policy-gate")
        assert self.CANONICAL_FEEDBACK_PATH in prompt, (
            f"write-policy-gate prompt does not contain canonical "
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
    """Verify the CommonMark validation instruction references its rule identifiers.

    Under Kiro 1.0, ``commonmark-validation`` is no longer a shipped hook — the
    former manual hook became the ``/commonmark-validation`` slash-command
    steering file. The CommonMark-rule intent is preserved there, so this class
    now validates the slash-command steering file rather than a hook prompt.
    """

    COMMONMARK_RULES = ["MD022", "MD031", "MD032", "MD040"]
    SLASH_COMMAND_FILE = (
        Path("senzing-bootcamp/steering/slash-commonmark-validation.md")
    )

    def _slash_command_text(self) -> str:
        assert self.SLASH_COMMAND_FILE.exists(), (
            f"Slash command file not found: {self.SLASH_COMMAND_FILE}"
        )
        return self.SLASH_COMMAND_FILE.read_text(encoding="utf-8")

    def test_prompt_references_commonmark_rule(self):
        """The slash command references at least one CommonMark rule id (Req 3.6)."""
        text = self._slash_command_text()
        found = [r for r in self.COMMONMARK_RULES if r in text]
        assert len(found) >= 1, (
            f"slash-commonmark-validation does not reference any CommonMark rule. "
            f"Expected at least one of: {self.COMMONMARK_RULES}"
        )

    def test_prompt_references_all_rules(self):
        """The slash command references all 4 required CommonMark rule ids."""
        text = self._slash_command_text()
        missing = [r for r in self.COMMONMARK_RULES if r not in text]
        assert not missing, (
            f"slash-commonmark-validation missing CommonMark rules: {missing}"
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
    """Verify PreToolUse/UserPromptSubmit critical hooks contain silent processing."""

    # Critical hooks that use the 1.0 PreToolUse or UserPromptSubmit triggers
    PASS_THROUGH_TRIGGERS = {"PreToolUse", "UserPromptSubmit"}

    def test_pass_through_critical_hooks_have_silent_processing(self):
        """All critical hooks with PreToolUse/UserPromptSubmit have silent processing (Req 3.8)."""
        for hook_id in CRITICAL_HOOKS:
            data = _load_hook_data(hook_id)
            trigger = data.get("trigger", "")
            if trigger not in self.PASS_THROUGH_TRIGGERS:
                continue
            prompt = data["action"]["prompt"]
            assert has_silent_processing(prompt), (
                f'Critical hook "{hook_id}" (trigger: {trigger}) '
                f"missing silent processing instruction in prompt"
            )

    @pytest.mark.parametrize("hook_id", CRITICAL_HOOKS)
    def test_individual_critical_hook_silent_processing(self, hook_id: str):
        """Each critical hook with a pass-through trigger has silent processing."""
        data = _load_hook_data(hook_id)
        trigger = data.get("trigger", "")
        if trigger not in self.PASS_THROUGH_TRIGGERS:
            pytest.skip(f"{hook_id} uses trigger '{trigger}', not pass-through")
        prompt = data["action"]["prompt"]
        assert has_silent_processing(prompt), (
            f'Critical hook "{hook_id}" missing silent processing instruction'
        )
