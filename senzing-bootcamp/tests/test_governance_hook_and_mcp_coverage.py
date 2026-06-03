"""Presence + conformance tests for the new governance Rule Entries.

Feature: governance-hook-and-mcp-coverage

This additive feature appends five new Rule Entries to the shipped registry
``senzing-bootcamp/config/governance-rules.yaml`` to close two coverage gaps:
the agentStop hook contract (Gap 1) and MCP config drift between ``mcp.json``
and ``POWER.md`` (Gap 2). These tests verify the entries are present in the
shipped registry and that the validator stays conformant over the real
repository with them present.

The change is purely additive registry data over an unchanged validator, so the
test shape is presence + conformance, not generated-input property tests. The
existing validator behavioral property tests are not duplicated here; the
conformance check reuses the validator's ``run`` entry point.

Covered cases:
    * The five new rule ids are present in the shipped registry, and every
      registry id is unique (Requirements 11.1, 8.4).
    * ``run(shipped_registry, repo_root)`` over the real repository runs to
      completion, exits 0, and reports no violation whose ``rule_id`` is one of
      the five new ids (Requirements 11.2, 11.3, 11.5).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_governance_rules import (  # noqa: E402
    RunResult,
    load_registry,
    run,
)

# The repository root: <repo_root>/senzing-bootcamp/tests/<this file>.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SHIPPED_REGISTRY = _REPO_ROOT / "senzing-bootcamp" / "config" / "governance-rules.yaml"

# The five new Rule Entry ids added by this feature.
_NEW_RULE_IDS = (
    "agentstop-hook-set",
    "agentstop-trigger-type",
    "agentstop-contract-doc",
    "mcp-server-name",
    "mcp-disabled-tool",
)


def _format_violations(result: RunResult) -> str:
    """Render a run's violations as a diagnosable, multi-line message.

    Args:
        result: The :class:`RunResult` whose violations should be described.

    Returns:
        A human-readable block listing each violation's rule id, kind, detail,
        and (when present) the assertion type and file path, so a future drift
        is easy to locate and fix.
    """
    lines: list[str] = []
    for violation in result.violations:
        atype = violation.assertion.type if violation.assertion else "-"
        lines.append(
            f"  - rule={violation.rule_id!r} kind={violation.kind} "
            f"assertion={atype} file={violation.file!r}: {violation.detail}"
        )
    return "\n".join(lines)


class TestNewRuleEntriesPresent:
    """The five new Rule Entries ship in the registry with unique ids.

    Validates: Requirements 11.1, 8.4
    """

    def test_new_rule_ids_present(self) -> None:
        """``load_registry`` of the shipped file exposes every new rule id."""
        raw_entries = load_registry(_SHIPPED_REGISTRY)
        ids = {raw.get("id") for raw in raw_entries}

        for new_id in _NEW_RULE_IDS:
            assert new_id in ids, f"shipped registry is missing new rule id {new_id!r}"

    def test_all_registry_ids_unique(self) -> None:
        """No two Rule Entries share an id (the new ids do not collide).

        Confirms the five new entries were appended with ids unique across the
        whole registry (Requirement 8.4), not duplicating any seed id.
        """
        raw_entries = load_registry(_SHIPPED_REGISTRY)
        all_ids: list[str] = [raw.get("id") for raw in raw_entries]

        assert len(all_ids) == len(set(all_ids)), (
            "the shipped registry has duplicate rule ids: "
            f"{sorted(i for i in all_ids if all_ids.count(i) > 1)}"
        )


class TestNewRuleEntriesConformant:
    """The validator stays conformant over the real repo with the new entries.

    Validates: Requirements 11.2, 11.3, 11.5
    """

    def test_shipped_registry_conformant_with_new_entries(self) -> None:
        """``run`` over the real repo exits 0 and flags no new-entry violation.

        Reusing ``run`` (the same entry point the existing conformance test
        uses) verifies the five new entries hold against the real repository
        without re-testing the validator's parsing/evaluation internals.
        """
        result = run(_SHIPPED_REGISTRY, _REPO_ROOT)

        assert result.completed is True, (
            "the validator did not run to completion over the shipped registry; "
            "this indicates a load or schema halt:\n" + _format_violations(result)
        )
        assert result.exit_code == 0, (
            "expected exit code 0 for the conformant shipped registry, got "
            f"{result.exit_code}:\n" + _format_violations(result)
        )

        new_id_violations = [
            v for v in result.violations if v.rule_id in _NEW_RULE_IDS
        ]
        assert new_id_violations == [], (
            "the new governance Rule Entries have conformance violations:\n"
            + _format_violations(
                RunResult(
                    rules_checked=result.rules_checked,
                    violations=new_id_violations,
                    completed=result.completed,
                    exit_code=result.exit_code,
                )
            )
        )
