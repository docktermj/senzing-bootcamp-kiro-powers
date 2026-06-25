"""Conformance test: the shipped registry passes its own validator.

Feature: governance-rule-conformance

The conformance layer must itself be conformant — the registry that enumerates
the governing rules and points at their enforcement must pass when evaluated
against the real repository. This test runs the validator over the actual
checkout with the shipped ``senzing-bootcamp/config/governance-rules.yaml`` and
asserts a clean (exit-0, zero-violation) result, so that any future drift
between a stated rule and where it is enforced fails CI here.

Covered cases:
    * ``run(shipped_registry, repo_root)`` over the real repository exits 0,
      runs to completion, and finds no violations (Requirements 7.9, 11.8). On
      failure the assertion message lists each violation so the drift is
      diagnosable.
    * ``main([])`` exits 0 with the default path resolution (shipped registry +
      inferred repo root) end-to-end over the real repository (Requirement 11.8).
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
    main,
    run,
)

# The repository root: <repo_root>/senzing-bootcamp/tests/<this file>.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SHIPPED_REGISTRY = _REPO_ROOT / "senzing-bootcamp" / "config" / "governance-rules.yaml"


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


class TestShippedRegistryConformance:
    """The shipped governance-rules.yaml passes the validator over the real repo.

    Validates: Requirements 7.9, 11.8
    """

    def test_shipped_registry_is_conformant(self) -> None:
        """``run`` over the real repo exits 0 with no violations.

        Calling ``run`` directly (rather than only ``main([])``) lets the
        assertion message enumerate any violations, so a future drift between a
        governing rule and its enforcement point is immediately diagnosable.
        """
        result = run(_SHIPPED_REGISTRY, _REPO_ROOT)

        assert result.completed is True, (
            "the validator did not run to completion over the shipped registry; "
            "this indicates a load or schema halt:\n" + _format_violations(result)
        )
        assert result.violations == [], (
            "the shipped governance-rules.yaml has conformance violations "
            "(rule enforcement has drifted):\n" + _format_violations(result)
        )
        assert result.exit_code == 0, (
            "expected exit code 0 for the conformant shipped registry, got "
            f"{result.exit_code}:\n" + _format_violations(result)
        )

    def test_main_no_args_passes_over_real_repo(self) -> None:
        """``main([])`` resolves the default paths and exits 0 end-to-end.

        This second check confirms the default-path resolution (the shipped
        registry plus the repo root inferred from the script location) works
        over the real repository, not just an explicit ``run`` call.
        """
        assert main([]) == 0
