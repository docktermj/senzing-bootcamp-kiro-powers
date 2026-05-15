"""Example-based unit tests for auto-load-error-recovery feature.

Validates the error-recovery-context hook file structure, prompt content,
category registration, and hook count.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
HOOK_PATH = HOOKS_DIR / "error-recovery-context.kiro.hook"
CATEGORIES_PATH = HOOKS_DIR / "hook-categories.yaml"

EXPECTED_HOOK_COUNT = 26


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def hook_data() -> dict:
    """Load and parse error-recovery-context.kiro.hook."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def prompt(hook_data: dict) -> str:
    """Extract the prompt string from the hook data."""
    return hook_data["then"]["prompt"]


# ===========================================================================
# 4.1: Hook file structure tests
# ===========================================================================


class TestHookFileStructure:
    """Verify hook file parses as valid JSON with correct field values."""

    def test_hook_file_is_valid_json(self):
        """error-recovery-context.kiro.hook parses as valid JSON."""
        with open(HOOK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_name_field(self, hook_data: dict):
        """name field equals 'to help recover from errors'."""
        assert hook_data["name"] == "to help recover from errors"

    def test_version_field(self, hook_data: dict):
        """version field equals '1.0.0'."""
        assert hook_data["version"] == "1.0.0"

    def test_description_contains_shell_and_pitfalls_or_recovery(self, hook_data: dict):
        """description contains 'shell' and either 'pitfalls' or 'recovery'."""
        desc = hook_data["description"].lower()
        assert "shell" in desc
        assert "pitfalls" in desc or "recovery" in desc

    def test_when_type(self, hook_data: dict):
        """when.type equals 'postToolUse'."""
        assert hook_data["when"]["type"] == "postToolUse"

    def test_when_tool_types(self, hook_data: dict):
        """when.toolTypes equals ['shell']."""
        assert hook_data["when"]["toolTypes"] == ["shell"]

    def test_then_type(self, hook_data: dict):
        """then.type equals 'askAgent'."""
        assert hook_data["then"]["type"] == "askAgent"

    def test_then_prompt_is_non_empty_string(self, hook_data: dict):
        """then.prompt is a non-empty string."""
        prompt = hook_data["then"]["prompt"]
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ===========================================================================
# 4.2: Silent processing tests
# ===========================================================================


class TestSilentProcessing:
    """Verify prompt contains silent-processing instructions."""

    def test_produce_no_output_at_all(self, prompt: str):
        """Prompt contains 'produce no output at all'."""
        assert "produce no output at all" in prompt

    def test_exit_code_zero_no_output(self, prompt: str):
        """Prompt contains instruction about exit code zero producing no output."""
        prompt_lower = prompt.lower()
        assert "exit" in prompt_lower and "zero" in prompt_lower
        assert "no output" in prompt_lower

    def test_missing_progress_file_no_output(self, prompt: str):
        """Prompt contains instruction about missing progress file producing no output."""
        # The prompt says: if it does not exist, produce no output at all
        assert "does not exist" in prompt
        assert "produce no output" in prompt


# ===========================================================================
# 4.3: File reference tests
# ===========================================================================


class TestFileReferences:
    """Verify prompt references required files."""

    def test_references_bootcamp_progress(self, prompt: str):
        """Prompt references config/bootcamp_progress.json."""
        assert "config/bootcamp_progress.json" in prompt

    def test_references_common_pitfalls(self, prompt: str):
        """Prompt references common-pitfalls.md."""
        assert "common-pitfalls.md" in prompt

    def test_references_recovery_from_mistakes(self, prompt: str):
        """Prompt references recovery-from-mistakes.md."""
        assert "recovery-from-mistakes.md" in prompt


# ===========================================================================
# 4.4: Module-scoped lookup tests
# ===========================================================================


class TestModuleScopedLookup:
    """Verify prompt contains module-scoped lookup instructions."""

    def test_scope_to_current_module_section(self, prompt: str):
        """Prompt contains instruction about scoping to current module section first."""
        prompt_lower = prompt.lower()
        assert "current module" in prompt_lower and "section" in prompt_lower

    def test_fallback_to_general_pitfalls(self, prompt: str):
        """Prompt contains fallback to 'General Pitfalls'."""
        assert "General Pitfalls" in prompt

    def test_fallback_to_troubleshooting_by_symptom(self, prompt: str):
        """Prompt contains fallback to 'Troubleshooting by Symptom'."""
        assert "Troubleshooting by Symptom" in prompt


# ===========================================================================
# 4.5: Citation and specificity tests
# ===========================================================================


class TestCitationAndSpecificity:
    """Verify prompt contains citation and specificity instructions."""

    def test_cite_source_section(self, prompt: str):
        """Prompt contains instruction about citing the source section."""
        prompt_lower = prompt.lower()
        assert "cite" in prompt_lower or "source section" in prompt_lower

    def test_specific_command_or_action(self, prompt: str):
        """Prompt contains instruction about specific command or action."""
        prompt_lower = prompt.lower()
        assert "specific command" in prompt_lower or "specific action" in prompt_lower \
            or ("command" in prompt_lower and "action" in prompt_lower)

    def test_most_specific_match(self, prompt: str):
        """Prompt contains instruction about most specific match."""
        assert "most specific match" in prompt.lower() or "most specific" in prompt.lower()


# ===========================================================================
# 4.6: SENZ error code tests
# ===========================================================================


class TestSenzErrorCode:
    """Verify prompt references explain_error_code and SENZ prefix."""

    def test_references_explain_error_code(self, prompt: str):
        """Prompt references explain_error_code."""
        assert "explain_error_code" in prompt

    def test_references_senz_prefix(self, prompt: str):
        """Prompt references SENZ error code prefix."""
        assert "SENZ" in prompt


# ===========================================================================
# 4.7: Category registration test
# ===========================================================================


class TestCategoryRegistration:
    """Verify hook-categories.yaml contains error-recovery-context in modules.any."""

    def test_error_recovery_context_in_any_list(self):
        """hook-categories.yaml contains error-recovery-context in the any list."""
        content = CATEGORIES_PATH.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the 'any:' line under modules and check entries after it
        in_any_section = False
        found = False
        for line in lines:
            stripped = line.strip()
            if stripped == "any:":
                in_any_section = True
                continue
            if in_any_section:
                if stripped.startswith("- "):
                    if stripped == "- error-recovery-context":
                        found = True
                        break
                elif stripped and not stripped.startswith("#"):
                    # We've left the any section
                    break

        assert found, "error-recovery-context not found in the 'any' list"


# ===========================================================================
# 4.8: Hook count test
# ===========================================================================


class TestHookCount:
    """Verify total hook count."""

    def test_total_hook_file_count(self):
        """There are exactly 24 .kiro.hook files in the hooks directory."""
        hook_files = list(HOOKS_DIR.glob("*.kiro.hook"))
        assert len(hook_files) == EXPECTED_HOOK_COUNT
