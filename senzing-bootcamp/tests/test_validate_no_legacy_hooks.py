"""Unit tests for the stale-legacy-reference gate (validate_no_legacy_hooks).

Feature: kiro-1-0-migration

Concrete, example-based unit tests for the gate that fails CI when a shipped
artifact still references the legacy ``*.kiro.hook`` / ``when``-``then`` hook
schema (Requirement 14.5). Each test builds a synthetic repo root under
``tmp_path`` with fabricated shipped files, so the detection logic is exercised
against controlled fixtures rather than the real shipped tree (the real-tree
pass is asserted separately in ``tests/test_no_legacy_references_gate.py``).

Covered behaviour:
    * A fully-migrated synthetic tree yields no findings (exit 0).
    * A residual ``*.kiro.hook`` file is flagged; one under ``scripts/`` or
      ``tests/`` (legitimate migration data) is not.
    * A hook ``.json`` with a ``when``/``then`` block, a legacy trigger value, or
      a legacy action type is flagged; a valid v1 hook is not.
    * A hook config ``.yaml`` with a legacy trigger value or a ``.kiro.hook``
      path is flagged; the 1.0 ``PreToolUse`` value (differing only by case) is
      not.
    * Docs/steering markdown: a legacy identifier or ``.kiro.hook`` presented as
      current schema is flagged, but the same identifier on migration/removal
      prose (carrying a marker) is not; an embedded legacy JSON definition is
      flagged unconditionally.
    * ``main`` returns 1 when findings exist and 0 when clean.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_no_legacy_hooks as gate  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _mkpower(repo_root: Path) -> Path:
    """Create ``<repo_root>/senzing-bootcamp/{hooks,steering,docs/guides}``.

    Args:
        repo_root: The temp directory acting as the repository root.

    Returns:
        The created ``senzing-bootcamp`` power directory.
    """
    power = repo_root / "senzing-bootcamp"
    (power / "hooks").mkdir(parents=True, exist_ok=True)
    (power / "steering").mkdir(parents=True, exist_ok=True)
    (power / "docs" / "guides").mkdir(parents=True, exist_ok=True)
    return power


def _write(path: Path, text: str) -> None:
    """Write ``text`` to ``path``, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_v1_hook(name: str, trigger: str, matcher: str | None) -> str:
    """Return a serialized valid v1 hook wrapper.

    Args:
        name: The hook name.
        trigger: A 1.0 trigger name.
        matcher: The matcher regex, or None for an unscoped trigger.

    Returns:
        The JSON text of a ``{"version": "v1", "hooks": [ ... ]}`` wrapper.
    """
    entry: dict = {
        "name": name,
        "trigger": trigger,
        "action": {"type": "agent", "prompt": "do the thing"},
    }
    if matcher is not None:
        entry["matcher"] = matcher
    return json.dumps({"version": "v1", "hooks": [entry]}, indent=2)


def _seed_clean_tree(repo_root: Path) -> Path:
    """Build a small, fully-migrated synthetic tree and return its power dir."""
    power = _mkpower(repo_root)
    _write(
        power / "hooks" / "code-style-check.json",
        _valid_v1_hook("to check code style", "PostFileSave", r"^src/[^/]*\.py$"),
    )
    _write(
        power / "hooks" / "ask-bootcamper.json",
        _valid_v1_hook("to wait for your answer", "Stop", None),
    )
    _write(
        power / "hooks" / "hooks.lock.yaml",
        "hooks:\n  - id: ask-bootcamper\n    event_type: Stop\n"
        "  - id: write-policy-gate\n    event_type: PreToolUse\n",
    )
    _write(
        power / "steering" / "hook-architecture.md",
        "Under Kiro 1.0 the end-of-turn event is the `Stop` trigger "
        "(the legacy `agentStop` event renamed).\n",
    )
    _write(
        power / "docs" / "guides" / "guide.md",
        "Hooks fire on `PostFileSave` and `Stop`. The action is "
        "`{\"type\": \"agent\", \"prompt\": ...}`.\n",
    )
    return power


# ---------------------------------------------------------------------------
# Clean tree
# ---------------------------------------------------------------------------


class TestCleanTree:
    """A fully-migrated synthetic tree produces no findings.

    Validates: Requirement 14.5 (the gate PASSES against a migrated tree)
    """

    def test_clean_tree_has_no_findings(self, tmp_path: Path) -> None:
        _seed_clean_tree(tmp_path)
        assert gate.scan_power(tmp_path) == []

    def test_main_returns_zero_on_clean_tree(self, tmp_path: Path) -> None:
        _seed_clean_tree(tmp_path)
        assert gate.main(["--repo-root", str(tmp_path)]) == 0


