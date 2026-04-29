"""Bug condition exploration tests for silent-hook-processing bugfix.

Bug condition tests verify that the four affected hook prompts contain an
explicit "produce no output" instruction for the no-action-needed case.
Also checks that hook-registry.md mirrors the same prompts and that
agent-instructions.md does NOT yet contain a silent-processing rule.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

EXPECTED OUTCOME on UNFIXED code:
- Bug condition tests FAIL (confirming the bug — prompts lack explicit silent instructions)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"

_AFFECTED_HOOK_FILES: dict[str, Path] = {
    "capture-feedback": _HOOKS_DIR / "capture-feedback.kiro.hook",
    "enforce-feedback-path": _HOOKS_DIR / "enforce-feedback-path.kiro.hook",
    "enforce-working-directory": _HOOKS_DIR / "enforce-working-directory.kiro.hook",
    "verify-senzing-facts": _HOOKS_DIR / "verify-senzing-facts.kiro.hook",
}

_HOOK_REGISTRY = _STEERING_DIR / "hook-registry.md"
_AGENT_INSTRUCTIONS = _STEERING_DIR / "agent-instructions.md"

# The phrase that must appear in fixed prompts for the no-action case
_SILENT_INSTRUCTION = "produce no output"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_hook_prompt(path: Path) -> str:
    """Parse a .kiro.hook JSON file and return the then.prompt value."""
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    return data["then"]["prompt"]


def _extract_registry_prompt(registry_text: str, hook_id: str) -> str:
    """Extract the Prompt: text for a given hook id from hook-registry.md.

    The registry format is:
        **hook-id** (event → action)
        Prompt: "..."
    """
    # Match the section starting with **hook-id** and capture the Prompt line
    # The prompt is enclosed in double quotes after "Prompt: "
    pattern = rf"\*\*{re.escape(hook_id)}\*\*.*?\nPrompt:\s*\"(.*?)\"\n"
    match = re.search(pattern, registry_text, re.DOTALL)
    if match:
        return match.group(1)
    # Fallback: try without trailing newline
    pattern2 = rf"\*\*{re.escape(hook_id)}\*\*.*?\nPrompt:\s*\"(.*?)\""
    match2 = re.search(pattern2, registry_text, re.DOTALL)
    if match2:
        return match2.group(1)
    return ""


def _prompt_has_silent_instruction(prompt: str) -> bool:
    """Check if a prompt contains an explicit 'produce no output' instruction."""
    return _SILENT_INSTRUCTION.lower() in prompt.lower()


# ---------------------------------------------------------------------------
# Tests -- Bug Condition: Hook prompts should contain "produce no output"
# On UNFIXED code, these tests FAIL (confirming the bug exists)
# ---------------------------------------------------------------------------


class TestBugConditionHookFiles:
    """Assert that each affected hook file's prompt contains an explicit
    'produce no output' instruction for the no-action case.

    On unfixed code these assertions will FAIL, confirming the bug exists.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4**
    """

    def test_capture_feedback_has_silent_instruction(self) -> None:
        """capture-feedback prompt should contain 'produce no output'.

        **Validates: Requirements 1.1, 2.1**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["capture-feedback"])
        assert _prompt_has_silent_instruction(prompt), (
            f"capture-feedback prompt lacks explicit silent instruction.\n"
            f"Prompt uses 'do nothing' without 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_enforce_feedback_path_has_silent_instruction(self) -> None:
        """enforce-feedback-path prompt should contain 'produce no output'.

        **Validates: Requirements 1.2, 2.2**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["enforce-feedback-path"])
        assert _prompt_has_silent_instruction(prompt), (
            f"enforce-feedback-path prompt lacks explicit silent instruction.\n"
            f"Prompt uses 'do nothing' without 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_enforce_working_directory_has_silent_instruction(self) -> None:
        """enforce-working-directory prompt should contain 'produce no output'.

        **Validates: Requirements 1.3, 2.3**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["enforce-working-directory"])
        assert _prompt_has_silent_instruction(prompt), (
            f"enforce-working-directory prompt lacks explicit silent instruction.\n"
            f"Prompt has no explicit no-action branch with 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_verify_senzing_facts_has_silent_instruction(self) -> None:
        """verify-senzing-facts prompt should contain 'produce no output'.

        **Validates: Requirements 1.4, 2.4**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["verify-senzing-facts"])
        assert _prompt_has_silent_instruction(prompt), (
            f"verify-senzing-facts prompt lacks explicit silent instruction.\n"
            f"Prompt has no explicit no-action branch with 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )


class TestBugConditionHookRegistry:
    """Assert that hook-registry.md prompts for the four affected hooks
    contain an explicit 'produce no output' instruction.

    On unfixed code these assertions will FAIL, confirming the bug exists.

    **Validates: Requirements 1.5, 2.5**
    """

    @pytest.fixture(autouse=True)
    def _load_registry(self) -> None:
        self._registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")

    def test_registry_capture_feedback_has_silent_instruction(self) -> None:
        """hook-registry capture-feedback prompt should contain 'produce no output'.

        **Validates: Requirements 1.5, 2.5**"""
        prompt = _extract_registry_prompt(self._registry_text, "capture-feedback")
        assert prompt, "Could not extract capture-feedback prompt from hook-registry.md"
        assert _prompt_has_silent_instruction(prompt), (
            f"hook-registry capture-feedback prompt lacks 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_registry_enforce_feedback_path_has_silent_instruction(self) -> None:
        """hook-registry enforce-feedback-path prompt should contain 'produce no output'.

        **Validates: Requirements 1.5, 2.5**"""
        prompt = _extract_registry_prompt(self._registry_text, "enforce-feedback-path")
        assert prompt, "Could not extract enforce-feedback-path prompt from hook-registry.md"
        assert _prompt_has_silent_instruction(prompt), (
            f"hook-registry enforce-feedback-path prompt lacks 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_registry_enforce_working_directory_has_silent_instruction(self) -> None:
        """hook-registry enforce-working-directory prompt should contain 'produce no output'.

        **Validates: Requirements 1.5, 2.5**"""
        prompt = _extract_registry_prompt(self._registry_text, "enforce-working-directory")
        assert prompt, "Could not extract enforce-working-directory prompt from hook-registry.md"
        assert _prompt_has_silent_instruction(prompt), (
            f"hook-registry enforce-working-directory prompt lacks 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_registry_verify_senzing_facts_has_silent_instruction(self) -> None:
        """hook-registry verify-senzing-facts prompt should contain 'produce no output'.

        **Validates: Requirements 1.5, 2.5**"""
        prompt = _extract_registry_prompt(self._registry_text, "verify-senzing-facts")
        assert prompt, "Could not extract verify-senzing-facts prompt from hook-registry.md"
        assert _prompt_has_silent_instruction(prompt), (
            f"hook-registry verify-senzing-facts prompt lacks 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )


class TestBugConditionAgentInstructions:
    """Assert that agent-instructions.md does NOT yet contain a
    silent-processing rule under the Hooks section.

    On unfixed code this assertion will FAIL (confirming the rule is missing).

    **Validates: Requirements 2.6**
    """

    def test_agent_instructions_has_silent_processing_rule(self) -> None:
        """agent-instructions.md should contain a silent-processing rule under Hooks.

        **Validates: Requirements 2.6**"""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        # Extract the Hooks section
        hooks_match = re.search(
            r"^## Hooks\s*\n(.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        assert hooks_match, "Could not find ## Hooks section in agent-instructions.md"
        hooks_section = hooks_match.group(1)
        assert _SILENT_INSTRUCTION.lower() in hooks_section.lower(), (
            "agent-instructions.md Hooks section lacks a silent-processing rule.\n"
            f"Hooks section content:\n{hooks_section}"
        )


# ---------------------------------------------------------------------------
# Property-Based Test -- Bug Condition across all affected hooks
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5**
# ---------------------------------------------------------------------------

_AFFECTED_HOOK_KEYS = list(_AFFECTED_HOOK_FILES.keys())


class TestBugConditionProperty:
    """Property-based test: for any randomly selected affected hook,
    both the hook file prompt and the hook-registry prompt should contain
    an explicit 'produce no output' instruction.

    On unfixed code this property FAILS, surfacing counterexamples that
    demonstrate the bug exists."""

    @given(hook_key=st.sampled_from(_AFFECTED_HOOK_KEYS))
    @settings(max_examples=20)
    def test_all_affected_hooks_have_silent_instruction(
        self, hook_key: str
    ) -> None:
        """**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5**

        For any affected hook, both the .kiro.hook file prompt and the
        hook-registry.md prompt should contain 'produce no output'."""
        # Check hook file
        hook_prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES[hook_key])
        hook_has_silent = _prompt_has_silent_instruction(hook_prompt)

        # Check registry
        registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")
        registry_prompt = _extract_registry_prompt(registry_text, hook_key)
        registry_has_silent = _prompt_has_silent_instruction(registry_prompt)

        assert hook_has_silent and registry_has_silent, (
            f"Bug condition found in {hook_key}:\n"
            f"  Hook file has 'produce no output': {hook_has_silent}\n"
            f"  Registry has 'produce no output': {registry_has_silent}\n"
            f"  Hook prompt excerpt: {hook_prompt[:150]}...\n"
            f"  Registry prompt excerpt: {registry_prompt[:150]}..."
        )


# ===========================================================================
# Preservation Property Tests (Task 2)
#
# These tests verify that action-required branches in affected hooks are
# preserved, non-affected hooks are unchanged, ask-bootcamper.kiro.hook
# matches baseline, and agent-instructions.md existing content is preserved.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
#
# EXPECTED OUTCOME on UNFIXED code: All preservation tests PASS
# ===========================================================================

# ---------------------------------------------------------------------------
# Baseline constants — action-required content that MUST be preserved
# ---------------------------------------------------------------------------

# capture-feedback: feedback workflow initiation keywords
_CAPTURE_FEEDBACK_ACTION_KEYWORDS: list[str] = [
    "bootcamp feedback",
    "power feedback",
    "submit feedback",
    "provide feedback",
    "I have feedback",
    "report an issue",
    "feedback-workflow.md",
]

# enforce-feedback-path: path redirection keywords
_ENFORCE_FEEDBACK_PATH_ACTION_KEYWORDS: list[str] = [
    "SENZING_BOOTCAMP_POWER_FEEDBACK.md",
    "STOP and redirect",
]

# enforce-working-directory: path correction keywords
_ENFORCE_WORKING_DIR_ACTION_KEYWORDS: list[str] = [
    "/tmp/",
    "%TEMP%",
    "~/Downloads",
    "project-relative",
    "Do NOT proceed",
]

# verify-senzing-facts: MCP verification keywords
_VERIFY_SENZING_FACTS_ACTION_KEYWORDS: list[str] = [
    "MCP",
    "mapping_workflow",
    "generate_scaffold",
    "get_sdk_reference",
    "search_docs",
    "explain_error_code",
    "SENZING_INFORMATION_POLICY",
]

# Map hook id → action-required keywords
_ACTION_REQUIRED_KEYWORDS: dict[str, list[str]] = {
    "capture-feedback": _CAPTURE_FEEDBACK_ACTION_KEYWORDS,
    "enforce-feedback-path": _ENFORCE_FEEDBACK_PATH_ACTION_KEYWORDS,
    "enforce-working-directory": _ENFORCE_WORKING_DIR_ACTION_KEYWORDS,
    "verify-senzing-facts": _VERIFY_SENZING_FACTS_ACTION_KEYWORDS,
}

# Non-affected hook ids in hook-registry.md (all hooks except the 4 affected)
_NON_AFFECTED_HOOK_IDS: list[str] = [
    "code-style-check",
    "ask-bootcamper",
    "commonmark-validation",
    "data-quality-check",
    "validate-senzing-json",
    "analyze-after-mapping",
    "backup-before-load",
    "run-tests-after-change",
    "verify-generated-code",
    "offer-visualization",
    "enforce-visualization-offers",
    "deployment-phase-gate",
    "backup-project-on-request",
    "git-commit-reminder",
]

_ASK_BOOTCAMPER_HOOK = _HOOKS_DIR / "ask-bootcamper.kiro.hook"


# ---------------------------------------------------------------------------
# Baseline snapshots — captured from UNFIXED code
# ---------------------------------------------------------------------------


def _snapshot_registry_non_affected() -> dict[str, str]:
    """Return a dict of hook_id → full section text for non-affected hooks."""
    registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")
    snapshots: dict[str, str] = {}
    for hook_id in _NON_AFFECTED_HOOK_IDS:
        # Extract the full section for this hook (from **hook-id** to the next
        # **hook-id** or end of file)
        pattern = (
            rf"(\*\*{re.escape(hook_id)}\*\*.*?)(?=\n\*\*[a-z]|\Z)"
        )
        match = re.search(pattern, registry_text, re.DOTALL)
        if match:
            snapshots[hook_id] = match.group(1).strip()
    return snapshots


def _snapshot_ask_bootcamper() -> str:
    """Return the full content of ask-bootcamper.kiro.hook."""
    return _ASK_BOOTCAMPER_HOOK.read_text(encoding="utf-8")


def _snapshot_agent_instructions() -> str:
    """Return the full content of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")


# Capture baselines at module load time (before any fix is applied)
_BASELINE_REGISTRY_NON_AFFECTED = _snapshot_registry_non_affected()
_BASELINE_ASK_BOOTCAMPER = _snapshot_ask_bootcamper()
_BASELINE_AGENT_INSTRUCTIONS = _snapshot_agent_instructions()


# ---------------------------------------------------------------------------
# Helpers for preservation tests
# ---------------------------------------------------------------------------


def _extract_registry_section(registry_text: str, hook_id: str) -> str:
    """Extract the full section for a hook from hook-registry.md."""
    pattern = (
        rf"(\*\*{re.escape(hook_id)}\*\*.*?)(?=\n\*\*[a-z]|\Z)"
    )
    match = re.search(pattern, registry_text, re.DOTALL)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Unit Tests — Preservation of action-required branches
# ---------------------------------------------------------------------------


class TestPreservationActionBranches:
    """Verify that each affected hook's action-required content is preserved.

    These tests check that key phrases from the action-required branches
    exist in the current hook prompts. They should PASS on both unfixed
    and fixed code.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    def test_capture_feedback_preserves_feedback_workflow(self) -> None:
        """capture-feedback preserves feedback workflow initiation text.

        **Validates: Requirements 3.1**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["capture-feedback"])
        for keyword in _CAPTURE_FEEDBACK_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"capture-feedback prompt missing action-required keyword: "
                f"'{keyword}'\nPrompt: {prompt[:300]}..."
            )

    def test_enforce_feedback_path_preserves_redirection(self) -> None:
        """enforce-feedback-path preserves path redirection text.

        **Validates: Requirements 3.2**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["enforce-feedback-path"])
        for keyword in _ENFORCE_FEEDBACK_PATH_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"enforce-feedback-path prompt missing action-required keyword: "
                f"'{keyword}'\nPrompt: {prompt[:300]}..."
            )

    def test_enforce_working_directory_preserves_correction(self) -> None:
        """enforce-working-directory preserves path correction text.

        **Validates: Requirements 3.3**"""
        prompt = _read_hook_prompt(
            _AFFECTED_HOOK_FILES["enforce-working-directory"]
        )
        for keyword in _ENFORCE_WORKING_DIR_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"enforce-working-directory prompt missing action-required "
                f"keyword: '{keyword}'\nPrompt: {prompt[:300]}..."
            )

    def test_verify_senzing_facts_preserves_mcp_verification(self) -> None:
        """verify-senzing-facts preserves MCP verification text.

        **Validates: Requirements 3.4**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["verify-senzing-facts"])
        for keyword in _VERIFY_SENZING_FACTS_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"verify-senzing-facts prompt missing action-required keyword: "
                f"'{keyword}'\nPrompt: {prompt[:300]}..."
            )


