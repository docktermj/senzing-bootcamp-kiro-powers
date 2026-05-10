"""Property-based tests for auto-load error recovery hook infrastructure.

Uses Hypothesis to verify structural invariants across all hook files
and category entries in the senzing-bootcamp hooks directory.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
CATEGORIES_PATH = HOOKS_DIR / "hook-categories.yaml"

VALID_EVENT_TYPES = {
    "promptSubmit", "preToolUse", "postToolUse",
    "fileEdited", "fileCreated", "fileDeleted",
    "agentStop", "userTriggered", "postTaskExecution", "preTaskExecution",
}

VALID_ACTION_TYPES = {"askAgent", "runCommand"}

VALID_TOOL_CATEGORIES = {"read", "write", "shell", "web", "spec", "*"}

TOOL_EVENT_TYPES = {"preToolUse", "postToolUse"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_all_category_ids(path: Path) -> list[str]:
    """Extract all hook IDs from hook-categories.yaml."""
    text = path.read_text(encoding="utf-8")
    ids: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and not stripped.endswith(":"):
            hook_id = stripped[2:].strip()
            if hook_id and not hook_id.endswith(":"):
                ids.append(hook_id)
    return ids


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_hook_file() -> st.SearchStrategy[Path]:
    """Strategy that draws from all .kiro.hook files in the hooks directory."""
    hook_files = sorted(HOOKS_DIR.glob("*.kiro.hook"))
    return st.sampled_from(hook_files)


def st_category_hook_id() -> st.SearchStrategy[str]:
    """Strategy that draws from all hook IDs listed in hook-categories.yaml."""
    hook_ids = _parse_all_category_ids(CATEGORIES_PATH)
    return st.sampled_from(sorted(hook_ids))


# ===========================================================================
# Property 1: Hook structural validity
# Feature: auto-load-error-recovery, Property 1: Hook structural validity
# ===========================================================================


class TestHookStructuralValidity:
    """Property 1: Hook structural validity.

    For any .kiro.hook file, it parses as valid JSON with all required fields
    and valid event/action types.

    Validates: Requirements 1.1, 6.1, 6.2, 6.3, 6.4, 6.5
    """

    @given(hook_path=st_hook_file())
    @settings(max_examples=100)
    def test_hook_parses_as_valid_json_with_required_fields(self, hook_path: Path):
        """For any hook file, it parses as valid JSON with required fields."""
        with open(hook_path, encoding="utf-8") as f:
            data = json.load(f)

        # Required top-level fields
        assert "name" in data, f"{hook_path.name}: missing 'name'"
        assert "version" in data, f"{hook_path.name}: missing 'version'"

        # Required nested fields
        assert "when" in data, f"{hook_path.name}: missing 'when'"
        assert "type" in data["when"], f"{hook_path.name}: missing 'when.type'"
        assert "then" in data, f"{hook_path.name}: missing 'then'"
        assert "type" in data["then"], f"{hook_path.name}: missing 'then.type'"

        # Valid event type
        event_type = data["when"]["type"]
        assert event_type in VALID_EVENT_TYPES, (
            f"{hook_path.name}: invalid event type '{event_type}'"
        )

        # Valid action type
        action_type = data["then"]["type"]
        assert action_type in VALID_ACTION_TYPES, (
            f"{hook_path.name}: invalid action type '{action_type}'"
        )


# ===========================================================================
# Property 2: Category-to-file bidirectional consistency
# Feature: auto-load-error-recovery, Property 2: Category-to-file bidirectional
#   consistency
# ===========================================================================


class TestCategoryToFileBidirectionalConsistency:
    """Property 2: Category-to-file bidirectional consistency.

    For any hook ID in hook-categories.yaml, a corresponding .kiro.hook file exists.

    Validates: Requirements 5.1, 5.2
    """

    @given(hook_id=st_category_hook_id())
    @settings(max_examples=100)
    def test_category_hook_id_has_corresponding_file(self, hook_id: str):
        """For any hook ID in categories, a .kiro.hook file exists."""
        expected_path = HOOKS_DIR / f"{hook_id}.kiro.hook"
        assert expected_path.is_file(), (
            f"Category entry '{hook_id}' has no corresponding file: {expected_path}"
        )


# ===========================================================================
# Property 3: ToolType validity for tool-event hooks
# Feature: auto-load-error-recovery, Property 3: ToolType validity for
#   tool-event hooks
# ===========================================================================


class TestToolTypeValidity:
    """Property 3: ToolType validity for tool-event hooks.

    For any postToolUse/preToolUse hook, every toolTypes entry is a valid
    category or compilable regex.

    Validates: Requirements 1.6, 6.3
    """

    @given(hook_path=st_hook_file())
    @settings(max_examples=100)
    def test_tool_event_hooks_have_valid_tool_types(self, hook_path: Path):
        """For any tool-event hook, toolTypes entries are valid categories or regex."""
        with open(hook_path, encoding="utf-8") as f:
            data = json.load(f)

        event_type = data["when"]["type"]
        if event_type not in TOOL_EVENT_TYPES:
            return  # Skip non-tool-event hooks

        tool_types = data["when"].get("toolTypes", [])
        assert isinstance(tool_types, list), (
            f"{hook_path.name}: toolTypes must be a list"
        )
        assert len(tool_types) > 0, (
            f"{hook_path.name}: toolTypes must be non-empty for {event_type}"
        )

        for tt in tool_types:
            if tt in VALID_TOOL_CATEGORIES:
                continue  # Valid category
            # Try as regex
            try:
                re.compile(tt)
            except re.error as e:
                pytest.fail(
                    f"{hook_path.name}: invalid toolType '{tt}' — "
                    f"not a valid category or regex: {e}"
                )
