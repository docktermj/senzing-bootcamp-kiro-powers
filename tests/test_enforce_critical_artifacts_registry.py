"""Registry-sync tests for the enforce-critical-artifacts hook.

Validates that the new enforcement hook is correctly registered:

1. It is listed in ``hook-categories.yaml`` under the ``any`` bucket.
2. It has an entry in the ``agentstop_order`` precedence list.
3. ``hooks.lock.yaml`` is in sync — the hook is present with an ``event_type``
   matching the ``.json`` v1 hook file's ``trigger``, and
   ``sync_hook_registry.py --verify`` exits 0 on the canonical repository.

Mirrors the existing registry-preservation / sync tests
(``test_hook_categories_sync.py``, ``test_agentstop_order_properties.py``,
``test_commonmark_hook_rescope.py``).

**Validates: Requirements 6.4**
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import HOOKS_DIR, load_hook, load_hook_wrapper, parse_categories_yaml

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent

HOOK_ID = "enforce-critical-artifacts"
HOOK_FILE = HOOKS_DIR / f"{HOOK_ID}.json"
CATEGORIES_PATH = HOOKS_DIR / "hook-categories.yaml"
LOCKFILE_PATH = HOOKS_DIR / "hooks.lock.yaml"
SYNC_SCRIPT = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "sync_hook_registry.py"


# ---------------------------------------------------------------------------
# Minimal stdlib parsers (no PyYAML), consistent with the repo convention
# ---------------------------------------------------------------------------


def _strip_scalar(value: str) -> str:
    """Strip surrounding quotes and whitespace from a YAML scalar."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_agentstop_order_ids(path: Path = CATEGORIES_PATH) -> list[str]:
    """Parse ordered ``id`` values from the ``agentstop_order`` YAML block."""
    ids: list[str] = []
    in_block = False
    id_pattern = re.compile(r"^\s*-\s*id:\s*(.+?)\s*$")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            in_block = stripped[:-1].strip() == "agentstop_order"
            continue
        if in_block:
            match = id_pattern.match(line)
            if match:
                ids.append(_strip_scalar(match.group(1)))
    return ids


def _parse_lockfile(path: Path = LOCKFILE_PATH) -> dict[str, dict[str, str]]:
    """Parse hooks.lock.yaml into a mapping of hook id -> field dict."""
    entries: dict[str, dict[str, str]] = {}
    current_id: str | None = None
    in_hooks_block = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "hooks:" and not raw_line.startswith(" "):
            in_hooks_block = True
            continue
        if not in_hooks_block:
            continue
        item_match = re.match(r"^-\s*id:\s*(.+)$", stripped)
        if item_match:
            current_id = _strip_scalar(item_match.group(1))
            entries[current_id] = {"id": current_id}
            continue
        kv_match = re.match(r"^([A-Za-z_]+):\s*(.+)$", stripped)
        if kv_match and current_id is not None:
            entries[current_id][kv_match.group(1)] = _strip_scalar(kv_match.group(2))
    return entries


# ---------------------------------------------------------------------------
# Module-level data
# ---------------------------------------------------------------------------

_categories = parse_categories_yaml()
_agentstop_order_ids = _parse_agentstop_order_ids()
_lock_entries = _parse_lockfile()
_hook_data = load_hook(HOOK_FILE)
_hook_wrapper = load_hook_wrapper(HOOK_FILE)


class TestEnforceCriticalArtifactsInCategories:
    """The hook is registered in hook-categories.yaml under the ``any`` bucket.

    **Validates: Requirements 6.4**
    """

    def test_hook_file_exists(self) -> None:
        """The hook file exists on disk."""
        assert HOOK_FILE.exists(), f"Hook file not found at {HOOK_FILE}"

    def test_registered_in_any_bucket(self) -> None:
        """The hook appears under the ``any`` bucket (module-any) in categories."""
        any_bucket = _categories.get("module-any", [])
        assert HOOK_ID in any_bucket, (
            f'"{HOOK_ID}" is not registered in the `any` bucket of '
            f"hook-categories.yaml; found: {any_bucket}"
        )

    def test_not_in_other_top_level_buckets(self) -> None:
        """The hook is not duplicated into critical or a numbered module bucket."""
        critical = _categories.get("critical", [])
        assert HOOK_ID not in critical, (
            f'"{HOOK_ID}" must not appear in the critical bucket'
        )
        numbered = [
            cat for cat in _categories
            if cat.startswith("module-") and cat != "module-any"
        ]
        for cat in numbered:
            assert HOOK_ID not in _categories[cat], (
                f'"{HOOK_ID}" must not appear in {cat}; it belongs in `any`'
            )


class TestEnforceCriticalArtifactsInAgentStopOrder:
    """The hook has an entry in the ``agentstop_order`` precedence list.

    **Validates: Requirements 6.4**
    """

    def test_present_in_agentstop_order(self) -> None:
        """The hook id appears in the agentstop_order list."""
        assert HOOK_ID in _agentstop_order_ids, (
            f'"{HOOK_ID}" is not listed in agentstop_order; '
            f"found: {_agentstop_order_ids}"
        )

    def test_agentstop_order_has_no_duplicates(self) -> None:
        """The agentstop_order list contains no duplicate ids."""
        assert len(_agentstop_order_ids) == len(set(_agentstop_order_ids)), (
            f"agentstop_order contains duplicate ids: {_agentstop_order_ids}"
        )

    def test_ordered_after_higher_priority_hooks(self) -> None:
        """The hook runs after module-recap-append and the gate/celebration hooks.

        Per the design, it is placed at the end so its blocking output appears
        only after higher-priority output clears and after the recap section is
        captured.
        """
        idx = _agentstop_order_ids.index(HOOK_ID)
        for predecessor in (
            "module-recap-append",
            "module-completion-celebration",
            "enforce-gate-on-stop",
        ):
            assert predecessor in _agentstop_order_ids, (
                f"expected {predecessor} in agentstop_order"
            )
            assert idx > _agentstop_order_ids.index(predecessor), (
                f'"{HOOK_ID}" must be ordered after "{predecessor}"'
            )


class TestEnforceCriticalArtifactsLockfileSync:
    """hooks.lock.yaml is in sync with the hook file and the registry.

    **Validates: Requirements 6.4**
    """

    def test_present_in_lockfile(self) -> None:
        """The hook appears in hooks.lock.yaml."""
        assert HOOK_ID in _lock_entries, (
            f'"{HOOK_ID}" not present in {LOCKFILE_PATH}'
        )

    def test_lockfile_event_type_matches_hook_file(self) -> None:
        """The lock file event_type matches the hook file's 1.0 trigger."""
        lock_event_type = _lock_entries[HOOK_ID].get("event_type")
        hook_trigger = _hook_data["trigger"]
        assert lock_event_type == hook_trigger == "Stop", (
            f'Lock event_type "{lock_event_type}" must equal hook trigger '
            f'"{hook_trigger}" and be "Stop"'
        )

    def test_lockfile_version_matches_hook_file(self) -> None:
        """The lock file version matches the hook file's ``v1`` wrapper version."""
        assert _lock_entries[HOOK_ID].get("version") == _hook_wrapper["version"], (
            f'Lock version "{_lock_entries[HOOK_ID].get("version")}" != hook '
            f'wrapper version "{_hook_wrapper["version"]}"'
        )

    def test_sync_hook_registry_verify_passes(self) -> None:
        """Running sync_hook_registry.py --verify exits 0 (registry in sync)."""
        result = subprocess.run(
            ["python3", str(SYNC_SCRIPT), "--verify"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"sync_hook_registry.py --verify failed (exit {result.returncode}).\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
