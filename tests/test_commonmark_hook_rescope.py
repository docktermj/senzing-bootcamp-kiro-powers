"""Tests for the commonmark-validation manual invocation path.

Historically the CommonMark validation hook was re-scoped from a per-edit
``fileEdited`` trigger to a single manual (``userTriggered``) graduation-time
pass. Under the Kiro 1.0 migration the ``userTriggered`` trigger no longer
exists, so this manual hook was converted to the ``/commonmark-validation``
slash-command steering file (``steering/slash-commonmark-validation.md``). The
behavioral intent is unchanged — CommonMark validation is still available as a
single on-demand pass, never as a per-edit automatic hook.

This test preserves that intent for the v1 reality:

* ``commonmark-validation`` is NOT a shipped hook (no ``.json``/``.kiro.hook``
  file, absent from ``hooks.lock.yaml`` and ``hook-categories.yaml``).
* The Slash_Command_File exists, is manually invoked, and preserves the
  CommonMark instruction text.

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import HOOKS_DIR

# ---------------------------------------------------------------------------
# Module-level data
# ---------------------------------------------------------------------------

HOOK_ID = "commonmark-validation"
_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
STEERING_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "steering"
SLASH_COMMAND_FILE: Path = STEERING_DIR / "slash-commonmark-validation.md"
LOCKFILE_PATH: Path = HOOKS_DIR / "hooks.lock.yaml"


def _read_slash_command() -> str:
    """Return the slash-command steering file text."""
    return SLASH_COMMAND_FILE.read_text(encoding="utf-8")


# ===========================================================================
# TestCommonmarkNotAShippedHook — Req 4.4
# ===========================================================================


class TestCommonmarkNotAShippedHook:
    """The former manual hook no longer ships as a hook definition."""

    def test_no_v1_hook_file(self):
        """No ``commonmark-validation.json`` v1 hook file ships (Req 4.4)."""
        assert not (HOOKS_DIR / f"{HOOK_ID}.json").exists(), (
            "commonmark-validation must not ship as a v1 hook file — "
            "it is now the /commonmark-validation slash command"
        )

    def test_no_legacy_hook_file(self):
        """No legacy ``commonmark-validation.kiro.hook`` file remains (Req 4.4)."""
        assert not (HOOKS_DIR / f"{HOOK_ID}.kiro.hook").exists(), (
            "legacy commonmark-validation.kiro.hook must be removed"
        )

    def test_absent_from_lockfile(self):
        """commonmark-validation is not present in hooks.lock.yaml (Req 4.4)."""
        lock_text = LOCKFILE_PATH.read_text(encoding="utf-8")
        assert f"id: {HOOK_ID}" not in lock_text, (
            "commonmark-validation must not appear in hooks.lock.yaml"
        )

    def test_absent_from_categories(self):
        """commonmark-validation is not listed in hook-categories.yaml (Req 4.4)."""
        categories_text = (HOOKS_DIR / "hook-categories.yaml").read_text(
            encoding="utf-8"
        )
        assert HOOK_ID not in categories_text, (
            "commonmark-validation must not appear in hook-categories.yaml"
        )


# ===========================================================================
# TestCommonmarkSlashCommand — Req 4.1, 4.2, 4.3
# ===========================================================================


class TestCommonmarkSlashCommand:
    """The CommonMark validation intent is preserved as a slash command."""

    def test_slash_command_file_exists(self):
        """The slash-command steering file exists (Req 4.1)."""
        assert SLASH_COMMAND_FILE.exists(), (
            f"Slash command file not found at {SLASH_COMMAND_FILE}"
        )

    def test_manual_invocation(self):
        """The slash command is configured for manual invocation (Req 4.3)."""
        text = _read_slash_command()
        assert re.search(r"^inclusion:\s*manual\s*$", text, re.MULTILINE), (
            "Slash command file must declare `inclusion: manual` frontmatter"
        )

    def test_instruction_text_preserved(self):
        """The CommonMark instruction text is preserved (Req 4.2)."""
        text = _read_slash_command()
        # Key instruction fragments from the former hook prompt must survive.
        for fragment in (
            "CommonMark compliance",
            "MD022",
            "MD040",
            "MD031",
            "MD032",
        ):
            assert fragment in text, (
                f"Slash command must preserve instruction fragment: {fragment!r}"
            )

    def test_documents_replacement_of_manual_hook(self):
        """The slash command notes it replaces the former manual hook (Req 4.1)."""
        text = _read_slash_command()
        assert "commonmark-validation" in text, (
            "Slash command should reference the former commonmark-validation hook"
        )
