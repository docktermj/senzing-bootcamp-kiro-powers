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

from hook_test_helpers import validate_required_fields  # noqa: E402
from write_gate_momentum_baseline import load_hook  # noqa: E402


class TestWriteGateHookSchemaConformance:
    """Schema conformance checks for the live write-policy-gate hook.

    Validates: Requirements 6.1, 6.2, 6.3
    """

    def test_hook_parses_as_json(self) -> None:
        """The hook file is well-formed JSON parsing to a dict (Requirement 6.3)."""
        hook = load_hook()
        assert isinstance(hook, dict), "Hook must parse to a JSON object"

    def test_when_type_is_pretooluse(self) -> None:
        """``when.type`` is exactly ``preToolUse`` (Requirement 6.1)."""
        hook = load_hook()
        assert hook["when"]["type"] == "preToolUse"

    def test_tool_types_is_write_only(self) -> None:
        """``when.toolTypes`` is exactly ``["write"]`` (Requirement 6.1)."""
        hook = load_hook()
        assert hook["when"]["toolTypes"] == ["write"]

    def test_required_fields_present(self) -> None:
        """Required hook fields are present (Requirement 6.2).

        Confirms ``name``, ``version``, ``when``, and ``then`` exist, alongside
        the dot-notation required fields tracked by the shared helper.
        """
        hook = load_hook()
        for field in ("name", "version", "when", "then"):
            assert field in hook, f"missing required field: {field}"

        missing = validate_required_fields(hook)
        assert missing == [], f"missing required dot-notation fields: {missing}"

    def test_required_fields_non_empty(self) -> None:
        """Required hook fields hold non-empty values (Requirement 6.2)."""
        hook = load_hook()

        assert isinstance(hook["name"], str) and hook["name"].strip()
        assert isinstance(hook["version"], str) and hook["version"].strip()
        assert isinstance(hook["when"], dict) and hook["when"]
        assert isinstance(hook["then"], dict) and hook["then"]

    def test_then_is_ask_agent_with_non_empty_prompt(self) -> None:
        """``then.type`` is ``askAgent`` with a non-empty ``then.prompt`` (Requirement 6.2)."""
        hook = load_hook()
        then = hook["then"]
        assert then["type"] == "askAgent"
        assert isinstance(then["prompt"], str) and then["prompt"].strip()
