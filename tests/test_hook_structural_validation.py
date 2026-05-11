"""Structural validation tests for all 25 hooks.

Verifies JSON structure, required fields, event types, conditional fields,
prompt length, version format, and hook file count.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    FILE_EVENT_TYPES,
    HOOKS_DIR,
    REQUIRED_FIELDS,
    SEMVER_PATTERN,
    TOOL_EVENT_TYPES,
    VALID_EVENT_TYPES,
    get_hook_files,
    load_all_hooks,
    validate_conditional_fields,
    validate_required_fields,
)

# ---------------------------------------------------------------------------
# Module-level data for parametrization
# ---------------------------------------------------------------------------

_hook_files = get_hook_files()
_hook_data = load_all_hooks()
_hook_ids = [hook_id for hook_id, _ in _hook_data]


# ===========================================================================
# TestHookJsonStructure — Req 2.1, 2.2
# ===========================================================================

class TestHookJsonStructure:
    """Verify all 25 hooks parse as valid JSON and contain required fields."""

    @pytest.mark.parametrize("hook_path", _hook_files, ids=[p.name for p in _hook_files])
    def test_parses_as_valid_json(self, hook_path: Path):
        """Each hook file parses as valid JSON (Req 2.1)."""
        try:
            with open(hook_path, encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{hook_path.name} did not parse as a JSON object"
        except json.JSONDecodeError as exc:
            pytest.fail(f'"{hook_path.name}" is not valid JSON: {exc}')

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_contains_all_required_fields(self, hook_id: str, data: dict):
        """Each hook contains all required fields (Req 2.2)."""
        missing = validate_required_fields(data)
        assert not missing, (
            f'"{hook_id}" missing required field(s): {", ".join(missing)}'
        )


# ===========================================================================
# TestHookEventTypes — Req 2.3
# ===========================================================================

class TestHookEventTypes:
    """Verify every hook's when.type is a valid Event_Type."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_event_type_is_valid(self, hook_id: str, data: dict):
        """Each hook's when.type is in VALID_EVENT_TYPES (Req 2.3)."""
        event_type = data.get("when", {}).get("type", "")
        assert event_type in VALID_EVENT_TYPES, (
            f'"{hook_id}" has invalid event type: "{event_type}"'
        )


# ===========================================================================
# TestHookPromptLength — Req 2.4
# ===========================================================================

class TestHookPromptLength:
    """Verify every hook's then.prompt is non-empty with at least 20 characters."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_prompt_at_least_20_chars(self, hook_id: str, data: dict):
        """Each hook's then.prompt is non-empty and >= 20 chars (Req 2.4)."""
        prompt = data.get("then", {}).get("prompt", "")
        assert isinstance(prompt, str) and len(prompt) >= 20, (
            f'"{hook_id}" prompt is {len(prompt)} chars, minimum is 20'
        )


# ===========================================================================
# TestHookConditionalFields — Req 2.5, 2.6
# ===========================================================================

class TestHookConditionalFields:
    """Verify file-event hooks have when.patterns and tool-event hooks have when.toolTypes."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_file_event_hooks_have_patterns(self, hook_id: str, data: dict):
        """File-event hooks have non-empty when.patterns (Req 2.5)."""
        event_type = data.get("when", {}).get("type", "")
        if event_type not in FILE_EVENT_TYPES:
            pytest.skip("Not a file event hook")
        patterns = data.get("when", {}).get("patterns")
        assert patterns and isinstance(patterns, list) and len(patterns) > 0, (
            f'"{hook_id}" with event type "{event_type}" missing when.patterns'
        )

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_tool_event_hooks_have_tool_types(self, hook_id: str, data: dict):
        """Tool-event hooks have non-empty when.toolTypes (Req 2.6)."""
        event_type = data.get("when", {}).get("type", "")
        if event_type not in TOOL_EVENT_TYPES:
            pytest.skip("Not a tool event hook")
        tool_types = data.get("when", {}).get("toolTypes")
        assert tool_types and isinstance(tool_types, list) and len(tool_types) > 0, (
            f'"{hook_id}" with event type "{event_type}" missing when.toolTypes'
        )


# ===========================================================================
# TestHookVersionFormat — Req 2.7, 7.1, 7.3
# ===========================================================================

class TestHookVersionFormat:
    """Verify version matches semver format with no leading zeros."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_version_is_valid_semver(self, hook_id: str, data: dict):
        """Each hook's version matches X.Y.Z semver format (Req 2.7, 7.1)."""
        version = data.get("version", "")
        assert SEMVER_PATTERN.match(version), (
            f'"{hook_id}" has invalid version: "{version}" '
            f"(expected format: major.minor.patch with no leading zeros)"
        )

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_version_no_leading_zeros(self, hook_id: str, data: dict):
        """No version component has leading zeros (Req 7.3)."""
        version = data.get("version", "")
        parts = version.split(".")
        if len(parts) == 3:
            for part in parts:
                if len(part) > 1 and part.startswith("0"):
                    pytest.fail(
                        f'"{hook_id}" version "{version}" has leading zero in component "{part}"'
                    )


# ===========================================================================
# TestHookCount — Req 2.8
# ===========================================================================

class TestHookCount:
    """Verify the expected number of .kiro.hook files exist."""

    def test_hook_file_count_matches_categories(self):
        """Hook file count matches the total entries in hook-categories.yaml (Req 2.8)."""
        from hook_test_helpers import parse_categories_yaml
        categories = parse_categories_yaml()
        expected_count = sum(len(ids) for ids in categories.values())
        hook_files = get_hook_files()
        assert len(hook_files) == expected_count, (
            f"Expected {expected_count} hook files (from categories YAML), "
            f"found {len(hook_files)}: {[p.name for p in hook_files]}"
        )
