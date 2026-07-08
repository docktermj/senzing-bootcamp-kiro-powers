"""Integration test: the stale-legacy-reference gate passes the shipped tree.

Feature: kiro-1-0-migration

Asserts that the CI stale-legacy-reference gate
(``senzing-bootcamp/scripts/validate_no_legacy_hooks.py``) runs cleanly against
the *real shipped* Power tree — exit 0, no findings — confirming the migration
left no residual ``*.kiro.hook`` file, no ``when``/``then``-shaped hook JSON, and
no legacy trigger/action reference in a shipped hook, config, steering file, or
doc (Requirement 14.5).

This is a repo-level test over the actual shipped files (hence its home in the
repo-root ``tests/``), complementing the synthetic-fixture unit tests in
``senzing-bootcamp/tests/test_validate_no_legacy_hooks.py``.

**Validates: Requirements 14.5**
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_REPO_ROOT / "senzing-bootcamp" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_no_legacy_hooks as gate  # noqa: E402


class TestGatePassesShippedTree:
    """The gate finds no stale legacy reference in the shipped Power tree."""

    def test_scan_power_reports_no_findings(self) -> None:
        """No stale legacy hook-schema reference exists in the shipped surface."""
        findings = gate.scan_power(_REPO_ROOT)
        rendered = "\n".join(f"{f.path}:{f.line}: {f.detail}" for f in findings)
        assert not findings, f"stale legacy references found:\n{rendered}"

    def test_main_exits_zero(self) -> None:
        """Running the gate against the shipped tree exits 0 (CI-green)."""
        assert gate.main(["--repo-root", str(_REPO_ROOT)]) == 0

    def test_no_kiro_hook_files_ship(self) -> None:
        """No ``*.kiro.hook`` file ships outside the migration tooling trees."""
        power = _REPO_ROOT / "senzing-bootcamp"
        assert gate.find_legacy_hook_files(power, _REPO_ROOT) == []
