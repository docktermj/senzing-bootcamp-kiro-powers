"""Unit tests for the write-gate preservation guard in validate_governance_rules.

Feature: kiro-1-0-migration

These are concrete, example-based unit tests for ``check_write_gates`` — the
guard that keeps the three ``PreToolUse`` write gates (``write-policy-gate``,
``enforce-mandatory-gate``, ``gate-module3-visualization``) present, enabled,
and scoped to the ``fs_write|str_replace|fs_append`` matcher under Kiro 1.0.

Each test builds a synthetic repo root under ``tmp_path`` with fabricated
``senzing-bootcamp/hooks/<id>.json`` files, so the guard is exercised against
controlled fixtures rather than the real shipped hook files.

Covered cases:
    * All three gates present and correct -> guard PASSES (exit_code 0),
      Requirements 5.1, 5.2.
    * A gate file missing -> guard FAILS (exit_code 1) and the violation names
      the missing gate (Requirement 5.4).
    * A gate disabled (``"enabled": false`` at the wrapper or ``"disabled":
      true`` on the entry) -> guard FAILS (Requirement 5.4).
    * A gate drifted (wrong trigger or wrong matcher) -> guard FAILS
      (Requirement 5.4).
    * APPROVAL SIGNAL: a gate removed AND ``expected_gates`` updated to exclude
      that id -> guard PASSES (Requirement 5.5).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_governance_rules import (  # noqa: E402
    EXPECTED_WRITE_GATES,
    WRITE_GATE_MATCHER,
    WRITE_GATE_TRIGGER,
    check_write_gates,
)

# Repo-root-relative directory the guard scans for shipped v1 hook files.
_HOOKS_DIR_REL = "senzing-bootcamp/hooks"

# The three write gates the guard preserves by default.
_GATE_IDS = tuple(sorted(EXPECTED_WRITE_GATES))


def _valid_gate_wrapper(gate_id: str) -> dict:
    """Return a schema-valid v1 wrapper for one PreToolUse write gate.

    Args:
        gate_id: The write-gate id used as the hook ``name``.

    Returns:
        A ``{"version": "v1", "hooks": [ ... ]}`` wrapper whose single entry is
        an enabled ``PreToolUse`` hook carrying the fixed write matcher.
    """
    return {
        "version": "v1",
        "hooks": [
            {
                "name": gate_id,
                "trigger": WRITE_GATE_TRIGGER,
                "matcher": WRITE_GATE_MATCHER,
                "action": {"type": "agent", "prompt": f"{gate_id} policy prompt"},
            }
        ],
    }


def _write_gate(hooks_dir: Path, gate_id: str, wrapper: dict) -> None:
    """Write ``wrapper`` as ``<gate_id>.json`` under ``hooks_dir``.

    Args:
        hooks_dir: The ``senzing-bootcamp/hooks`` directory to write into.
        gate_id: The write-gate id (becomes the file stem).
        wrapper: The v1 wrapper object to serialize.
    """
    (hooks_dir / f"{gate_id}.json").write_text(
        json.dumps(wrapper, indent=2), encoding="utf-8"
    )


def _make_repo(tmp_path: Path, wrappers: dict[str, dict]) -> Path:
    """Build a fake repo root with one hook file per entry in ``wrappers``.

    Creates ``<tmp_path>/senzing-bootcamp/hooks/`` and writes each
    ``<id>.json`` from ``wrappers``. An id omitted from ``wrappers`` simply has
    no file, modeling a missing gate.

    Args:
        tmp_path: The pytest temp directory used as the repo root.
        wrappers: Mapping of gate id -> v1 wrapper object to write.

    Returns:
        The repo root path to pass to ``check_write_gates``.
    """
    hooks_dir = tmp_path / _HOOKS_DIR_REL
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for gate_id, wrapper in wrappers.items():
        _write_gate(hooks_dir, gate_id, wrapper)
    return tmp_path


def _all_valid_wrappers() -> dict[str, dict]:
    """Return valid wrappers for all three default write gates."""
    return {gate_id: _valid_gate_wrapper(gate_id) for gate_id in _GATE_IDS}


class TestAllGatesPresent:
    """All three write gates present and correct -> guard passes.

    Validates: Requirements 5.1, 5.2
    """

    def test_all_gates_valid_passes(self, tmp_path: Path) -> None:
        """Three valid PreToolUse write gates yield a clean pass (exit_code 0)."""
        repo_root = _make_repo(tmp_path, _all_valid_wrappers())

        result = check_write_gates(repo_root)

        assert result.exit_code == 0
        assert result.violations == []
        assert result.hooks_dir_present is True
        assert result.expected_gates == _GATE_IDS


class TestMissingGate:
    """A missing gate file fails the guard and names the gate.

    Validates: Requirement 5.4
    """

    def test_missing_gate_fails_and_names_it(self, tmp_path: Path) -> None:
        """Dropping one gate file fails the guard (exit_code 1)."""
        wrappers = _all_valid_wrappers()
        missing_id = "enforce-mandatory-gate"
        del wrappers[missing_id]
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        assert len(result.violations) == 1
        violation = result.violations[0]
        # The violation names the specific missing gate.
        assert missing_id in violation.detail
        assert "missing" in violation.detail
        assert violation.file == f"{_HOOKS_DIR_REL}/{missing_id}.json"

    def test_missing_gate_detail_carries_approval_signal(
        self, tmp_path: Path
    ) -> None:
        """A blocked change explains the maintainer-approval remediation (5.4).

        The violation must point the maintainer at removing the id from
        ``EXPECTED_WRITE_GATES`` as the sanctioned way to proceed.
        """
        wrappers = _all_valid_wrappers()
        del wrappers["write-policy-gate"]
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        assert "EXPECTED_WRITE_GATES" in result.violations[0].detail


class TestDisabledGate:
    """A disabled gate fails the guard, whether opted out at wrapper or entry.

    Validates: Requirement 5.4
    """

    def test_gate_disabled_at_wrapper_fails(self, tmp_path: Path) -> None:
        """``"enabled": false`` on the wrapper disables the gate and fails."""
        wrappers = _all_valid_wrappers()
        disabled_id = "gate-module3-visualization"
        wrappers[disabled_id]["enabled"] = False
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        details = " ".join(v.detail for v in result.violations)
        assert disabled_id in details
        assert "disabled" in details

    def test_gate_disabled_at_entry_fails(self, tmp_path: Path) -> None:
        """``"disabled": true`` on the hook entry disables the gate and fails."""
        wrappers = _all_valid_wrappers()
        disabled_id = "write-policy-gate"
        wrappers[disabled_id]["hooks"][0]["disabled"] = True
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        details = " ".join(v.detail for v in result.violations)
        assert disabled_id in details
        assert "disabled" in details


class TestDriftedGate:
    """A gate that drifts from the fixed trigger/matcher fails the guard.

    Validates: Requirement 5.4
    """

    def test_wrong_trigger_fails(self, tmp_path: Path) -> None:
        """A non-``PreToolUse`` trigger no longer intercepts writes and fails."""
        wrappers = _all_valid_wrappers()
        drifted_id = "enforce-mandatory-gate"
        wrappers[drifted_id]["hooks"][0]["trigger"] = "PostToolUse"
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        details = " ".join(v.detail for v in result.violations)
        assert drifted_id in details
        assert "trigger" in details

    def test_wrong_matcher_fails(self, tmp_path: Path) -> None:
        """A drifted matcher no longer scopes to writes and fails."""
        wrappers = _all_valid_wrappers()
        drifted_id = "gate-module3-visualization"
        wrappers[drifted_id]["hooks"][0]["matcher"] = "fs_write"
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        details = " ".join(v.detail for v in result.violations)
        assert drifted_id in details
        assert "matcher" in details


class TestApprovalSignal:
    """Removing a gate AND its expected-set id together is sanctioned.

    Validates: Requirement 5.5
    """

    def test_removed_gate_with_updated_expected_set_passes(
        self, tmp_path: Path
    ) -> None:
        """The approval signal (Req 5.5): removing a gate id from the expected
        set in the same change lets the removal proceed cleanly.

        With ``gate-module3-visualization`` both absent from disk and dropped
        from ``expected_gates``, the guard passes (exit_code 0) and only checks
        the two remaining gates.
        """
        removed_id = "gate-module3-visualization"
        wrappers = _all_valid_wrappers()
        del wrappers[removed_id]
        repo_root = _make_repo(tmp_path, wrappers)

        approved_gates = frozenset(EXPECTED_WRITE_GATES - {removed_id})
        result = check_write_gates(repo_root, expected_gates=approved_gates)

        assert result.exit_code == 0
        assert result.violations == []
        assert removed_id not in result.expected_gates
        assert result.expected_gates == tuple(sorted(approved_gates))

    def test_removed_gate_without_updated_expected_set_still_fails(
        self, tmp_path: Path
    ) -> None:
        """Removing a gate WITHOUT updating the expected set is blocked (5.4).

        This is the contrast to the approval signal: the same missing file
        fails when the default expected set still lists the gate.
        """
        removed_id = "gate-module3-visualization"
        wrappers = _all_valid_wrappers()
        del wrappers[removed_id]
        repo_root = _make_repo(tmp_path, wrappers)

        result = check_write_gates(repo_root)

        assert result.exit_code == 1
        assert any(removed_id in v.detail for v in result.violations)