# ---------------------------------------------------------------------------
# Unit Tests — Non-affected hooks unchanged
# ---------------------------------------------------------------------------


class TestPreservationNonAffectedHooks:
    """Verify that all non-affected hooks in hook-registry.md are unchanged.

    **Validates: Requirements 3.5, 3.6**
    """

    @pytest.fixture(autouse=True)
    def _load_registry(self) -> None:
        self._registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")

    @pytest.mark.parametrize("hook_id", _NON_AFFECTED_HOOK_IDS)
    def test_non_affected_hook_unchanged(self, hook_id: str) -> None:
        """Non-affected hook '{hook_id}' section in registry is unchanged.

        **Validates: Requirements 3.5, 3.6**"""
        current_section = _extract_registry_section(
            self._registry_text, hook_id
        )
        baseline_section = _BASELINE_REGISTRY_NON_AFFECTED.get(hook_id, "")
        assert baseline_section, (
            f"No baseline captured for non-affected hook: {hook_id}"
        )
        assert current_section == baseline_section, (
            f"Non-affected hook '{hook_id}' section changed in registry!\n"
            f"Expected:\n{baseline_section[:200]}...\n"
            f"Got:\n{current_section[:200]}..."
        )


# ---------------------------------------------------------------------------
# Unit Tests — ask-bootcamper.kiro.hook unchanged
# ---------------------------------------------------------------------------


