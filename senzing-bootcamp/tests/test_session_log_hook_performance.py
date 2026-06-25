"""Fix-checking tests for the session-log-hook-performance bugfix.

The ``session-log-events`` postToolUse hook is being converted from an
``askAgent`` hook (which forces a full agent round-trip plus a fresh Python
process per write) to a ``runCommand`` hook backed by a new stdlib helper
``scripts/log_write_event.py`` so the IDE appends the log line directly.

This module contains:

* ``TestHookUsesRunCommand`` (Property 1) — parses the real hook file and
  asserts the ``then`` block is a ``runCommand`` referencing
  ``log_write_event.py``. This test is **authored to FAIL on the unfixed
  code** (the hook is still ``askAgent``); its failure confirms the bug.
* ``TestLogWriteEventBehavior`` — behavioral checks for the new helper script
  (appends exactly one valid JSONL line, defaults the module to ``0``, fails
  silently, and prints nothing to stdout). The helper does not exist yet, so
  these tests skip gracefully until ``scripts/log_write_event.py`` is added,
  then pass.

Feature: session-log-hook-performance
Requirements: 2.1, 2.2, 2.3, 2.4
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup for importing scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_SCRIPTS_DIR: str = str(_POWER_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_HOOKS_DIR: Path = _POWER_ROOT / "hooks"
_HOOK_FILE: Path = _HOOKS_DIR / "session-log-events.kiro.hook"

_PROGRESS_PATH: str = "config/bootcamp_progress.json"
_SESSION_LOG_PATH: str = "config/session_log.jsonl"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_hook() -> dict:
    """Parse the real session-log-events hook file as JSON."""
    return json.loads(_HOOK_FILE.read_text(encoding="utf-8"))


def _load_log_write_event():
    """Import the ``log_write_event`` helper, or ``None`` if it doesn't exist yet."""
    try:
        module = importlib.import_module("log_write_event")
    except Exception:  # pragma: no cover - script not added yet
        return None
    return importlib.reload(module)


# ---------------------------------------------------------------------------
# Property 1 (Fix Checking) — logging uses runCommand, not an agent round-trip
# ---------------------------------------------------------------------------


class TestHookUsesRunCommand:
    """The session-log-events hook logs via ``runCommand``, not ``askAgent``.

    **Validates: Requirements 2.1**

    Authored to FAIL on the unfixed hook (still ``askAgent``) and PASS after
    the hook is converted to a ``runCommand`` invoking ``log_write_event.py``.
    """

    def test_hook_file_exists(self) -> None:
        """The hook file must exist."""
        assert _HOOK_FILE.exists(), f"hook file not found at {_HOOK_FILE}"

    def test_hook_uses_run_command(self) -> None:
        """``then.type`` is ``runCommand`` and the command runs ``log_write_event.py``.

        FAILS on unfixed code where ``then.type`` is still ``askAgent``.
        """
        hook = _read_hook()
        then = hook.get("then", {})

        assert then.get("type") == "runCommand", (
            "session-log-events hook must log via 'runCommand' (no agent "
            f"round-trip), got then.type={then.get('type')!r}. The hook is "
            "still an 'askAgent' hook — this confirms the performance bug."
        )

        command = then.get("command", "")
        assert "log_write_event.py" in command, (
            "runCommand must invoke the log_write_event.py helper, got "
            f"command={command!r}"
        )


# ---------------------------------------------------------------------------
# Behavioral checks for the new helper (skipped until the script is added)
# ---------------------------------------------------------------------------


class TestLogWriteEventBehavior:
    """The ``log_write_event.py`` helper appends one valid, silent log line.

    **Validates: Requirements 2.2, 2.3, 2.4**

    These tests skip gracefully while ``scripts/log_write_event.py`` does not
    exist, then pass once the helper is implemented.
    """

    @pytest.fixture()
    def workspace(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a temp workspace with a config/ dir and chdir into it.

        The helper resolves ``config/bootcamp_progress.json`` and
        ``config/session_log.jsonl`` relative to the current working directory.
        """
        (tmp_path / "config").mkdir()
        monkeypatch.chdir(tmp_path)
        return tmp_path

    def _module_or_skip(self):
        """Return the helper module, skipping the test if it isn't present yet."""
        module = _load_log_write_event()
        if module is None:
            pytest.skip("scripts/log_write_event.py does not exist yet")
        return module

    def _read_log_lines(self, workspace: Path) -> list[str]:
        """Return non-empty lines from the session log in *workspace*."""
        log_file = workspace / _SESSION_LOG_PATH
        if not log_file.exists():
            return []
        return [line for line in log_file.read_text(encoding="utf-8").splitlines() if line]

    def test_appends_one_valid_jsonl_line(self, workspace: Path) -> None:
        """One run appends exactly one valid single-line JSON entry with the module."""
        module = self._module_or_skip()
        (workspace / _PROGRESS_PATH).write_text(
            json.dumps({"current_module": 5}), encoding="utf-8"
        )

        rc = module.main([])

        assert rc == 0
        lines = self._read_log_lines(workspace)
        assert len(lines) == 1, f"expected exactly one log line, got {len(lines)}"
        entry = json.loads(lines[0])  # must parse as JSON
        assert entry.get("timestamp"), "entry must contain a timestamp"
        assert entry.get("module") == 5, "entry module must match current_module"

    def test_defaults_module_zero(self, workspace: Path) -> None:
        """With no/unreadable progress file, the appended entry uses module 0."""
        module = self._module_or_skip()
        # No progress file created in this workspace.

        rc = module.main([])

        assert rc == 0
        lines = self._read_log_lines(workspace)
        assert len(lines) == 1, f"expected exactly one log line, got {len(lines)}"
        entry = json.loads(lines[0])
        assert entry.get("module") == 0, "entry must default to module 0"

    def test_fails_silently(self, workspace: Path) -> None:
        """An unwritable log target makes main return 0 without raising."""
        module = self._module_or_skip()
        # Make the log path a directory so the append cannot create the file.
        log_target = workspace / _SESSION_LOG_PATH
        log_target.mkdir(parents=True, exist_ok=True)

        rc = module.main([])  # must not raise

        assert rc == 0, "helper must fail silently (return 0) on any error"

    def test_no_stdout(self, workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """The helper produces zero user-facing stdout output."""
        module = self._module_or_skip()
        (workspace / _PROGRESS_PATH).write_text(
            json.dumps({"current_module": 3}), encoding="utf-8"
        )

        module.main([])

        captured = capsys.readouterr()
        assert captured.out == "", f"helper must print nothing to stdout, got {captured.out!r}"
