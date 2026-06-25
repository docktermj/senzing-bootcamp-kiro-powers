"""Example-based schema-validation tests for validate_governance_rules.py.

Feature: governance-rule-conformance

These are concrete, non-input-varying unit tests for ``validate_schema`` — the
schema gate that converts raw registry mappings (as produced by
``load_registry``) into typed ``RuleEntry``/``Assertion`` dataclasses while
collecting schema ``Violation``s. ``validate_schema`` takes RAW dict mappings
(NOT dataclasses) and returns ``(entries, violations)``.

Covered cases (Requirement 11.4):
    * Each required field missing individually: ``id``, ``rule``, ``category``,
      ``enforced_by``, ``assertions`` (Requirements 2.1, 2.8).
    * Duplicate ``id`` across entries (Requirements 2.2, 2.9).
    * An unsupported assertion ``type`` — halts with empty entries (Req 3.9).
    * An assertion missing a parameter required by its type (Req 3.10).
    * The behavioral-only exception: empty ``assertions`` is allowed when
      ``static_checkable`` is ``false`` but rejected when it is true/absent.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_governance_rules import (  # noqa: E402
    RuleEntry,
    validate_schema,
)

# Required Rule Entry fields, per Requirement 2.1.
_REQUIRED_FIELDS = ["id", "rule", "category", "enforced_by", "assertions"]


def _valid_entry() -> dict:
    """Return a fresh, schema-valid raw rule mapping.

    Each call returns an independent dict so negative cases can mutate a copy
    without affecting other tests. Values mirror the shape ``load_registry``
    produces (scalars decoded, ``enforced_by`` a list of strings, ``assertions``
    a list of mapping dicts). File paths are arbitrary strings because
    ``validate_schema`` performs schema checks only — it never touches disk.

    Returns:
        A raw rule mapping that ``validate_schema`` accepts with no violations.
    """
    return {
        "id": "pointer-prefix",
        "rule": "ALWAYS prefix input-requiring prompts with the pointer (👉).",
        "category": "conversation-protocol",
        "enforced_by": [
            "senzing-bootcamp/steering/agent-behavior-rules.md",
            "senzing-bootcamp/steering/agent-instructions.md",
        ],
        "assertions": [
            {
                "type": "substring_present",
                "file": "senzing-bootcamp/steering/agent-behavior-rules.md",
                "value": "Prefix every input-requiring prompt with 👉",
            },
        ],
    }


class TestValidEntryBaseline:
    """Anchor: the baseline valid entry must pass cleanly.

    Validates: Requirements 2.1
    """

    def test_valid_entry_has_no_violations(self) -> None:
        entries, violations = validate_schema([_valid_entry()])

        assert violations == []
        assert len(entries) == 1
        assert isinstance(entries[0], RuleEntry)
        assert entries[0].id == "pointer-prefix"


class TestMissingRequiredField:
    """Each required field missing individually is a schema violation.

    Validates: Requirements 2.1, 2.8
    """

    @pytest.mark.parametrize("field", _REQUIRED_FIELDS)
    def test_missing_required_field_is_violation(self, field: str) -> None:
        raw = _valid_entry()
        del raw[field]

        entries, violations = validate_schema([raw])

        # The malformed entry is dropped and a schema violation names the field.
        assert entries == []
        assert violations, f"expected a violation for missing '{field}'"
        assert all(v.kind == "schema" for v in violations)
        assert any(field in v.detail for v in violations), (
            f"no violation mentioned the missing field '{field}': "
            f"{[v.detail for v in violations]}"
        )

    @pytest.mark.parametrize("field", _REQUIRED_FIELDS)
    def test_empty_required_field_is_violation(self, field: str) -> None:
        # An empty string / empty list counts as missing (Req 2.8).
        raw = _valid_entry()
        raw[field] = [] if field in ("enforced_by", "assertions") else ""

        entries, violations = validate_schema([raw])

        assert entries == []
        assert any(field in v.detail for v in violations), (
            f"no violation mentioned the empty field '{field}': "
            f"{[v.detail for v in violations]}"
        )


class TestDuplicateId:
    """Two entries sharing an ``id`` is a duplicate-id violation.

    Validates: Requirements 2.2, 2.9
    """

    def test_duplicate_id_is_reported(self) -> None:
        first = _valid_entry()
        second = copy.deepcopy(_valid_entry())
        # Same id, but otherwise-valid second entry.
        second["category"] = "mcp-integrity"

        _entries, violations = validate_schema([first, second])

        duplicate = [v for v in violations if "duplicate" in v.detail.lower()]
        assert duplicate, (
            f"expected a duplicate-id violation: {[v.detail for v in violations]}"
        )
        assert duplicate[0].kind == "schema"
        assert duplicate[0].rule_id == "pointer-prefix"
        assert "pointer-prefix" in duplicate[0].detail

    def test_distinct_ids_have_no_duplicate_violation(self) -> None:
        first = _valid_entry()
        second = copy.deepcopy(_valid_entry())
        second["id"] = "mcp-first"

        _entries, violations = validate_schema([first, second])

        assert not [v for v in violations if "duplicate" in v.detail.lower()]


class TestUnsupportedAssertionType:
    """An unsupported assertion ``type`` halts with empty entries (Req 3.9).

    Validates: Requirements 3.9
    """

    def test_unsupported_type_returns_early_with_empty_entries(self) -> None:
        raw = _valid_entry()
        raw["assertions"] = [
            {
                "type": "substring_somewhere",  # not in the supported set
                "file": "senzing-bootcamp/steering/agent-instructions.md",
                "value": "👉",
            },
        ]

        entries, violations = validate_schema([raw])

        # Unsupported type takes precedence and halts before content eval:
        # no entries are built.
        assert entries == []
        assert violations, "expected an unsupported-type violation"
        assert all(v.kind == "schema" for v in violations)
        assert any(
            "unsupported assertion type" in v.detail for v in violations
        ), [v.detail for v in violations]
        assert any(
            "substring_somewhere" in v.detail for v in violations
        ), [v.detail for v in violations]

    def test_unsupported_type_precedes_other_schema_errors(self) -> None:
        # Even with another entry missing required fields, the unsupported
        # type halts validation first and returns only the type violation(s).
        good_but_unsupported = _valid_entry()
        good_but_unsupported["assertions"] = [{"type": "totally_unknown"}]
        broken = {"id": "broken"}  # missing rule/category/enforced_by/assertions

        entries, violations = validate_schema([good_but_unsupported, broken])

        assert entries == []
        assert violations
        assert all(
            "unsupported assertion type" in v.detail for v in violations
        ), [v.detail for v in violations]


class TestMalformedAssertion:
    """A supported assertion missing a required parameter is malformed.

    Validates: Requirements 3.10
    """

    def test_missing_required_parameter_is_violation(self) -> None:
        raw = _valid_entry()
        # substring_present requires both 'file' and 'value'; drop 'value'.
        raw["assertions"] = [
            {
                "type": "substring_present",
                "file": "senzing-bootcamp/steering/agent-instructions.md",
            },
        ]

        entries, violations = validate_schema([raw])

        assert entries == []
        malformed = [v for v in violations if "malformed assertion" in v.detail]
        assert malformed, [v.detail for v in violations]
        assert malformed[0].kind == "schema"
        assert "value" in malformed[0].detail
        assert malformed[0].assertion is not None
        assert malformed[0].assertion.type == "substring_present"

    def test_hook_field_equals_missing_key_path_is_violation(self) -> None:
        raw = _valid_entry()
        # hook_field_equals requires 'file', 'key_path', and 'value'.
        raw["assertions"] = [
            {
                "type": "hook_field_equals",
                "file": "senzing-bootcamp/hooks/ask-bootcamper.kiro.hook",
                "value": "askBootcamper",
            },
        ]

        entries, violations = validate_schema([raw])

        assert entries == []
        malformed = [v for v in violations if "malformed assertion" in v.detail]
        assert malformed, [v.detail for v in violations]
        assert "key_path" in malformed[0].detail


class TestBehavioralOnlyAssertionsException:
    """Empty ``assertions`` is allowed only for behavioral-only rules.

    Validates: Requirements 2.1, 2.8
    """

    def test_empty_assertions_ok_when_static_checkable_false(self) -> None:
        raw = _valid_entry()
        raw["id"] = "no-ambiguous-yes-no"
        raw["static_checkable"] = False
        raw["assertions"] = []

        entries, violations = validate_schema([raw])

        assert violations == [], [v.detail for v in violations]
        assert len(entries) == 1
        assert entries[0].static_checkable is False
        assert entries[0].assertions == []

    def test_empty_assertions_violation_when_static_checkable_true(self) -> None:
        raw = _valid_entry()
        raw["static_checkable"] = True
        raw["assertions"] = []

        entries, violations = validate_schema([raw])

        assert entries == []
        assert any("assertions" in v.detail for v in violations), (
            f"expected an assertions violation: {[v.detail for v in violations]}"
        )

    def test_empty_assertions_violation_when_static_checkable_absent(self) -> None:
        raw = _valid_entry()
        raw["assertions"] = []
        # static_checkable omitted entirely => defaults to True.
        assert "static_checkable" not in raw

        entries, violations = validate_schema([raw])

        assert entries == []
        assert any("assertions" in v.detail for v in violations), (
            f"expected an assertions violation: {[v.detail for v in violations]}"
        )