class TestPreservationAskBootcamper:
    """Verify ask-bootcamper.kiro.hook content matches baseline.

    **Validates: Requirements 3.5**
    """

    def test_ask_bootcamper_hook_unchanged(self) -> None:
        """ask-bootcamper.kiro.hook content matches baseline.

        **Validates: Requirements 3.5**"""
        current = _ASK_BOOTCAMPER_HOOK.read_text(encoding="utf-8")
        assert current == _BASELINE_ASK_BOOTCAMPER, (
            "ask-bootcamper.kiro.hook content changed!\n"
            f"Expected length: {len(_BASELINE_ASK_BOOTCAMPER)}\n"
            f"Got length: {len(current)}"
        )


# ---------------------------------------------------------------------------
# Unit Tests — agent-instructions.md existing content preserved
# ---------------------------------------------------------------------------


class TestPreservationAgentInstructions:
    """Verify all existing content in agent-instructions.md is preserved.

    New content may be added (e.g., a silent-processing rule), but all
    existing content must remain.

    **Validates: Requirements 3.5**
    """

    def test_agent_instructions_existing_content_preserved(self) -> None:
        """All existing agent-instructions.md content is preserved.

        **Validates: Requirements 3.5**"""
        current = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        # Every line from the baseline must appear in the current content
        # (new lines may be added, but existing lines must not be removed)
        baseline_lines = _BASELINE_AGENT_INSTRUCTIONS.splitlines()
        current_lines_set = set(current.splitlines())
        missing_lines: list[str] = []
        for line in baseline_lines:
            if line not in current_lines_set:
                missing_lines.append(line)
        assert not missing_lines, (
            f"agent-instructions.md is missing {len(missing_lines)} "
            f"baseline lines:\n"
            + "\n".join(f"  - {line!r}" for line in missing_lines[:10])
        )


