"""Unit tests for ``sync_hook_registry.py --verify`` against committed output.

These tests validate the *real* committed registry artifacts, so they live in
the repo-root ``tests/`` directory (per the project rule that tests exercising
shipped hook files belong here rather than in ``senzing-bootcamp/tests/``).

Two things are asserted:

1. ``sync_hook_registry.py --verify`` exits 0 against the committed registry
   slices and lockfile — i.e. the shipped artifacts are already in sync with
   what the generator would produce from the ``v1`` hook files.
2. The committed lockfile (``senzing-bootcamp/hooks/hooks.lock.yaml``) records
   exactly 26 hook entries (27 migrated Non_Manual_Hooks minus ``module-recap-append``,
   folded into ``ask-bootcamper`` Phase 0 by the stop-hook-ux bugfix), and every
   entry's ``event_type`` is a valid Kiro 1.0 trigger.

``main()`` in ``sync_hook_registry.py`` parses ``sys.argv`` directly via argparse
and terminates with ``sys.exit()``. Rather than patch ``sys.argv`` and catch
``SystemExit`` in-process, the ``--verify`` check runs the script as a
subprocess with ``cwd`` set to the repository root so the default relative
paths (``HOOKS_DIR``, ``REGISTRY_PATH``, ``LOCKFILE_PATH``) resolve correctly.
This is the most robust invocation and mirrors the existing registry-sync test
(``test_enforce_critical_artifacts_registry.py``).

**Validates: Requirements 7.5**
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the scripts directory importable so we can reuse the authoritative
# 1.0 trigger accept-list (VALID_V1_TRIGGERS) instead of re-listing it here.
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_REPO_ROOT / "senzing-bootcamp" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import hook_renames  # noqa: E402  (import after sys.path manipulation)

SYNC_SCRIPT: Path = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "sync_hook_registry.py"
LOCKFILE_PATH: Path = _REPO_ROOT / "senzing-bootcamp" / "hooks" / "hooks.lock.yaml"

#: The migration converted 27 Non_Manual_Hooks; the stop-hook-ux bugfix then
#: folded ``module-recap-append`` into ``ask-bootcamper`` (Phase 0), leaving 26
#: shipped hooks in the lockfile (Requirement 7 / 7.5).
EXPECTED_HOOK_COUNT = 26


def _parse_lockfile_entries(path: Path) -> list[dict[str, str]]:
    """Parse ``hooks.lock.yaml`` into a list of per-hook field dicts.

    Counts each ``- id:`` list item under the top-level ``hooks:`` block and
    collects its indented ``key: value`` scalars. A minimal stdlib parser is
    used (no PyYAML), consistent with the repo convention.

    Args:
        path: Path to the ``hooks.lock.yaml`` lockfile.

    Returns:
        One dict per hook entry, each with at least an ``id`` key plus any
        scalar fields (``version``, ``category``, ``event_type``).
    """
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_hooks_block = False
    id_item = re.compile(r"^-\s*id:\s*(.+?)\s*$")
    kv = re.compile(r"^([A-Za-z_]+):\s*(.+?)\s*$")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Top-level ``hooks:`` marker (no leading indentation).
        if stripped == "hooks:" and not raw_line.startswith(" "):
            in_hooks_block = True
            continue
        if not in_hooks_block:
            continue
        item_match = id_item.match(stripped)
        if item_match:
            current = {"id": _strip_scalar(item_match.group(1))}
            entries.append(current)
            continue
        kv_match = kv.match(stripped)
        if kv_match and current is not None:
            current[kv_match.group(1)] = _strip_scalar(kv_match.group(2))
    return entries


def _strip_scalar(value: str) -> str:
    """Strip surrounding quotes and whitespace from a YAML scalar."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


# Module-level parse: the lockfile is static during a test run.
_LOCK_ENTRIES: list[dict[str, str]] = _parse_lockfile_entries(LOCKFILE_PATH)


class TestRegistryVerifyCommitted:
    """``sync_hook_registry.py --verify`` succeeds against the committed output.

    **Validates: Requirements 7.5**
    """

    def test_verify_exits_zero(self) -> None:
        """``--verify`` exits 0 — the committed registry/lockfile are in sync."""
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--verify"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"sync_hook_registry.py --verify failed (exit {result.returncode}).\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class TestLockfileEntryCount:
    """The committed lockfile records exactly 26 hook entries.

    **Validates: Requirements 7.5**
    """

    def test_lockfile_exists(self) -> None:
        """The committed lockfile is present on disk."""
        assert LOCKFILE_PATH.exists(), f"Lockfile not found at {LOCKFILE_PATH}"

    def test_lockfile_has_expected_entries(self) -> None:
        """The lockfile lists the 26 shipped hooks (recap folded into ask-bootcamper)."""
        assert len(_LOCK_ENTRIES) == EXPECTED_HOOK_COUNT, (
            f"Expected {EXPECTED_HOOK_COUNT} lockfile entries, found "
            f"{len(_LOCK_ENTRIES)}: {[e['id'] for e in _LOCK_ENTRIES]}"
        )

    def test_lockfile_ids_are_unique(self) -> None:
        """No hook id is duplicated in the lockfile."""
        ids = [e["id"] for e in _LOCK_ENTRIES]
        assert len(ids) == len(set(ids)), (
            f"Lockfile contains duplicate hook ids: {ids}"
        )

    def test_every_entry_has_valid_v1_trigger(self) -> None:
        """Each entry's ``event_type`` is a valid Kiro 1.0 trigger name."""
        for entry in _LOCK_ENTRIES:
            event_type = entry.get("event_type")
            assert event_type is not None, (
                f"Lockfile entry {entry['id']!r} is missing 'event_type'"
            )
            assert event_type in hook_renames.VALID_V1_TRIGGERS, (
                f"Lockfile entry {entry['id']!r} has event_type "
                f"{event_type!r}, which is not a valid 1.0 trigger "
                f"({sorted(hook_renames.VALID_V1_TRIGGERS)})"
            )
