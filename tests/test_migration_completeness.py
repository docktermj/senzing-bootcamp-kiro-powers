"""Example test for Kiro 1.0 hook migration completeness.

Feature: kiro-1-0-migration

Validates that the one-time migration produced exactly one shipped V1_Hook
``.json`` file for every non-manual legacy hook, that each shipped file is a
schema-valid ``v1`` wrapper, and that the three ``PreToolUse`` write gates carry
the fixed write matcher.

This is a concrete example/edge test over the *real shipped hook files* under
``senzing-bootcamp/hooks/`` (not a Hypothesis property test). The legacy
``*.kiro.hook`` files have been removed from the Power (Req 13.1), so the
expected set of non-manual hook ids is captured here as a self-contained
constant rather than derived by scanning legacy files. The three manual
(``userTriggered``) hooks become slash commands and are intentionally NOT
emitted as ``.json`` files.

**Validates: Requirements 1.1, 5.1, 5.2**
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR: Path = Path("senzing-bootcamp/hooks")

# The three manual (userTriggered) legacy hooks are converted to slash-command
# steering files and are NOT emitted as v1 .json files.
MANUAL_HOOK_IDS: frozenset[str] = frozenset(
    {
        "backup-project-on-request",
        "git-commit-reminder",
        "commonmark-validation",
    }
)

# The 27 non-manual hooks that the migration ships as v1 .json files. The
# migration produced 27 (30 legacy hooks minus the 3 manual hooks); the
# stop-hook-ux bugfix then folded ``module-recap-append`` into ``ask-bootcamper``
# (Phase 0) and deleted the standalone recap hook, leaving 26; the
# durable-qa-capture bugfix then added ``capture-qa-events``, bringing the set
# back to 27. This set is self-contained: the legacy *.kiro.hook files no longer
# exist to scan (Req 13.1), so the expected shipped id set is captured here directly.
EXPECTED_NON_MANUAL_HOOK_IDS: frozenset[str] = frozenset(
    {
        "analyze-after-mapping",
        "ask-bootcamper",
        "backup-before-load",
        "capture-qa-events",
        "code-style-check",
        "data-quality-check",
        "deployment-phase-gate",
        "enforce-critical-artifacts",
        "enforce-gate-on-stop",
        "enforce-mandatory-gate",
        "enforce-mapping-spec",
        "enforce-visualization-offers",
        "error-recovery-context",
        "gate-module3-visualization",
        "module-completion-celebration",
        "review-bootcamper-input",
        "run-tests-after-change",
        "security-scan-on-save",
        "session-log-events",
        "validate-alert-config",
        "validate-benchmark-results",
        "validate-business-problem",
        "validate-data-files",
        "verify-demo-results",
        "verify-generated-code",
        "verify-sdk-setup",
        "write-policy-gate",
    }
)

# 27 migrated v1 hooks minus ``module-recap-append`` (folded into ask-bootcamper
# Phase 0 by the stop-hook-ux bugfix) = 26, plus ``capture-qa-events`` (added by
# the durable-qa-capture bugfix) = 27 shipped v1 hooks (Req 1.1).
EXPECTED_V1_HOOK_COUNT: int = 27

# The three PreToolUse write gates and the fixed 1.0 write matcher.
WRITE_GATE_IDS: tuple[str, ...] = (
    "write-policy-gate",
    "enforce-mandatory-gate",
    "gate-module3-visualization",
)
WRITE_MATCHER: str = "fs_write|str_replace|fs_append"

# 1.0 action types accepted by the v1 schema.
VALID_ACTION_TYPES: frozenset[str] = frozenset({"agent", "command"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict:
    """Parse a JSON hook file and return its top-level object."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _v1_hook_paths() -> list[Path]:
    """Return the shipped v1 hook JSON file paths, sorted by name."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.json"))


def _v1_id(path: Path) -> str:
    """Return the hook id for a v1 ``.json`` file (name without extension)."""
    return path.name[: -len(".json")]


def _v1_hook_ids() -> set[str]:
    """Return the set of shipped v1 hook ids."""
    return {_v1_id(p) for p in _v1_hook_paths()}


def _first_hook_entry(data: dict) -> dict:
    """Return the single hook entry from a v1 wrapper object."""
    hooks = data.get("hooks")
    assert isinstance(hooks, list) and hooks, (
        "v1 wrapper must contain a non-empty 'hooks' array"
    )
    entry = hooks[0]
    assert isinstance(entry, dict), "each 'hooks' entry must be an object"
    return entry


# ===========================================================================
# Migration completeness (Req 1.1, 5.1, 5.2)
# ===========================================================================


class TestMigrationCompleteness:
    """The migration ships 26 v1 hooks — the 27 migrated non-manual ids minus
    ``module-recap-append`` (folded into ``ask-bootcamper`` Phase 0) — and the
    write gates keep the fixed 1.0 write matcher.

    Feature: kiro-1-0-migration
    Validates: Requirements 1.1, 5.1, 5.2
    """

    def test_exactly_27_v1_hook_files_exist(self) -> None:
        """Exactly 27 ``hooks/*.json`` v1 files ship (recap folded in; capture-qa-events added).

        **Validates: Requirements 1.1**
        """
        paths = _v1_hook_paths()
        assert len(paths) == EXPECTED_V1_HOOK_COUNT, (
            f"expected {EXPECTED_V1_HOOK_COUNT} shipped v1 hook files, "
            f"found {len(paths)}: {sorted(p.name for p in paths)}"
        )

    def test_no_legacy_kiro_hook_files_remain(self) -> None:
        """No legacy ``*.kiro.hook`` files remain in the shipped hooks dir.

        The legacy schema is fully removed by the migration (Req 13.1), so the
        shipped id set is self-contained rather than derived from legacy files.

        **Validates: Requirements 1.1**
        """
        legacy = sorted(HOOKS_DIR.glob("*.kiro.hook"))
        assert not legacy, (
            f"legacy *.kiro.hook files must be removed; found "
            f"{sorted(p.name for p in legacy)}"
        )

    def test_v1_ids_equal_expected_non_manual_ids(self) -> None:
        """The set of shipped v1 ids equals the expected non-manual id set.

        One v1 ``.json`` file exists per expected non-manual hook, and no manual
        hook is shipped as a v1 file.

        **Validates: Requirements 1.1**
        """
        v1_ids = _v1_hook_ids()

        missing = EXPECTED_NON_MANUAL_HOOK_IDS - v1_ids
        extra = v1_ids - EXPECTED_NON_MANUAL_HOOK_IDS
        assert v1_ids == set(EXPECTED_NON_MANUAL_HOOK_IDS), (
            f"v1 hook id set does not match expected non-manual id set; "
            f"missing v1 files for {sorted(missing)}, "
            f"unexpected v1 files {sorted(extra)}"
        )

    def test_no_manual_hook_shipped_as_v1_json(self) -> None:
        """None of the three manual hook ids ships as a v1 ``.json`` file.

        This replaces the former ``userTriggered``-scan check: rather than
        reading legacy files, it asserts the known manual ids are absent from
        the shipped ``.json`` set.

        **Validates: Requirements 1.1**
        """
        v1_ids = _v1_hook_ids()
        leaked = v1_ids & set(MANUAL_HOOK_IDS)
        assert not leaked, (
            f"manual hooks must not ship as v1 .json files; found {sorted(leaked)}"
        )

    def test_each_v1_file_is_valid_v1_wrapper(self) -> None:
        """Every shipped ``.json`` file is a schema-valid v1 wrapper.

        Each file wraps ``{"version": "v1", "hooks": [...]}`` and every entry
        carries ``name``, ``trigger``, and an ``action`` with a 1.0 type.

        **Validates: Requirements 1.1**
        """
        for path in _v1_hook_paths():
            data = _load_json(path)
            assert isinstance(data, dict), f"{path.name}: top level must be an object"
            assert data.get("version") == "v1", (
                f"{path.name}: top-level 'version' must be 'v1', "
                f"got {data.get('version')!r}"
            )
            hooks = data.get("hooks")
            assert isinstance(hooks, list) and hooks, (
                f"{path.name}: 'hooks' must be a non-empty array"
            )
            for entry in hooks:
                assert isinstance(entry, dict), (
                    f"{path.name}: each 'hooks' entry must be an object"
                )
                for field in ("name", "trigger", "action"):
                    assert field in entry, (
                        f"{path.name}: hook entry missing required field '{field}'"
                    )
                assert isinstance(entry["name"], str) and entry["name"].strip(), (
                    f"{path.name}: 'name' must be a non-empty string"
                )
                assert isinstance(entry["trigger"], str) and entry["trigger"].strip(), (
                    f"{path.name}: 'trigger' must be a non-empty string"
                )
                action = entry["action"]
                assert isinstance(action, dict), (
                    f"{path.name}: 'action' must be an object"
                )
                assert action.get("type") in VALID_ACTION_TYPES, (
                    f"{path.name}: action.type must be one of "
                    f"{sorted(VALID_ACTION_TYPES)}, got {action.get('type')!r}"
                )

    def test_write_gates_carry_fixed_write_matcher(self) -> None:
        """Each write gate is a ``PreToolUse`` hook with the fixed write matcher.

        The three write gates (``write-policy-gate``, ``enforce-mandatory-gate``,
        ``gate-module3-visualization``) ship as v1 files whose single entry has
        ``trigger == "PreToolUse"`` and ``matcher == "fs_write|str_replace|fs_append"``.

        **Validates: Requirements 5.1, 5.2**
        """
        for gate_id in WRITE_GATE_IDS:
            path = HOOKS_DIR / f"{gate_id}.json"
            assert path.is_file(), f"write gate '{gate_id}' missing at {path}"
            entry = _first_hook_entry(_load_json(path))
            assert entry.get("trigger") == "PreToolUse", (
                f"{gate_id}: trigger must be 'PreToolUse', "
                f"got {entry.get('trigger')!r}"
            )
            assert entry.get("matcher") == WRITE_MATCHER, (
                f"{gate_id}: matcher must be {WRITE_MATCHER!r}, "
                f"got {entry.get('matcher')!r}"
            )
