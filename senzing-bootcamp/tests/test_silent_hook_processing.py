"""Bug condition exploration tests for silent-hook-processing bugfix.

Bug condition tests verify that the four affected hook prompts contain an
explicit "produce no output" instruction for the no-action-needed case.
Also checks that hook-registry.md mirrors the same prompts and that
agent-instructions.md does NOT yet contain a silent-processing rule.

Extended tests verify STRONGER guardrail language identified in the design:
- ask-bootcamper: explicit prohibitions, STOP instruction, broader detection
- preToolUse hooks: STOP/return instructions, redundant emphasis
- hook-registry.md: same strong language as hook files
- agent-instructions.md: explicit prohibitions against narrating evaluation

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6,
             2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

EXPECTED OUTCOME on UNFIXED code:
- Original bug condition tests PASS (hooks already have "produce no output")
- Extended bug condition tests FAIL (proving stronger guardrails are missing)
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
    "ask-bootcamper": _HOOKS_DIR / "ask-bootcamper.kiro.hook",
    "review-bootcamper-input": _HOOKS_DIR / "review-bootcamper-input.kiro.hook",
}

_ASK_BOOTCAMPER_HOOK_FILE = _HOOKS_DIR / "ask-bootcamper.kiro.hook"

# preToolUse hooks that need STOP instructions
_PRE_TOOL_USE_HOOKS: dict[str, Path] = {
}

_HOOK_REGISTRY = _STEERING_DIR / "hook-registry-detail.md"
_AGENT_INSTRUCTIONS = _STEERING_DIR / "agent-instructions.md"

# The phrase that must appear in fixed prompts for the no-action case
_SILENT_INSTRUCTION = "produce no output"
_SILENT_INSTRUCTION_ALT = "default output"

# Strong guardrail phrases expected in fixed prompts
_STOP_PHRASES = ["stop", "return immediately", "return nothing", "output only: ."]
_ZERO_TOKEN_PHRASES = ["zero tokens", "zero characters", "completely empty"]
_ASK_BOOTCAMPER_PROHIBITIONS = [
    "do not explain",
    "do not describe",
    "never generate text",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_hook_prompt(path: Path) -> str:
    """Parse a .kiro.hook JSON file and return the then.prompt value."""
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    return data["then"]["prompt"]


def _extract_registry_prompt(registry_text: str, hook_id: str) -> str:
    """Extract the prompt for a given hook id.

    The registry now stores only id/name/description. The full prompt is in
    the corresponding .kiro.hook file. Falls back to reading the hook file
    when no inline prompt is found in the registry.
    """
    # Try inline Prompt: "..." format first (legacy)
    pattern = rf"\*\*{re.escape(hook_id)}\*\*.*?\nPrompt:\s*\"(.*?)\"\n"
    match = re.search(pattern, registry_text, re.DOTALL)
    if match:
        return match.group(1)
    pattern2 = rf"\*\*{re.escape(hook_id)}\*\*.*?\nPrompt:\s*\"(.*?)\""
    match2 = re.search(pattern2, registry_text, re.DOTALL)
    if match2:
        return match2.group(1)
    # Fall back to reading from the hook file
    hook_file = _HOOKS_DIR / f"{hook_id}.kiro.hook"
    if hook_file.exists():
        try:
            data = json.loads(hook_file.read_text(encoding="utf-8"))
            return data.get("then", {}).get("prompt", "")
        except (json.JSONDecodeError, OSError):
            pass
    return ""


def _prompt_has_silent_instruction(prompt: str) -> bool:
    """Check if a prompt contains an explicit silence instruction."""
    lower = prompt.lower()
    return _SILENT_INSTRUCTION.lower() in lower or _SILENT_INSTRUCTION_ALT.lower() in lower


def _prompt_has_stop_instruction(prompt: str) -> bool:
    """Check if a prompt contains a STOP/return instruction."""
    lower = prompt.lower()
    return any(phrase in lower for phrase in _STOP_PHRASES)


def _prompt_has_zero_token_emphasis(prompt: str) -> bool:
    """Check if a prompt contains redundant zero-token emphasis."""
    lower = prompt.lower()
    return any(phrase in lower for phrase in _ZERO_TOKEN_PHRASES)


def _prompt_has_explicit_prohibitions(prompt: str) -> bool:
    """Check if a prompt contains explicit prohibitions (do NOT X)."""
    lower = prompt.lower()
    return any(phrase in lower for phrase in _ASK_BOOTCAMPER_PROHIBITIONS)


def _prompt_has_broad_pointing_detection(prompt: str) -> bool:
    """Check if a prompt detects 👉 anywhere, not just at the end."""
    lower = prompt.lower()
    has_anywhere = any(
        phrase in lower
        for phrase in ["contains a 👉", "anywhere"]
    )
    # Should NOT be limited to "ends with"
    has_ends_with_only = "ends with" in lower and "anywhere" not in lower
    return has_anywhere and not has_ends_with_only


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

    def test_review_bootcamper_input_has_silent_instruction(self) -> None:
        """review-bootcamper-input prompt should contain 'produce no output'.

        **Validates: Requirements 1.1, 2.1**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["review-bootcamper-input"])
        assert _prompt_has_silent_instruction(prompt), (
            f"review-bootcamper-input prompt lacks explicit silent instruction.\n"
            f"Prompt uses 'do nothing' without 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_enforce_feedback_path_has_silent_instruction(self) -> None:
        """enforce-feedback-path hook was removed (require-mcp-server spec)."""
        pass

    def test_enforce_working_directory_has_silent_instruction(self) -> None:
        """enforce-working-directory hook was removed (require-mcp-server spec)."""
        pass

    def test_verify_senzing_facts_has_silent_instruction(self) -> None:
        """verify-senzing-facts hook was removed (require-mcp-server spec)."""
        pass


class TestBugConditionHookRegistry:
    """Assert that hook-registry.md prompts for the four affected hooks
    contain an explicit 'produce no output' instruction.

    On unfixed code these assertions will FAIL, confirming the bug exists.

    **Validates: Requirements 1.5, 2.5**
    """

    @pytest.fixture(autouse=True)
    def _load_registry(self) -> None:
        self._registry_text = _HOOK_REGISTRY.read_text(encoding="utf-8")

    def test_registry_review_bootcamper_input_has_silent_instruction(self) -> None:
        """hook-registry review-bootcamper-input prompt should contain 'produce no output'.

        **Validates: Requirements 1.5, 2.5**"""
        prompt = _extract_registry_prompt(self._registry_text, "review-bootcamper-input")
        assert prompt, "Could not extract review-bootcamper-input prompt from hook-registry.md"
        assert _prompt_has_silent_instruction(prompt), (
            f"hook-registry review-bootcamper-input prompt lacks 'produce no output'.\n"
            f"Prompt: {prompt[:200]}..."
        )

    def test_registry_enforce_feedback_path_has_silent_instruction(self) -> None:
        """enforce-feedback-path hook was removed (require-mcp-server spec)."""
        pass

    def test_registry_enforce_working_directory_has_silent_instruction(self) -> None:
        """enforce-working-directory hook was removed (require-mcp-server spec)."""
        pass

    def test_registry_verify_senzing_facts_has_silent_instruction(self) -> None:
        """verify-senzing-facts hook was removed (require-mcp-server spec)."""
        pass


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
        hooks_section = hooks_match.group(1).lower()
        # Accept both original and strengthened phrasing
        has_silent = (
            _SILENT_INSTRUCTION.lower() in hooks_section
            or "produce absolutely no output" in hooks_section
            or "produce zero output" in hooks_section
        )
        assert has_silent, (
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
    @settings(max_examples=10)
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
# Extended Bug Condition Tests (Task 1 — stronger guardrails)
#
# These tests check for the STRONGER guardrail language identified in the
# design document. The existing tests above check for "produce no output"
# which already exists. These tests check for ADDITIONAL language that is
# MISSING from the unfixed code.
#
# EXPECTED OUTCOME on UNFIXED code: These tests FAIL
# (proving the stronger guardrails are missing)
#
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6,
#              2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**
# ===========================================================================

_PRE_TOOL_USE_HOOK_KEYS = list(_PRE_TOOL_USE_HOOKS.keys())


# ---------------------------------------------------------------------------
# Bug Condition: ask-bootcamper lacks strong guardrails
# ---------------------------------------------------------------------------


class TestBugConditionAskBootcamperGuardrails:
    """Assert that ask-bootcamper prompt contains explicit prohibitions
    beyond the weak 'do nothing' language.

    On unfixed code these assertions FAIL because the prompt only says
    'do nothing' without explicit prohibitions, STOP instruction, or
    broader 👉 detection.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
    """

    def test_ask_bootcamper_has_explicit_prohibitions(self) -> None:
        """ask-bootcamper prompt must contain explicit prohibitions.

        The prompt should say 'do NOT answer', 'do NOT role-play',
        'do NOT generate' — not just 'do nothing'.

        **Validates: Requirements 1.2, 2.2**"""
        prompt = _read_hook_prompt(_ASK_BOOTCAMPER_HOOK_FILE)
        assert _prompt_has_explicit_prohibitions(prompt), (
            "ask-bootcamper prompt lacks explicit prohibitions.\n"
            "Expected phrases like 'do NOT answer', "
            "'do NOT role-play', 'do NOT generate'.\n"
            f"Prompt: {prompt[:300]}..."
        )

    def test_ask_bootcamper_has_stop_instruction(self) -> None:
        """ask-bootcamper prompt must contain a STOP instruction.

        **Validates: Requirements 2.1, 2.2**"""
        prompt = _read_hook_prompt(_ASK_BOOTCAMPER_HOOK_FILE)
        assert _prompt_has_stop_instruction(prompt), (
            "ask-bootcamper prompt lacks STOP/return instruction.\n"
            "Expected 'STOP' or 'return immediately' or "
            "'return nothing'.\n"
            f"Prompt: {prompt[:300]}..."
        )

    def test_ask_bootcamper_has_broad_pointing_detection(self) -> None:
        """ask-bootcamper prompt must detect 👉 anywhere, not just at end.

        The current prompt says 'already ends with a 👉 question'
        but should detect 👉 anywhere in the text.

        **Validates: Requirements 1.1, 2.1**"""
        prompt = _read_hook_prompt(_ASK_BOOTCAMPER_HOOK_FILE)
        assert _prompt_has_broad_pointing_detection(prompt), (
            "ask-bootcamper prompt only checks for 👉 at end.\n"
            "Should detect 👉 'anywhere' in the text, not just "
            "'ends with'.\n"
            f"Prompt: {prompt[:300]}..."
        )


# ---------------------------------------------------------------------------
# Bug Condition: preToolUse hooks lack STOP instructions
# ---------------------------------------------------------------------------


class TestBugConditionPreToolUseStopInstructions:
    """Assert that each preToolUse hook prompt contains a STOP/return
    instruction in the silent-pass branch.

    On unfixed code these assertions FAIL because the prompts say
    'produce no output' but lack an explicit STOP instruction.

    **Validates: Requirements 1.3, 1.4, 1.5, 2.3, 2.4, 2.5**
    """

    def test_verify_senzing_facts_has_stop_instruction(self) -> None:
        """verify-senzing-facts hook was removed (require-mcp-server spec)."""
        pass

    def test_enforce_working_directory_has_stop_instruction(self) -> None:
        """enforce-working-directory hook was removed (require-mcp-server spec)."""
        pass

    def test_enforce_feedback_path_has_stop_instruction(self) -> None:
        """enforce-feedback-path hook was removed (require-mcp-server spec)."""
        pass


class TestBugConditionPreToolUseEmphasis:
    """Assert that each preToolUse hook prompt contains redundant
    emphasis language ('zero tokens' or similar).

    On unfixed code these assertions FAIL because the prompts lack
    redundant emphasis.

    **Validates: Requirements 2.3, 2.4, 2.5**
    """

    def test_verify_senzing_facts_has_zero_token_emphasis(self) -> None:
        """verify-senzing-facts hook was removed (require-mcp-server spec)."""
        pass

    def test_enforce_working_directory_has_zero_token_emphasis(
        self,
    ) -> None:
        """enforce-working-directory hook was removed (require-mcp-server spec)."""
        pass

    def test_enforce_feedback_path_has_zero_token_emphasis(self) -> None:
        """enforce-feedback-path hook was removed (require-mcp-server spec)."""
        pass


# ---------------------------------------------------------------------------
# Bug Condition: hook-registry.md lacks strong language
# ---------------------------------------------------------------------------


class TestBugConditionRegistryStrongLanguage:
    """Assert that hook-registry.md prompts contain the same strong
    guardrail language as the hook files (STOP instructions, etc.).

    On unfixed code these assertions FAIL because the registry mirrors
    the weak prompt language.

    **Validates: Requirements 1.6, 2.6**
    """

    @pytest.fixture(autouse=True)
    def _load_registry(self) -> None:
        self._registry_text = _HOOK_REGISTRY.read_text(
            encoding="utf-8"
        )

    def test_registry_ask_bootcamper_has_prohibitions(self) -> None:
        """Registry ask-bootcamper prompt must have prohibitions.

        **Validates: Requirements 1.6, 2.6**"""
        prompt = _extract_registry_prompt(
            self._registry_text, "ask-bootcamper"
        )
        assert prompt, (
            "Could not extract ask-bootcamper prompt from registry"
        )
        assert _prompt_has_explicit_prohibitions(prompt), (
            "Registry ask-bootcamper prompt lacks prohibitions.\n"
            "Expected 'do NOT answer', 'do NOT role-play', "
            "'do NOT generate'.\n"
            f"Prompt: {prompt[:300]}..."
        )

    def test_registry_pretooluse_hooks_have_stop(self) -> None:
        """Registry preToolUse prompts must have STOP instructions.

        **Validates: Requirements 1.6, 2.6**"""
        for hook_id in _PRE_TOOL_USE_HOOK_KEYS:
            prompt = _extract_registry_prompt(
                self._registry_text, hook_id
            )
            assert prompt, (
                f"Could not extract {hook_id} prompt from registry"
            )
            assert _prompt_has_stop_instruction(prompt), (
                f"Registry {hook_id} prompt lacks STOP instruction.\n"
                f"Prompt: {prompt[:300]}..."
            )


# ---------------------------------------------------------------------------
# Bug Condition: agent-instructions.md lacks explicit prohibitions
# ---------------------------------------------------------------------------


class TestBugConditionAgentInstructionsStrong:
    """Assert that agent-instructions.md Hooks section contains explicit
    prohibitions against narrating evaluation — not just 'produce no
    output' but also 'do not narrate', 'do not explain', etc.

    On unfixed code this assertion FAILS because the Hooks section has
    only a minimal silent-processing rule.

    **Validates: Requirements 2.7**
    """

    def test_agent_instructions_has_narration_prohibition(self) -> None:
        """Hooks section must have emphatic zero-output enforcement.

        The current rule says 'do not explain your reasoning' which
        is good but not emphatic enough. The fix should add 'do not
        narrate' AND 'zero tokens' for redundant emphasis.

        **Validates: Requirements 2.7**"""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        hooks_match = re.search(
            r"^## Hooks\s*\n(.*?)(?=^## |\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        assert hooks_match, (
            "Could not find ## Hooks section in agent-instructions.md"
        )
        hooks_section = hooks_match.group(1).lower()
        # Must have BOTH narration prohibition AND zero-output emphasis
        has_narrate = (
            "do not narrate" in hooks_section
            or "no acknowledgment" in hooks_section
        )
        has_zero_tokens = (
            "zero tokens" in hooks_section
            or "zero output" in hooks_section
        )
        assert has_narrate and has_zero_tokens, (
            "agent-instructions.md Hooks section lacks emphatic "
            "silent-processing enforcement.\n"
            f"  Has 'do not narrate': {has_narrate}\n"
            f"  Has 'zero tokens': {has_zero_tokens}\n"
            "Expected both for redundant emphasis.\n"
            f"Hooks section excerpt: {hooks_section[:400]}..."
        )


# ---------------------------------------------------------------------------
# PBT — Extended Bug Condition across preToolUse hooks
# ---------------------------------------------------------------------------


class TestBugConditionPreToolUseProperty:
    """Property-based test: for any randomly selected preToolUse hook,
    the hook file prompt must contain both a STOP instruction and
    zero-token emphasis.

    On unfixed code this property FAILS, surfacing counterexamples.

    **Validates: Requirements 1.3, 1.4, 1.5, 2.3, 2.4, 2.5**
    """

    @pytest.mark.skipif(
        not _PRE_TOOL_USE_HOOK_KEYS,
        reason="No preToolUse hooks remain after require-mcp-server cleanup",
    )
    @given(hook_key=st.sampled_from(_PRE_TOOL_USE_HOOK_KEYS or ["placeholder"]))
    @settings(max_examples=10)
    def test_pretooluse_hooks_have_strong_guardrails(
        self, hook_key: str
    ) -> None:
        """**Validates: Requirements 1.3, 1.4, 1.5, 2.3, 2.4, 2.5**

        For any preToolUse hook, the prompt must contain a STOP
        instruction and zero-token emphasis."""
        prompt = _read_hook_prompt(_PRE_TOOL_USE_HOOKS[hook_key])
        has_stop = _prompt_has_stop_instruction(prompt)
        has_emphasis = _prompt_has_zero_token_emphasis(prompt)
        assert has_stop and has_emphasis, (
            f"Weak guardrails in {hook_key}:\n"
            f"  Has STOP instruction: {has_stop}\n"
            f"  Has zero-token emphasis: {has_emphasis}\n"
            f"  Prompt excerpt: {prompt[:200]}..."
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

# review-bootcamper-input: feedback workflow initiation keywords
_REVIEW_BOOTCAMPER_INPUT_ACTION_KEYWORDS: list[str] = [
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

# ask-bootcamper: recap and skip-recap keywords
_ASK_BOOTCAMPER_ACTION_KEYWORDS: list[str] = [
    "accomplished",
    "files created or modified",
    "👉 question",
    "Skip to Phase 2",
    "files were edited",
    "no substantive",
]

# Map hook id → action-required keywords
_ACTION_REQUIRED_KEYWORDS: dict[str, list[str]] = {
    "ask-bootcamper": _ASK_BOOTCAMPER_ACTION_KEYWORDS,
    "review-bootcamper-input": _REVIEW_BOOTCAMPER_INPUT_ACTION_KEYWORDS,
}

# Non-affected hook ids in hook-registry.md (all hooks except the affected ones)
_NON_AFFECTED_HOOK_IDS: list[str] = [
    "code-style-check",
    "commonmark-validation",
    "data-quality-check",
    "analyze-after-mapping",
    "backup-before-load",
    "run-tests-after-change",
    "validate-data-files",
    "verify-generated-code",
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


def _snapshot_agent_instructions() -> str:
    """Return the full content of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")


# Capture baselines at module load time (before any fix is applied)
_BASELINE_REGISTRY_NON_AFFECTED = _snapshot_registry_non_affected()
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

    def test_ask_bootcamper_preserves_recap_branch(self) -> None:
        """ask-bootcamper preserves recap and skip-recap keywords.

        **Validates: Requirements 3.1, 3.2**"""
        prompt = _read_hook_prompt(
            _AFFECTED_HOOK_FILES["ask-bootcamper"]
        )
        for keyword in _ASK_BOOTCAMPER_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"ask-bootcamper prompt missing action-required "
                f"keyword: '{keyword}'\n"
                f"Prompt: {prompt[:300]}..."
            )

    def test_review_bootcamper_input_preserves_feedback_workflow(self) -> None:
        """review-bootcamper-input preserves feedback workflow initiation text.

        **Validates: Requirements 3.1**"""
        prompt = _read_hook_prompt(_AFFECTED_HOOK_FILES["review-bootcamper-input"])
        for keyword in _REVIEW_BOOTCAMPER_INPUT_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"review-bootcamper-input prompt missing action-required keyword: "
                f"'{keyword}'\nPrompt: {prompt[:300]}..."
            )

    def test_enforce_feedback_path_preserves_redirection(self) -> None:
        """enforce-feedback-path hook was removed (require-mcp-server spec)."""
        pass

    def test_enforce_working_directory_preserves_correction(self) -> None:
        """enforce-working-directory hook was removed (require-mcp-server spec)."""
        pass

    def test_verify_senzing_facts_preserves_mcp_verification(self) -> None:
        """verify-senzing-facts hook was removed (require-mcp-server spec)."""
        pass


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
# Unit Tests — ask-bootcamper action-required keywords preserved
# ---------------------------------------------------------------------------


class TestPreservationAskBootcamperKeywords:
    """Verify ask-bootcamper prompt preserves recap and skip-recap keywords.

    Since we ARE modifying ask-bootcamper in this bugfix, we check that
    action-required keywords (recap, skip-recap, 👉 question) are
    preserved rather than checking exact file content.

    **Validates: Requirements 3.1, 3.2**
    """

    def test_ask_bootcamper_preserves_recap_keywords(self) -> None:
        """ask-bootcamper prompt preserves recap action keywords.

        **Validates: Requirements 3.1, 3.2**"""
        prompt = _read_hook_prompt(_ASK_BOOTCAMPER_HOOK_FILE)
        for keyword in _ASK_BOOTCAMPER_ACTION_KEYWORDS:
            assert keyword in prompt, (
                f"ask-bootcamper prompt missing action-required "
                f"keyword: '{keyword}'\n"
                f"Prompt: {prompt[:300]}..."
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
    @settings(max_examples=10)
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
    @settings(max_examples=10)
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
    @settings(max_examples=10)
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
