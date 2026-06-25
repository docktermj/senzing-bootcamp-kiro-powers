"""Tests for the re-scoped commonmark-validation hook.

Validates that the CommonMark validation hook has been re-scoped from a
per-edit ``fileEdited`` trigger on ``**/*.md`` to a single ``userTriggered``
graduation-time pass, that it remains a valid Kiro hook, and that it stays
consistent with the generated hook lock file.

Validates: Requirements 8.3, 4.1, 4.5, 4.6
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import HOOKS_DIR, load_hook, validate_required_fields

# ---------------------------------------------------------------------------
# Module-level data
# ---------------------------------------------------------------------------

HOOK_ID = "commonmark-validation"
HOOK_PATH: Path = HOOKS_DIR / f"{HOOK_ID}.kiro.hook"
LOCKFILE_PATH: Path = HOOKS_DIR / "hooks.lock.yaml"

# Fields that make a hook a valid Kiro hook (top-level + nested).
VALID_HOOK_FIELDS: list[str] = ["name", "version", "when.type", "then.type"]


def _strip_scalar(value: str) -> str:
    """Strip surrounding quotes and whitespace from a YAML scalar."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_lockfile(path: Path) -> dict[str, dict[str, str]]:
    """Parse hooks.lock.yaml into a mapping of hook id -> field dict.

    The lock file is a deterministic, machine-generated list of hook entries
    of the form::

        hooks:
          - id: commonmark-validation
            version: "2.0.0"
            category: critical
            event_type: userTriggered

    Uses a minimal stdlib parser (no PyYAML) consistent with the repo's
    custom-YAML-parser convention.

    Args:
        path: Path to the hooks.lock.yaml file.

    Returns:
        Dict mapping hook id to a dict of its scalar fields.
    """
    entries: dict[str, dict[str, str]] = {}
    current_id: str | None = None
    in_hooks_block = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Enter the top-level `hooks:` list block.
        if stripped == "hooks:" and not raw_line.startswith(" "):
            in_hooks_block = True
            continue
        if not in_hooks_block:
            continue

        # A new list item starts with `- id: <value>`.
        item_match = re.match(r"^-\s*id:\s*(.+)$", stripped)
        if item_match:
            current_id = _strip_scalar(item_match.group(1))
            entries[current_id] = {"id": current_id}
            continue

        # Subsequent `key: value` lines belong to the current item.
        kv_match = re.match(r"^([A-Za-z_]+):\s*(.+)$", stripped)
        if kv_match and current_id is not None:
            key = kv_match.group(1)
            entries[current_id][key] = _strip_scalar(kv_match.group(2))

    return entries


_hook_data = load_hook(HOOK_PATH)
_lock_entries = _parse_lockfile(LOCKFILE_PATH)


# ===========================================================================
# TestCommonmarkHookRescope — Req 8.3, 4.1, 4.5, 4.6
# ===========================================================================

class TestCommonmarkHookRescope:
    """Verify the commonmark-validation hook is re-scoped to userTriggered."""

    def test_hook_file_exists(self):
        """The hook file exists on disk."""
        assert HOOK_PATH.exists(), f"Hook file not found at {HOOK_PATH}"

    def test_hook_is_valid_kiro_hook(self):
        """The hook contains name, version, when, then (valid Kiro hook) (Req 4.6)."""
        missing = validate_required_fields(_hook_data)
        # Ensure the core valid-hook fields are present at minimum.
        core_missing = [
            f for f in VALID_HOOK_FIELDS
            if f.split(".")[0] not in _hook_data
            or (
                "." in f
                and f.split(".")[1] not in _hook_data.get(f.split(".")[0], {})
            )
        ]
        assert not core_missing, (
            f"Hook missing required valid-hook fields: {core_missing}"
        )
        # No required field (per shared helper) should be missing either.
        assert not missing, f"Hook missing required fields: {missing}"

    def test_when_type_is_user_triggered(self):
        """when.type is userTriggered, NOT a per-edit trigger (Req 4.1)."""
        assert _hook_data["when"]["type"] == "userTriggered", (
            f'Expected when.type == "userTriggered", got '
            f'"{_hook_data["when"].get("type")}"'
        )

    def test_not_file_edited_trigger(self):
        """The hook is no longer a fileEdited trigger (Req 4.1, 4.6)."""
        assert _hook_data["when"]["type"] != "fileEdited", (
            "Hook must not use the per-edit fileEdited trigger"
        )

    def test_no_markdown_glob_patterns(self):
        """The hook does not watch **/*.md patterns (Req 4.1, 4.6)."""
        patterns = _hook_data["when"].get("patterns", [])
        assert "**/*.md" not in patterns, (
            f"Hook must not watch the **/*.md pattern; got patterns={patterns}"
        )
        # A userTriggered hook should carry no file patterns at all.
        assert not patterns, (
            f"userTriggered hook should have no file patterns; got {patterns}"
        )

    def test_name_matches_governance_prefix(self):
        """The hook name starts with 'to ' per governance regex (Req 4.5)."""
        name = _hook_data["name"]
        assert re.match(r"^to ", name), (
            f'Hook name must match ^to ; got "{name}"'
        )

    def test_present_in_lockfile_with_matching_event_type(self):
        """The hook is in hooks.lock.yaml with event_type userTriggered (Req 4.5)."""
        assert HOOK_ID in _lock_entries, (
            f'"{HOOK_ID}" not present in {LOCKFILE_PATH}'
        )
        entry = _lock_entries[HOOK_ID]
        assert entry.get("event_type") == "userTriggered", (
            f'Lock file event_type for "{HOOK_ID}" should be "userTriggered", '
            f'got "{entry.get("event_type")}"'
        )

    def test_lockfile_event_type_matches_hook_file(self):
        """The lock file event_type matches the hook file's when.type (Req 4.5)."""
        lock_event_type = _lock_entries[HOOK_ID].get("event_type")
        hook_event_type = _hook_data["when"]["type"]
        assert lock_event_type == hook_event_type, (
            f"Lock file event_type ({lock_event_type}) does not match hook "
            f"file when.type ({hook_event_type})"
        )