# ---------------------------------------------------------------------------
# Property-Based Tests — Preservation across all affected hooks
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
# ---------------------------------------------------------------------------


class TestPreservationActionBranchesProperty:
    """Property-based test: for any randomly selected affected hook and
    any of its action-required keywords, the keyword must be present in
    the current hook file prompt.

    Should PASS on both unfixed and fixed code.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    @given(hook_key=st.sampled_from(_AFFECTED_HOOK_KEYS))
    @settings(max_examples=20)
    def test_action_keywords_preserved_in_hook_files(
        self, hook_key: str
    ) -> None:
        """**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

        For any affected hook, all action-required keywords are present
        in the hook file prompt."""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES[hook_key])
        keywords = _ACTION_REQUIRED_KEYWORDS[hook_key]
        for keyword in keywords:
            assert keyword in prompt, (
                f"Action-required keyword missing from {hook_key} prompt: "
                f"'{keyword}'\nPrompt excerpt: {prompt[:200]}..."
            )

    @given(hook_key=st.sampled_from(_AFFECTED_HOOK_KEYS))
    @settings(max_examples=20)
    def test_action_keywords_preserved_in_registry(
        self, hook_key: str
    ) -> None:
        """**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

        For any affected hook, all action-required keywords are present
        in the hook-registry.md prompt."""
        registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")
        prompt = _extract_registry_prompt(registry_text, hook_key)
        assert prompt, (
            f"Could not extract {hook_key} prompt from hook-registry.md"
        )
        keywords = _ACTION_REQUIRED_KEYWORDS[hook_key]
        for keyword in keywords:
            assert keyword in prompt, (
                f"Action-required keyword missing from registry {hook_key} "
                f"prompt: '{keyword}'\nPrompt excerpt: {prompt[:200]}..."
            )


# ---------------------------------------------------------------------------
# Property-Based Tests — Non-affected hooks unchanged
# **Validates: Requirements 3.5, 3.6**
# ---------------------------------------------------------------------------


class TestPreservationNonAffectedProperty:
    """Property-based test: for any randomly selected non-affected hook,
    its section in hook-registry.md is identical to the baseline.

    Should PASS on both unfixed and fixed code.

    **Validates: Requirements 3.5, 3.6**
    """

    @given(hook_id=st.sampled_from(_NON_AFFECTED_HOOK_IDS))
    @settings(max_examples=30)
    def test_non_affected_hooks_unchanged(self, hook_id: str) -> None:
        """**Validates: Requirements 3.5, 3.6**

        For any non-affected hook, its registry section matches baseline."""
        registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")
        current_section = _extract_registry_section(registry_text, hook_id)
        baseline_section = _BASELINE_REGISTRY_NON_AFFECTED.get(hook_id, "")
        assert baseline_section, (
            f"No baseline captured for non-affected hook: {hook_id}"
        )
        assert current_section == baseline_section, (
            f"Non-affected hook '{hook_id}' section changed!\n"
            f"Baseline excerpt: {baseline_section[:150]}...\n"
            f"Current excerpt: {current_section[:150]}..."
        )
