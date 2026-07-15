"""Structural validation tests for all shipped Kiro 1.0 hooks.

Verifies JSON structure, required v1 fields, 1.0 trigger names, matcher scoping
(and regex compilability), prompt/command presence, the ``v1`` wrapper version,
and hook file count.

Each shipped hook is a ``{"version": "v1", "hooks": [entry]}`` wrapper; the
entry carries ``name``, ``trigger``, an optional ``matcher`` (single regex), and
an ``action`` (``{"type": "agent", "prompt": ...}`` or
``{"type": "command", "command": ...}``). ``load_all_hooks`` returns the entries.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    get_hook_files,
    load_all_hooks,
    load_hook_wrapper,
    parse_categories_yaml,
)

# ---------------------------------------------------------------------------
# Kiro 1.0 trigger taxonomy
# ---------------------------------------------------------------------------

# All valid 1.0 triggers.
V1_TRIGGERS: set[str] = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "Stop",
    "UserPromptSubmit",
    "PostTaskExec",
    "PreToolUse",
    "PostToolUse",
}

# Triggers that scope to a subject (file path or tool name) and therefore
# require a ``matcher`` regex on the shipped hooks.
V1_SCOPED_TRIGGERS: set[str] = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "PreToolUse",
    "PostToolUse",
}

# Unscoped triggers omit the matcher.
V1_UNSCOPED_TRIGGERS: set[str] = {"Stop", "UserPromptSubmit", "PostTaskExec"}

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
    """Verify all hooks parse as valid JSON and contain required v1 fields."""

    @pytest.mark.parametrize("hook_path", _hook_files, ids=[p.name for p in _hook_files])
    def test_parses_as_valid_json(self, hook_path: Path):
        """Each hook file parses as a valid v1 wrapper object (Req 2.1)."""
        try:
            with open(hook_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f'"{hook_path.name}" is not valid JSON: {exc}')
        assert isinstance(data, dict), f"{hook_path.name} did not parse as a JSON object"
        assert data.get("version") == "v1", (
            f'{hook_path.name} must have top-level version "v1"'
        )
        assert isinstance(data.get("hooks"), list) and data["hooks"], (
            f"{hook_path.name} must contain a non-empty 'hooks' array"
        )

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_contains_all_required_fields(self, hook_id: str, data: dict):
        """Each v1 entry contains name, trigger, and a valid action (Req 2.2).

        agent actions require ``action.prompt``; command actions require
        ``action.command``.
        """
        missing: list[str] = []
        if not data.get("name"):
            missing.append("name")
        if not data.get("trigger"):
            missing.append("trigger")
        action = data.get("action")
        if not isinstance(action, dict):
            missing.append("action")
        else:
            action_type = action.get("type")
            if action_type == "agent" and not action.get("prompt"):
                missing.append("action.prompt")
            elif action_type == "command" and not action.get("command"):
                missing.append("action.command")
            elif action_type not in ("agent", "command"):
                missing.append("action.type")
        assert not missing, (
            f'"{hook_id}" missing required field(s): {", ".join(missing)}'
        )


# ===========================================================================
# TestHookTriggers — Req 2.3
# ===========================================================================

class TestHookTriggers:
    """Verify every hook's trigger is a valid 1.0 trigger and action type is 1.0."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_trigger_is_valid(self, hook_id: str, data: dict):
        """Each hook's trigger is in the 1.0 trigger set (Req 2.3)."""
        trigger = data.get("trigger", "")
        assert trigger in V1_TRIGGERS, (
            f'"{hook_id}" has invalid trigger: "{trigger}"'
        )

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_action_type_is_valid(self, hook_id: str, data: dict):
        """Each hook's action type is one of the 1.0 types agent/command."""
        action_type = data.get("action", {}).get("type", "")
        assert action_type in ("agent", "command"), (
            f'"{hook_id}" has invalid action type: "{action_type}"'
        )


# ===========================================================================
# TestHookActionContent — Req 2.4
# ===========================================================================

class TestHookActionContent:
    """Verify agent hooks have a >= 20 char prompt; command hooks have a command."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_prompt_at_least_20_chars(self, hook_id: str, data: dict):
        """agent prompts are >= 20 chars; command hooks carry a command instead (Req 2.4)."""
        action = data.get("action", {})
        if action.get("type") == "command":
            command = action.get("command", "")
            assert isinstance(command, str) and command.strip(), (
                f'"{hook_id}" is a command hook but has no action.command'
            )
            return
        prompt = action.get("prompt", "")
        assert isinstance(prompt, str) and len(prompt) >= 20, (
            f'"{hook_id}" prompt is {len(prompt)} chars, minimum is 20'
        )


# ===========================================================================
# TestHookMatcherScoping — Req 2.5, 2.6
# ===========================================================================

class TestHookMatcherScoping:
    """Verify scoped triggers carry a compilable matcher and unscoped ones omit it."""

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_scoped_triggers_have_compilable_matcher(self, hook_id: str, data: dict):
        """File/tool triggers carry a single matcher regex that compiles (Req 2.5, 2.6)."""
        trigger = data.get("trigger", "")
        if trigger not in V1_SCOPED_TRIGGERS:
            pytest.skip("Not a scoped (file/tool) trigger")
        matcher = data.get("matcher")
        assert isinstance(matcher, str) and matcher, (
            f'"{hook_id}" with scoped trigger "{trigger}" is missing a matcher'
        )
        try:
            re.compile(matcher)
        except re.error as exc:
            pytest.fail(f'"{hook_id}" matcher is not a valid regex: {exc}')

    @pytest.mark.parametrize("hook_id,data", _hook_data, ids=_hook_ids)
    def test_unscoped_triggers_omit_matcher(self, hook_id: str, data: dict):
        """Unscoped triggers (Stop/UserPromptSubmit/PostTaskExec) omit the matcher."""
        trigger = data.get("trigger", "")
        if trigger not in V1_UNSCOPED_TRIGGERS:
            pytest.skip("Not an unscoped trigger")
        assert not data.get("matcher"), (
            f'"{hook_id}" with unscoped trigger "{trigger}" should omit the matcher, '
            f'got {data.get("matcher")!r}'
        )


# ===========================================================================
# TestHookWrapperVersion — Req 2.7, 7.1, 7.3
# ===========================================================================

class TestHookWrapperVersion:
    """Verify each hook file's wrapper declares the v1 schema version."""

    @pytest.mark.parametrize("hook_path", _hook_files, ids=[p.name for p in _hook_files])
    def test_wrapper_version_is_v1(self, hook_path: Path):
        """Each hook file's top-level version equals "v1" (Req 2.7, 7.1)."""
        wrapper = load_hook_wrapper(hook_path)
        assert wrapper.get("version") == "v1", (
            f'"{hook_path.name}" has invalid wrapper version: '
            f'"{wrapper.get("version")}" (expected "v1")'
        )


# ===========================================================================
# TestHookCount — Req 2.8
# ===========================================================================

class TestHookCount:
    """Verify the expected number of .json hook files exist."""

    def test_hook_file_count_matches_categories(self):
        """Hook file count matches unique hook IDs in hook-categories.yaml (Req 2.8)."""
        categories = parse_categories_yaml()
        unique_hook_ids: set[str] = set()
        for ids in categories.values():
            unique_hook_ids.update(ids)
        expected_count = len(unique_hook_ids)
        hook_files = get_hook_files()
        assert len(hook_files) == expected_count, (
            f"Expected {expected_count} hook files (unique IDs in categories YAML), "
            f"found {len(hook_files)}: {[p.name for p in hook_files]}"
        )