# ---------------------------------------------------------------------------
# Legacy *.kiro.hook files
# ---------------------------------------------------------------------------


class TestLegacyHookFiles:
    """Residual ``*.kiro.hook`` files are flagged; tooling copies are not.

    Validates: Requirement 14.5 (reintroduced legacy hook file fails the gate)
    """

    def test_kiro_hook_file_is_flagged(self, tmp_path: Path) -> None:
        power = _seed_clean_tree(tmp_path)
        _write(power / "hooks" / "old-hook.kiro.hook", '{"when": {}, "then": {}}')

        findings = gate.scan_power(tmp_path)

        assert any(f.path.endswith("old-hook.kiro.hook") for f in findings)
        assert gate.main(["--repo-root", str(tmp_path)]) == 1

    def test_kiro_hook_under_scripts_or_tests_is_excluded(self, tmp_path: Path) -> None:
        """Legacy names as migration data under scripts/ and tests/ are ignored."""
        power = _seed_clean_tree(tmp_path)
        _write(power / "scripts" / "fixture.kiro.hook", '{"when": {}}')
        _write(power / "tests" / "fixture.kiro.hook", '{"then": {}}')

        legacy_file_findings = gate.find_legacy_hook_files(power, tmp_path)

        assert legacy_file_findings == []


# ---------------------------------------------------------------------------
# Hook JSON schema shape
# ---------------------------------------------------------------------------


class TestHookJsonShape:
    """Legacy-shaped hook JSON is flagged; valid v1 hooks are not.

    Validates: Requirement 14.5 (when/then hook JSON or legacy trigger/action)
    """

    def test_when_then_block_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "legacy.json",
            json.dumps(
                {
                    "name": "x",
                    "when": {"type": "fileEdited", "patterns": ["*.py"]},
                    "then": {"type": "askAgent", "prompt": "p"},
                },
                indent=2,
            ),
        )
        findings = gate.scan_hook_json_files(power, tmp_path)
        details = " ".join(f.detail for f in findings)
        assert "when" in details and "then" in details
        assert all(f.line > 0 for f in findings)

    def test_legacy_trigger_value_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "bad-trigger.json",
            json.dumps(
                {
                    "version": "v1",
                    "hooks": [
                        {
                            "name": "x",
                            "trigger": "agentStop",
                            "action": {"type": "agent", "prompt": "p"},
                        }
                    ],
                },
                indent=2,
            ),
        )
        findings = gate.scan_hook_json_files(power, tmp_path)
        assert any('legacy trigger "agentStop"' in f.detail for f in findings)

    def test_legacy_action_type_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "bad-action.json",
            json.dumps(
                {
                    "version": "v1",
                    "hooks": [
                        {
                            "name": "x",
                            "trigger": "Stop",
                            "action": {"type": "askAgent", "prompt": "p"},
                        }
                    ],
                },
                indent=2,
            ),
        )
        findings = gate.scan_hook_json_files(power, tmp_path)
        assert any('legacy action type "askAgent"' in f.detail for f in findings)

    def test_valid_v1_hook_not_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "ok.json",
            _valid_v1_hook("to write", "PreToolUse", "fs_write|str_replace|fs_append"),
        )
        assert gate.scan_hook_json_files(power, tmp_path) == []

    def test_invalid_json_with_legacy_tokens_flagged(self, tmp_path: Path) -> None:
        """A malformed hook JSON still gets a line scan for legacy tokens."""
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "broken.json",
            '{ "when": { "type": "fileEdited" },,, ]',  # deliberately invalid JSON
        )
        findings = gate.scan_hook_json_files(power, tmp_path)
        details = " ".join(f.detail for f in findings)
        assert "when/then" in details or "fileEdited" in details


# ---------------------------------------------------------------------------
# Hook config YAML
# ---------------------------------------------------------------------------


