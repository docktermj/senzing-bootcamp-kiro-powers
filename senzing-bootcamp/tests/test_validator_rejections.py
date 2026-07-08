"""Unit tests for the v1 hook validator rejection paths.

Feature: kiro-1-0-migration (Task 4.4)

The Kiro 1.0 migration replaces the legacy ``*.kiro.hook`` schema (a ``when``
block plus a ``then`` block whose ``type`` is ``askAgent``/``runCommand``) with
the ``v1`` wrapper ``{"version": "v1", "hooks": [{name, trigger, matcher,
action}]}``. These tests prove the updated validators REJECT the legacy schema
so a stale definition can never slip through CI.

Two validators share the same 1.0 accept-lists (sourced from ``hook_renames``):

- ``test_hooks.validate_hook(path)`` returns a ``HookTestResult`` with a
  ``.passed`` bool and a ``.failures`` list. It is the primary surface exercised
  here — rejection is asserted as ``result.passed is False`` plus an
  appropriate failure message.
- ``validate_power.check_hooks()`` scans the hooks directory and reports any
  residual ``*.kiro.hook`` file (Req 6.6). This is covered directly by pointing
  the validator's ``POWER_DIR`` at a throwaway ``tmp_path`` containing a legacy
  file, which is the most direct, non-brittle way to prove the residual-file
  report without depending on the shipped hook set.

Validated requirements: 6.3 (reject legacy trigger names), 6.4 (reject
``askAgent``/``runCommand`` action types), 6.6 (report residual
``*.kiro.hook`` / ``when`` / ``then`` shapes). Two additional cases strengthen
6.2/6.5 coverage: a scoped trigger missing its matcher and a matcher that does
not compile.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_power  # noqa: E402
from test_hooks import validate_hook  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_hook_json(tmp_path: Path, hook_id: str, data: dict) -> Path:
    """Write ``data`` as ``<hook_id>.json`` under ``tmp_path`` and return it.

    Args:
        tmp_path: The pytest temp directory to write into.
        hook_id: The hook id / filename stem.
        data: The JSON-serializable object to write.

    Returns:
        The path to the written ``.json`` file.
    """
    path = tmp_path / f"{hook_id}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _valid_entry(**overrides: object) -> dict:
    """Build a schema-valid v1 hook entry, applying any field overrides.

    The baseline uses the unscoped ``Stop`` trigger (no matcher required) and a
    valid ``agent`` action so a single overridden field is the sole reason a
    rejection test fails.

    Args:
        **overrides: Fields to replace on the baseline entry.

    Returns:
        A v1 hook entry dict.
    """
    entry: dict = {
        "name": "Test Hook",
        "trigger": "Stop",
        "action": {"type": "agent", "prompt": "do something"},
    }
    entry.update(overrides)
    return entry


def _wrapper(*entries: dict) -> dict:
    """Wrap one or more entries in the ``{"version": "v1", "hooks": [...]}`` shape.

    Args:
        *entries: The v1 hook entries to include.

    Returns:
        A v1 wrapper dict.
    """
    return {"version": "v1", "hooks": list(entries)}


# ---------------------------------------------------------------------------
# Req 6.3 — reject legacy trigger names
# ---------------------------------------------------------------------------


class TestLegacyTriggerRejection:
    """The validator rejects every legacy trigger name (Req 6.3)."""

    # The eight automatic legacy triggers plus the removed manual trigger. None
    # of these is a valid 1.0 trigger name (the 1.0 names are PostFileSave,
    # PostFileCreate, PostFileDelete, Stop, UserPromptSubmit, PostTaskExec,
    # PreToolUse, PostToolUse).
    LEGACY_TRIGGERS = [
        "fileEdited",
        "fileCreated",
        "fileDeleted",
        "agentStop",
        "promptSubmit",
        "postTaskExecution",
        "preToolUse",
        "postToolUse",
        "userTriggered",
    ]

    @pytest.mark.parametrize("legacy_trigger", LEGACY_TRIGGERS)
    def test_legacy_trigger_is_rejected(
        self, tmp_path: Path, legacy_trigger: str
    ) -> None:
        """A v1 entry carrying a legacy trigger name fails validation."""
        data = _wrapper(_valid_entry(trigger=legacy_trigger))
        path = _write_hook_json(tmp_path, "legacy-trigger", data)

        result = validate_hook(path)

        assert result.passed is False
        assert any(
            "invalid trigger" in f for f in result.failures
        ), f"expected an invalid-trigger failure, got: {result.failures}"


# ---------------------------------------------------------------------------
# Req 6.4 — reject legacy action types
# ---------------------------------------------------------------------------


class TestLegacyActionTypeRejection:
    """The validator rejects the legacy askAgent/runCommand action types (Req 6.4)."""

    @pytest.mark.parametrize(
        "action",
        [
            {"type": "askAgent", "prompt": "do something"},
            {"type": "runCommand", "command": "echo hi"},
        ],
    )
    def test_legacy_action_type_is_rejected(
        self, tmp_path: Path, action: dict
    ) -> None:
        """A v1 entry with a legacy action type fails validation."""
        data = _wrapper(_valid_entry(action=action))
        path = _write_hook_json(tmp_path, "legacy-action", data)

        result = validate_hook(path)

        assert result.passed is False
        assert any(
            "invalid action type" in f for f in result.failures
        ), f"expected an invalid-action-type failure, got: {result.failures}"


# ---------------------------------------------------------------------------
# Req 6.6 — reject residual *.kiro.hook / when / then shapes
# ---------------------------------------------------------------------------


class TestResidualLegacySchemaRejection:
    """The validator rejects any residual legacy when/then shape (Req 6.6)."""

    def test_top_level_when_then_shape_is_rejected(self, tmp_path: Path) -> None:
        """A legacy ``*.kiro.hook``-shaped ``.json`` (top-level when/then) fails."""
        legacy = {
            "name": "Legacy Hook",
            "version": "1.0.0",
            "when": {"type": "fileEdited", "patterns": ["src/**/*.py"]},
            "then": {"type": "askAgent", "prompt": "review the change"},
        }
        path = _write_hook_json(tmp_path, "legacy-when-then", legacy)

        result = validate_hook(path)

        assert result.passed is False
        assert any(
            "when/then" in f.lower() for f in result.failures
        ), f"expected a legacy when/then failure, got: {result.failures}"

    def test_top_level_when_only_is_rejected(self, tmp_path: Path) -> None:
        """A top-level shape carrying only a legacy ``when`` block fails."""
        legacy = {"name": "Legacy", "when": {"type": "agentStop"}}
        path = _write_hook_json(tmp_path, "legacy-when-only", legacy)

        result = validate_hook(path)

        assert result.passed is False
        assert any("when/then" in f.lower() for f in result.failures)

    def test_top_level_then_only_is_rejected(self, tmp_path: Path) -> None:
        """A top-level shape carrying only a legacy ``then`` block fails."""
        legacy = {"name": "Legacy", "then": {"type": "runCommand", "command": "ls"}}
        path = _write_hook_json(tmp_path, "legacy-then-only", legacy)

        result = validate_hook(path)

        assert result.passed is False
        assert any("when/then" in f.lower() for f in result.failures)

    def test_when_then_inside_entry_is_rejected(self, tmp_path: Path) -> None:
        """A v1 wrapper whose entry still carries when/then keys fails."""
        entry = _valid_entry(
            when={"type": "fileEdited", "patterns": ["*.py"]},
            then={"type": "askAgent", "prompt": "x"},
        )
        data = _wrapper(entry)
        path = _write_hook_json(tmp_path, "entry-when-then", data)

        result = validate_hook(path)

        assert result.passed is False
        assert any(
            "when/then" in f.lower() for f in result.failures
        ), f"expected a legacy when/then entry failure, got: {result.failures}"


class TestValidatePowerReportsResidualLegacyFile:
    """``validate_power.check_hooks`` reports a residual ``*.kiro.hook`` file (Req 6.6).

    Pointing ``POWER_DIR`` at a throwaway ``tmp_path`` isolates the check from
    the shipped hook set: with only a legacy file present (and no v1 ``*.json``
    or registry), the sole reported error is the residual-file report.
    """

    def test_residual_kiro_hook_file_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A leftover ``<id>.kiro.hook`` file is reported as a validation error."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "legacy-example.kiro.hook").write_text(
            json.dumps(
                {
                    "name": "Legacy Example",
                    "when": {"type": "agentStop"},
                    "then": {"type": "askAgent", "prompt": "y"},
                }
            ),
            encoding="utf-8",
        )

        # Point the validator at the throwaway tree and capture its findings in
        # fresh error/warning buffers (monkeypatch restores both afterwards).
        monkeypatch.setattr(validate_power, "POWER_DIR", tmp_path)
        monkeypatch.setattr(validate_power, "errors", [])
        monkeypatch.setattr(validate_power, "warnings", [])

        validate_power.check_hooks()

        assert any(
            "legacy-example.kiro.hook" in e for e in validate_power.errors
        ), f"expected the residual .kiro.hook file to be reported, got: {validate_power.errors}"


class TestValidatePowerHelperRejectsLegacyShape:
    """``validate_power`` entry/file helpers reject a legacy when/then shape (Req 6.6)."""

    def test_check_v1_hook_file_rejects_top_level_when_then(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``_check_v1_hook_file`` records an error for a top-level when/then shape."""
        monkeypatch.setattr(validate_power, "errors", [])
        monkeypatch.setattr(validate_power, "warnings", [])

        legacy = {
            "name": "Legacy",
            "when": {"type": "fileEdited", "patterns": ["*.py"]},
            "then": {"type": "askAgent", "prompt": "x"},
        }
        validate_power._check_v1_hook_file(Path("legacy.kiro.hook"), legacy)

        assert any(
            "when/then" in e.lower() for e in validate_power.errors
        ), f"expected a legacy when/then error, got: {validate_power.errors}"


