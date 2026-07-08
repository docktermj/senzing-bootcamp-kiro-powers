"""Property-based tests for hook-gaps-modules-1-and-3 feature.

Uses Hypothesis to verify universal invariants over the hook infrastructure:
- Property 1: All modules 1–11 have at least one hook
- Property 2: Every hook ID in categories has a corresponding file
- Property 3: Every .kiro.hook file is structurally valid

Feature: hook-gaps-modules-1-and-3
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from sync_hook_registry import (
    CATEGORIES_PATH,
    HOOKS_DIR,
    discover_hook_files,
    load_category_mapping,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_TRIGGERS = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "Stop",
    "UserPromptSubmit",
    "PostTaskExec",
    "PreToolUse",
    "PostToolUse",
}

VALID_ACTION_TYPES = {"agent", "command"}


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

def st_module_number() -> st.SearchStrategy[int]:
    """Strategy that generates module numbers from 1 to 11."""
    return st.integers(min_value=1, max_value=11)


def st_hook_id_from_categories() -> st.SearchStrategy[str]:
    """Strategy that samples hook IDs from the modules section of hook-categories.yaml."""
    mapping = load_category_mapping(CATEGORIES_PATH)
    module_hook_ids = [
        cat.hook_id
        for cat in mapping.values()
        if cat.category == "module" and cat.module_number is not None
    ]
    assert len(module_hook_ids) > 0, "No module hook IDs found in categories"
    return st.sampled_from(module_hook_ids)


def st_hook_file_path() -> st.SearchStrategy[Path]:
    """Strategy that samples from all .kiro.hook file paths."""
    hook_files = discover_hook_files(HOOKS_DIR)
    assert len(hook_files) > 0, "No hook files found"
    return st.sampled_from(hook_files)


# ---------------------------------------------------------------------------
# Helper: load categories as module-number → hook-id-list mapping
# ---------------------------------------------------------------------------

def _load_modules_mapping() -> dict[int, list[str]]:
    """Load hook-categories.yaml and return {module_number: [hook_ids]}.

    Reads the YAML directly instead of using ``load_category_mapping``,
    which flattens multi-module hooks by overwriting earlier module entries.
    """
    import yaml
    data = yaml.safe_load(CATEGORIES_PATH.read_text(encoding="utf-8")) or {}
    modules_raw = (data.get("modules") or {})
    modules: dict[int, list[str]] = {}
    for key, hook_ids in modules_raw.items():
        if key == "any":
            continue
        try:
            mod_num = int(key)
        except (TypeError, ValueError):
            continue
        modules[mod_num] = list(hook_ids or [])
    return modules


# ===========================================================================
# Property 1: All modules have hook coverage
# Feature: hook-gaps-modules-1-and-3, Property 1: All modules have hook coverage
# Validates: Requirements 7.1
# ===========================================================================

class TestProperty1AllModulesHaveCoverage:
    """For any module number 1–11, hook-categories.yaml lists at least one hook."""

    @given(module_num=st_module_number())
    @settings(max_examples=100)
    def test_every_module_has_at_least_one_hook(self, module_num: int):
        """Property 1: Module {module_num} has at least one hook in categories."""
        modules = _load_modules_mapping()
        assert module_num in modules, (
            f"Module {module_num} has no hooks in hook-categories.yaml"
        )
        assert len(modules[module_num]) >= 1, (
            f"Module {module_num} has an empty hook list"
        )


# ===========================================================================
# Property 2: Category-to-file bidirectional consistency
# Feature: hook-gaps-modules-1-and-3, Property 2: Category-to-file consistency
# Validates: Requirements 7.3
# ===========================================================================

class TestProperty2CategoryToFileConsistency:
    """For any hook ID in modules section, a corresponding .kiro.hook file exists."""

    @given(hook_id=st_hook_id_from_categories())
    @settings(max_examples=100)
    def test_hook_id_has_corresponding_file(self, hook_id: str):
        """Property 2: Hook ID '{hook_id}' has a matching .json file."""
        expected_path = HOOKS_DIR / f"{hook_id}.json"
        assert expected_path.is_file(), (
            f"Hook ID '{hook_id}' listed in categories but file "
            f"'{expected_path}' does not exist"
        )


# ===========================================================================
# Property 3: Hook structural validity
# Feature: hook-gaps-modules-1-and-3, Property 3: Hook structural validity
# Validates: Requirements 4.2, 4.3, 4.4, 4.5
# ===========================================================================

class TestProperty3HookStructuralValidity:
    """For any .kiro.hook file, it parses as valid JSON with required fields."""

    @given(hook_path=st_hook_file_path())
    @settings(max_examples=100)
    def test_hook_file_is_valid_and_complete(self, hook_path: Path):
        """Property 3: Hook file '{hook_path.name}' is a structurally valid v1 wrapper."""
        # Must parse as a valid v1 wrapper
        wrapper = json.loads(hook_path.read_text(encoding="utf-8"))
        assert isinstance(wrapper, dict), f"{hook_path.name} is not a JSON object"
        assert wrapper.get("version") == "v1", f"{hook_path.name} missing version v1"
        assert isinstance(wrapper.get("hooks"), list) and wrapper["hooks"], (
            f"{hook_path.name} missing 'hooks' array"
        )
        entry = wrapper["hooks"][0]

        # Must have all required v1 entry fields
        for field in ("name", "trigger", "action"):
            assert field in entry, f"{hook_path.name} missing required field '{field}'"

        # trigger must be valid
        assert entry["trigger"] in VALID_TRIGGERS, (
            f"{hook_path.name} has invalid trigger: '{entry['trigger']}'"
        )

        # action.type must be valid
        action = entry["action"]
        assert "type" in action, f"{hook_path.name} missing action.type"
        assert action["type"] in VALID_ACTION_TYPES, (
            f"{hook_path.name} has invalid action.type: '{action['type']}'"
        )

        # If agent action, must have non-empty prompt
        if action["type"] == "agent":
            assert "prompt" in action, f"{hook_path.name} missing action.prompt"
            assert len(action["prompt"]) > 0, f"{hook_path.name} has empty prompt"