class TestHookConfigYaml:
    """Legacy trigger values and ``.kiro.hook`` paths in configs are flagged.

    Validates: Requirement 14.5 (legacy trigger/action in a shipped config)
    """

    def test_legacy_trigger_value_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "hooks.lock.yaml",
            "hooks:\n  - id: ask-bootcamper\n    event_type: agentStop\n",
        )
        findings = gate.scan_hook_config_files(power, tmp_path)
        assert any('"agentStop"' in f.detail for f in findings)
        assert any(f.line == 3 for f in findings)

    def test_kiro_hook_path_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "hook-categories.yaml",
            "critical:\n  - senzing-bootcamp/hooks/ask-bootcamper.kiro.hook\n",
        )
        findings = gate.scan_hook_config_files(power, tmp_path)
        assert any("*.kiro.hook" in f.detail for f in findings)

    def test_v1_trigger_value_not_flagged_case_sensitive(self, tmp_path: Path) -> None:
        """``event_type: PreToolUse`` (1.0) must not match legacy ``preToolUse``."""
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "hooks.lock.yaml",
            "hooks:\n"
            "  - id: write-policy-gate\n    event_type: PreToolUse\n"
            "  - id: session-log-events\n    event_type: PostToolUse\n"
            "  - id: ask-bootcamper\n    event_type: Stop\n",
        )
        assert gate.scan_hook_config_files(power, tmp_path) == []

    def test_agentstop_order_key_not_flagged(self, tmp_path: Path) -> None:
        """The ``agentstop_order`` key (lowercase, key position) is not a value."""
        power = _mkpower(tmp_path)
        _write(
            power / "hooks" / "hook-categories.yaml",
            "agentstop_order:\n  - id: ask-bootcamper\n    order: 1\n",
        )
        assert gate.scan_hook_config_files(power, tmp_path) == []


# ---------------------------------------------------------------------------
# Markdown (docs / steering)
# ---------------------------------------------------------------------------


class TestMarkdownScan:
    """Docs/steering: stale schema is flagged; migration prose is not.

    Validates: Requirement 14.5 (a document still referencing the legacy schema)
    """

    def test_legacy_identifier_as_current_schema_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "docs" / "guides" / "arch.md",
            "The hook fires on `agentStop` after every response.\n",
        )
        findings = gate.scan_markdown_files(power, tmp_path)
        assert any("agentStop" in f.detail for f in findings)
        assert any(f.line == 1 for f in findings)

    def test_kiro_hook_in_prose_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "docs" / "guides" / "arch.md",
            "Each hook is a `.kiro.hook` JSON file in `hooks/`.\n",
        )
        findings = gate.scan_markdown_files(power, tmp_path)
        assert any("*.kiro.hook" in f.detail for f in findings)

    def test_migration_prose_with_marker_not_flagged(self, tmp_path: Path) -> None:
        """A legacy name on a marker-bearing line is legitimate documentation."""
        power = _mkpower(tmp_path)
        _write(
            power / "steering" / "hook-architecture.md",
            "Under Kiro 1.0 the `Stop` trigger is the legacy `agentStop` event "
            "renamed.\n"
            "The former `commonmark-validation` hook is now the "
            "`/commonmark-validation` slash command.\n"
            "Kiro 1.0 removed the manual (`userTriggered`) trigger.\n",
        )
        assert gate.scan_markdown_files(power, tmp_path) == []

    def test_v1_names_in_prose_not_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "docs" / "guides" / "arch.md",
            "Triggers include `PostFileSave`, `PreToolUse`, `PostToolUse`, and "
            "`Stop`.\n",
        )
        assert gate.scan_markdown_files(power, tmp_path) == []

    def test_embedded_legacy_json_definition_flagged(self, tmp_path: Path) -> None:
        """An embedded legacy hook JSON block is stale regardless of markers."""
        power = _mkpower(tmp_path)
        _write(
            power / "docs" / "guides" / "arch.md",
            "Example (legacy, for historical reference):\n"
            '    { "when": { "type": "fileEdited" }, '
            '"then": { "type": "askAgent" } }\n',
        )
        findings = gate.scan_markdown_files(power, tmp_path)
        details = " ".join(f.detail for f in findings)
        assert "when/then" in details or "askAgent" in details

    def test_createhook_with_legacy_trigger_flagged(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(
            power / "steering" / "onboarding.md",
            "Call createHook with trigger fileEdited to watch source files.\n",
        )
        findings = gate.scan_markdown_files(power, tmp_path)
        assert any("createHook" in f.detail or "fileEdited" in f.detail for f in findings)


# ---------------------------------------------------------------------------
# main / reporting
# ---------------------------------------------------------------------------


class TestMainExitCodes:
    """``main`` maps findings to exit codes.

    Validates: Requirement 14.5 (the gate fails CI on a stale reference)
    """

    def test_main_returns_one_with_findings(self, tmp_path: Path) -> None:
        power = _seed_clean_tree(tmp_path)
        _write(power / "hooks" / "old.kiro.hook", "{}")
        assert gate.main(["--repo-root", str(tmp_path)]) == 1

    def test_findings_are_sorted_by_path_then_line(self, tmp_path: Path) -> None:
        power = _mkpower(tmp_path)
        _write(power / "docs" / "guides" / "b.md", "fires on `agentStop`\n")
        _write(power / "docs" / "guides" / "a.md", "uses `fileEdited` trigger\n")
        findings = gate.scan_power(tmp_path)
        keys = [(f.path, f.line) for f in findings]
        assert keys == sorted(keys)