# ---------------------------------------------------------------------------
# Req 6.2 / 6.5 — reject scoped triggers missing a matcher and bad matchers
# ---------------------------------------------------------------------------


class TestMatcherRequirementRejection:
    """Scoped triggers must carry a matcher, and any matcher must compile."""

    @pytest.mark.parametrize(
        ("trigger", "kind"),
        [
            ("PostFileSave", "file-path"),
            ("PostFileCreate", "file-path"),
            ("PostFileDelete", "file-path"),
            ("PreToolUse", "tool-name"),
            ("PostToolUse", "tool-name"),
        ],
    )
    def test_scoped_trigger_missing_matcher_is_rejected(
        self, tmp_path: Path, trigger: str, kind: str
    ) -> None:
        """A scoped 1.0 trigger with no matcher fails validation (Req 6.2)."""
        data = _wrapper(_valid_entry(trigger=trigger))  # baseline omits matcher
        path = _write_hook_json(tmp_path, "missing-matcher", data)

        result = validate_hook(path)

        assert result.passed is False
        assert any(
            f"requires a {kind} matcher" in f for f in result.failures
        ), f"expected a missing-{kind}-matcher failure, got: {result.failures}"

    def test_matcher_that_does_not_compile_is_rejected(
        self, tmp_path: Path
    ) -> None:
        """A present matcher that is not a valid regex fails validation (Req 6.5)."""
        data = _wrapper(
            _valid_entry(trigger="PostFileSave", matcher="[invalid(regex")
        )
        path = _write_hook_json(tmp_path, "bad-matcher", data)

        result = validate_hook(path)

        assert result.passed is False
        assert any(
            "does not compile" in f for f in result.failures
        ), f"expected a matcher-compile failure, got: {result.failures}"
