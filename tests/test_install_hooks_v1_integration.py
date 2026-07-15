"""Integration test for the v1 hook installer (``scripts/install_hooks.py``).

Feature: kiro-1-0-migration (Task 10.3).

This test drives the installer end-to-end against the REAL shipped hook set,
installing into a temporary ``.kiro/hooks`` directory and asserting the Kiro 1.0
``.json`` installer contract:

- ``--all`` copies every shipped v1 ``.json`` hook (the set of 26, after the
  stop-hook-ux bugfix folded ``module-recap-append`` into ``ask-bootcamper``), and
  every copied file is a valid ``{"version": "v1", "hooks": [ ... ]}`` wrapper
  (Req 9.1, 9.2, 9.3).
- The install sets are derived from the shipped ``*.json`` files and the
  migrated ``hook-categories.yaml`` rather than a hardcoded legacy filename list
  (Req 9.3), and ``--essential`` installs exactly ``critical ∪ capture-critical``.
- The three manual hook ids and ``commonmark-validation`` never appear in any
  install set (Req 9.5); residual legacy ``*.kiro.hook`` files are never copied.
- The count the installer reports equals the number of files it actually
  installs (Req 9.6).

Per ``structure.md``, tests that read/validate the real shipped hook files live
in the repo-root ``tests/`` directory.

**Validates: Requirements 9.1, 9.2, 9.3, 9.5, 9.6**
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import install_hooks from senzing-bootcamp/scripts via the sys.path pattern.
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import install_hooks  # noqa: E402

# ---------------------------------------------------------------------------
# Constants — the REAL shipped hooks dir resolved relative to this test file.
# ---------------------------------------------------------------------------

REAL_HOOKS_DIR: Path = (
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "hooks"
)

# The migration shipped 27 non-manual v1 hooks; the stop-hook-ux bugfix folded
# ``module-recap-append`` into ``ask-bootcamper`` (Phase 0), leaving 26 (Req 1.1).
EXPECTED_MIGRATED_COUNT = 26

# The three former manual hooks, now slash commands — never installed (Req 9.4).
MANUAL_HOOK_IDS = {
    "backup-project-on-request",
    "git-commit-reminder",
    "commonmark-validation",
}

_INSTALLED_LINE = re.compile(r"Installed:\s+(\d+)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _shipped_json_filenames() -> set[str]:
    """Return the set of real shipped ``*.json`` v1 hook filenames."""
    return {p.name for p in REAL_HOOKS_DIR.glob("*.json")}


def _shipped_json_ids() -> set[str]:
    """Return the set of real shipped hook ids (filename without ``.json``)."""
    return {install_hooks._hook_id(name) for name in _shipped_json_filenames()}


def _installed_ids(user_dir: Path) -> set[str]:
    """Return the hook ids actually installed into *user_dir*."""
    return {install_hooks._hook_id(p.name) for p in user_dir.glob("*.json")}


def _reported_installed_count(output: str) -> int:
    """Parse the ``Installed: N ...`` count the installer prints on completion."""
    match = _INSTALLED_LINE.search(output)
    assert match is not None, f"no 'Installed: N' summary line in output:\n{output}"
    return int(match.group(1))


def _assert_valid_v1_wrapper(path: Path) -> None:
    """Assert *path* holds a schema-valid v1 hook wrapper."""
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("version") == "v1", f"{path.name}: version is not 'v1'"
    hooks = data.get("hooks")
    assert isinstance(hooks, list) and hooks, f"{path.name}: missing 'hooks' array"
    first = hooks[0]
    assert isinstance(first, dict), f"{path.name}: hooks[0] is not an object"
    name = first.get("name")
    assert isinstance(name, str) and name.strip(), f"{path.name}: missing 'name'"
    trigger = first.get("trigger")
    assert isinstance(trigger, str) and trigger.strip(), f"{path.name}: no 'trigger'"
    action = first.get("action")
    assert isinstance(action, dict), f"{path.name}: missing 'action' object"
    assert action.get("type") in {"agent", "command"}, (
        f"{path.name}: action.type must be 'agent' or 'command'"
    )


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestInstallerV1Integration:
    """End-to-end installer behaviour against the real shipped v1 hook set.

    **Validates: Requirements 9.1, 9.2, 9.3, 9.5, 9.6**
    """

    def test_all_installs_every_shipped_v1_hook_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``--all`` copies exactly the 26 shipped v1 ``.json`` files."""
        user_dir = tmp_path / ".kiro" / "hooks"

        code = install_hooks.main(
            ["--all", "--power-dir", str(REAL_HOOKS_DIR), "--user-dir", str(user_dir)]
        )

        assert code == 0
        installed = {p.name for p in user_dir.glob("*.json")}
        # Discovery-driven: the installed set equals the shipped ``*.json`` set,
        # not a hardcoded list (Req 9.1, 9.3).
        assert installed == _shipped_json_filenames()
        # The migrated set is exactly the 27 non-manual hooks (Req 1.1).
        assert len(installed) == EXPECTED_MIGRATED_COUNT

    def test_all_copies_are_valid_v1_wrappers(self, tmp_path: Path) -> None:
        """Every file copied by ``--all`` is a valid v1 hook wrapper (Req 9.2)."""
        user_dir = tmp_path / ".kiro" / "hooks"

        install_hooks.main(
            ["--all", "--power-dir", str(REAL_HOOKS_DIR), "--user-dir", str(user_dir)]
        )

        json_files = sorted(user_dir.glob("*.json"))
        assert len(json_files) == EXPECTED_MIGRATED_COUNT
        for hook_file in json_files:
            _assert_valid_v1_wrapper(hook_file)
        # No residual legacy ``*.kiro.hook`` file is ever copied.
        assert not list(user_dir.glob("*.kiro.hook"))

    def test_all_excludes_manual_ids_and_commonmark(self, tmp_path: Path) -> None:
        """No manual hook id (nor ``commonmark-validation``) is installed (Req 9.5)."""
        user_dir = tmp_path / ".kiro" / "hooks"

        install_hooks.main(
            ["--all", "--power-dir", str(REAL_HOOKS_DIR), "--user-dir", str(user_dir)]
        )

        installed_ids = _installed_ids(user_dir)
        assert MANUAL_HOOK_IDS.isdisjoint(installed_ids), (
            f"manual hook id leaked into --all install set: "
            f"{MANUAL_HOOK_IDS & installed_ids}"
        )
        for manual_id in MANUAL_HOOK_IDS:
            assert not (user_dir / f"{manual_id}.json").exists()

    def test_all_reported_count_equals_installed_count(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The reported install count matches the files on disk (Req 9.6)."""
        user_dir = tmp_path / ".kiro" / "hooks"

        install_hooks.main(
            ["--all", "--power-dir", str(REAL_HOOKS_DIR), "--user-dir", str(user_dir)]
        )

        out = capsys.readouterr().out
        actual = len(list(user_dir.glob("*.json")))
        assert _reported_installed_count(out) == actual == EXPECTED_MIGRATED_COUNT

    def test_essential_installs_only_the_derived_essential_set(
        self, tmp_path: Path
    ) -> None:
        """``--essential`` installs exactly ``(critical ∪ capture-critical)``.

        The essential set is derived from the migrated ``hook-categories.yaml``
        (critical block) unioned with the capture-critical hooks, intersected
        with the shipped files — never a hardcoded legacy list (Req 9.3).
        """
        user_dir = tmp_path / ".kiro" / "hooks"

        code = install_hooks.main(
            [
                "--essential",
                "--power-dir",
                str(REAL_HOOKS_DIR),
                "--user-dir",
                str(user_dir),
            ]
        )

        assert code == 0
        installed_ids = _installed_ids(user_dir)
        shipped_ids = _shipped_json_ids()

        # Derived from the categories file + capture-critical hooks.
        expected = (
            install_hooks.load_critical_hooks() | install_hooks.CAPTURE_CRITICAL
        ) & shipped_ids
        assert installed_ids == expected
        # And consistent with the module-level ESSENTIAL set the installer uses.
        assert installed_ids == install_hooks.ESSENTIAL & shipped_ids

    def test_essential_excludes_manual_ids_and_commonmark(self, tmp_path: Path) -> None:
        """The essential set carries no manual id and no ``commonmark-validation``."""
        user_dir = tmp_path / ".kiro" / "hooks"

        install_hooks.main(
            [
                "--essential",
                "--power-dir",
                str(REAL_HOOKS_DIR),
                "--user-dir",
                str(user_dir),
            ]
        )

        installed_ids = _installed_ids(user_dir)
        assert MANUAL_HOOK_IDS.isdisjoint(installed_ids)
        assert "commonmark-validation" not in installed_ids

    def test_essential_reported_count_equals_installed_count(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The reported essential-install count matches the files on disk (Req 9.6)."""
        user_dir = tmp_path / ".kiro" / "hooks"

        install_hooks.main(
            [
                "--essential",
                "--power-dir",
                str(REAL_HOOKS_DIR),
                "--user-dir",
                str(user_dir),
            ]
        )

        out = capsys.readouterr().out
        actual = len(list(user_dir.glob("*.json")))
        assert _reported_installed_count(out) == actual

    def test_critical_set_excludes_commonmark_validation(self) -> None:
        """The migrated critical set never contains ``commonmark-validation`` (Req 9.5)."""
        critical = install_hooks.load_critical_hooks()
        assert "commonmark-validation" not in critical
        assert "commonmark-validation" not in install_hooks.ESSENTIAL

    def test_essential_is_strict_subset_of_all(self, tmp_path: Path) -> None:
        """The essential install set is a strict subset of the full install set."""
        all_dir = tmp_path / "all" / ".kiro" / "hooks"
        ess_dir = tmp_path / "essential" / ".kiro" / "hooks"

        install_hooks.main(
            ["--all", "--power-dir", str(REAL_HOOKS_DIR), "--user-dir", str(all_dir)]
        )
        install_hooks.main(
            [
                "--essential",
                "--power-dir",
                str(REAL_HOOKS_DIR),
                "--user-dir",
                str(ess_dir),
            ]
        )

        all_ids = _installed_ids(all_dir)
        essential_ids = _installed_ids(ess_dir)
        assert essential_ids, "essential install set unexpectedly empty"
        assert essential_ids < all_ids
