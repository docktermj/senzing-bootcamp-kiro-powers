"""Property-based tests for auto-load error recovery hook infrastructure.

Uses Hypothesis to verify structural invariants across all hook files
and category entries in the senzing-bootcamp hooks directory.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
CATEGORIES_PATH = HOOKS_DIR / "hook-categories.yaml"

VALID_TRIGGERS = {
    "PostFileSave", "PostFileCreate", "PostFileDelete", "Stop",
    "UserPromptSubmit", "PostTaskExec", "PreToolUse", "PostToolUse",
}

VALID_ACTION_TYPES = {"agent", "command"}

TOOL_EVENT_TYPES = {"PreToolUse", "PostToolUse"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_all_category_ids(path: Path) -> list[str]:
    """Extract all hook IDs from hook-categories.yaml.

    Handles two list-item shapes present in the file:
      * Plain list items under ``critical`` / ``modules`` — e.g. ``- ask-bootcamper``.
      * Mapping list items under ``agentstop_order`` — e.g. ``- id: ask-bootcamper``,
        where the hook ID is the value of the ``id:`` key (sibling ``order:`` /
        ``rationale:`` lines are not list items and are skipped naturally).
    """
    text = path.read_text(encoding="utf-8")
    ids: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and not stripped.endswith(":"):
            hook_id = stripped[2:].strip()
            # agentstop_order entries are mappings: "- id: <hook-id>".
            if hook_id.startswith("id:"):
                hook_id = hook_id[len("id:"):].strip()
            if hook_id and not hook_id.endswith(":"):
                ids.append(hook_id)
    return ids


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_hook_file() -> st.SearchStrategy[Path]:
    """Strategy that draws from all .json v1 hook files in the hooks directory."""
    hook_files = sorted(HOOKS_DIR.glob("*.json"))
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
        """For any hook file, it parses as a valid v1 wrapper with required fields."""
        with open(hook_path, encoding="utf-8") as f:
            wrapper = json.load(f)

        assert wrapper.get("version") == "v1", f"{hook_path.name}: missing version v1"
        assert isinstance(wrapper.get("hooks"), list) and wrapper["hooks"], (
            f"{hook_path.name}: missing 'hooks' array"
        )
        entry = wrapper["hooks"][0]

        # Required entry fields
        assert "name" in entry, f"{hook_path.name}: missing 'name'"
        assert "trigger" in entry, f"{hook_path.name}: missing 'trigger'"
        assert "action" in entry, f"{hook_path.name}: missing 'action'"
        assert "type" in entry["action"], f"{hook_path.name}: missing 'action.type'"

        # Valid 1.0 trigger
        trigger = entry["trigger"]
        assert trigger in VALID_TRIGGERS, (
            f"{hook_path.name}: invalid trigger '{trigger}'"
        )

        # Valid action type
        action_type = entry["action"]["type"]
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
        """For any hook ID in categories, a .json hook file exists."""
        expected_path = HOOKS_DIR / f"{hook_id}.json"
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
        """For any tool-event hook, the matcher is a non-empty compilable regex.

        The legacy ``when.toolTypes`` list collapsed into the single 1.0
        ``matcher`` tool-name regex, so tool triggers (PreToolUse/PostToolUse)
        must carry a matcher that compiles.
        """
        with open(hook_path, encoding="utf-8") as f:
            entry = json.load(f)["hooks"][0]

        trigger = entry["trigger"]
        if trigger not in TOOL_EVENT_TYPES:
            return  # Skip non-tool-event hooks

        matcher = entry.get("matcher")
        assert isinstance(matcher, str) and matcher, (
            f"{hook_path.name}: tool trigger {trigger} must carry a matcher"
        )
        try:
            re.compile(matcher)
        except re.error as e:
            pytest.fail(
                f"{hook_path.name}: matcher '{matcher}' is not a valid regex: {e}"
            )
