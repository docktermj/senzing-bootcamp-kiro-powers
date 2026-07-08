"""Hook schema conformance example tests for write-gate-momentum-preservation.

Deterministic (non-property-based) example tests that lock in the structural
integrity of the live ``write-policy-gate`` hook after the Outcome B edit. They
assert the hook remains a valid ``preToolUse`` write hook with the required
fields populated, so the bootcamp continues to load and enforce write policy.

Validates: Requirements 6.1, 6.2, 6.3

Reuses (without modifying their public contracts):
- ``tests/write_gate_momentum_baseline.py`` (``load_hook()``) to read the live
  hook JSON document.
- ``tests/hook_test_helpers.py`` (``validate_required_fields()``) to confirm the
  required dot-notation fields are present.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from write_gate_momentum_baseline import load_hook  # noqa: E402


class TestWriteGateHookSchemaConformance:
    """Schema conformance checks for the live write-policy-gate v1 hook.

    Validates: Requirements 6.1, 6.2, 6.3
    """

    def test_hook_parses_as_json(self) -> None:
        """The hook file is well-formed JSON parsing to a v1 wrapper (Requirement 6.3)."""
        wrapper = load_hook()
        assert isinstance(wrapper, dict), "Hook must parse to a JSON object"
        assert wrapper.get("version") == "v1", "wrapper must declare version v1"
        assert isinstance(wrapper.get("hooks"), list) and wrapper["hooks"], (
            "wrapper must contain a non-empty 'hooks' array"
        )

    def test_when_type_is_pretooluse(self) -> None:
        """``trigger`` is exactly ``PreToolUse`` (Requirement 6.1)."""
        entry = load_hook()["hooks"][0]
        assert entry["trigger"] == "PreToolUse"

    def test_tool_types_is_write_only(self) -> None:
        """``matcher`` is the write-tool regex (Requirement 6.1)."""
        entry = load_hook()["hooks"][0]
        assert entry.get("matcher") == "fs_write|str_replace|fs_append"

    def test_required_fields_present(self) -> None:
        """Required v1 entry fields are present (Requirement 6.2).

        Confirms ``name``, ``trigger``, and ``action`` exist on the entry.
        """
        entry = load_hook()["hooks"][0]
        for field in ("name", "trigger", "action"):
            assert field in entry, f"missing required field: {field}"

    def test_required_fields_non_empty(self) -> None:
        """Required v1 entry fields hold non-empty values (Requirement 6.2)."""
        entry = load_hook()["hooks"][0]

        assert isinstance(entry["name"], str) and entry["name"].strip()
        assert isinstance(entry["trigger"], str) and entry["trigger"].strip()
        assert isinstance(entry["action"], dict) and entry["action"]

    def test_then_is_ask_agent_with_non_empty_prompt(self) -> None:
        """``action.type`` is ``agent`` with a non-empty ``action.prompt`` (Requirement 6.2)."""
        action = load_hook()["hooks"][0]["action"]
        assert action["type"] == "agent"
        assert isinstance(action["prompt"], str) and action["prompt"].strip()
