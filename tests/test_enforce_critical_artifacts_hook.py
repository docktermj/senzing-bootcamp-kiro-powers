"""Schema and command-contract verification for the enforce-critical-artifacts hook.

The enforce-critical-artifacts hook is the enforced guarantee for the bootcamp's
crown-jewel artifacts (the Q&A transcript, the recap Markdown, and the rendered
recap "trophy" PDF). It is a **deterministic ``command`` hook**: rather than
asking the agent (via a prompt) to run the guarantee, the runtime itself runs
``ensure_graduation_artifacts.py --stop-hook`` on every ``Stop``. This removes
the dependence on the agent choosing to act, which is what made recap-PDF
generation inconsistent.

This module validates the hook FILE contract:

1. Valid Kiro 1.0 ``v1`` wrapper — ``version: v1`` and a single hook entry with
   ``name`` / ``trigger`` / ``action``.
2. ``trigger == "Stop"`` (the enforcement trigger).
3. ``action.type == "command"`` (deterministic, not an agent prompt).
4. The command runs ``ensure_graduation_artifacts.py --stop-hook``.

The gating logic itself (defer while ``config/.question_pending`` exists, no-op
away from a track-end stopping point, otherwise ensure the artifacts) now lives
in tested Python — ``ensure_graduation_artifacts.is_stopping_point`` and the
``--stop-hook`` mode of its ``main`` — and is covered by the power-level suite
``senzing-bootcamp/tests/test_ensure_graduation_artifacts_stop_hook.py``.

**Validates: Requirements 2.1, 2.3, 2.6, 2.7, 6.4**
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    HOOKS_DIR,
    load_hook,
    load_hook_wrapper,
)

HOOK_ID = "enforce-critical-artifacts"
HOOK_FILE = HOOKS_DIR / f"{HOOK_ID}.json"

# The Kiro 1.0 trigger set (for validating the enforcement trigger).
_V1_TRIGGERS = {
    "PostFileSave", "PostFileCreate", "PostFileDelete", "Stop",
    "UserPromptSubmit", "PostTaskExec", "PreToolUse", "PostToolUse",
}


@pytest.fixture(scope="module")
def hook_data() -> dict:
    """Load and parse the enforce-critical-artifacts v1 hook entry."""
    assert HOOK_FILE.exists(), f"Hook file not found: {HOOK_FILE}"
    return load_hook(HOOK_FILE)


@pytest.fixture(scope="module")
def command(hook_data: dict) -> str:
    """Return the action.command text from the v1 command hook entry."""
    return hook_data["action"]["command"]


class TestEnforceCriticalArtifactsSchema:
    """Verify the hook is a well-formed Kiro ``v1`` command hook.

    **Validates: Requirements 2.6, 6.4**
    """

    def test_hook_file_exists(self) -> None:
        """The hook file exists on disk."""
        assert HOOK_FILE.exists(), f"Hook file not found at {HOOK_FILE}"

    def test_required_fields_present(self, hook_data: dict) -> None:
        """name, trigger, action, and (for a command action) action.command."""
        missing: list[str] = []
        if not hook_data.get("name"):
            missing.append("name")
        if not hook_data.get("trigger"):
            missing.append("trigger")
        action = hook_data.get("action")
        if not isinstance(action, dict):
            missing.append("action")
        elif action.get("type") == "command" and not action.get("command"):
            missing.append("action.command")
        assert not missing, f"Hook missing required fields: {missing}"

    def test_top_level_schema_fields(self, hook_data: dict) -> None:
        """The wrapper declares v1 and the entry carries name/trigger/action."""
        wrapper = load_hook_wrapper(HOOK_FILE)
        assert wrapper.get("version") == "v1", "wrapper must declare version v1"
        for field in ("name", "trigger", "action"):
            assert field in hook_data, f"Hook entry missing field '{field}'"

    def test_version_is_v1(self, hook_data: dict) -> None:
        """The wrapper declares the v1 schema version."""
        assert load_hook_wrapper(HOOK_FILE).get("version") == "v1"

    def test_trigger_is_stop(self, hook_data: dict) -> None:
        """trigger is the Stop enforcement trigger (1.0 rename of agentStop)."""
        trigger = hook_data["trigger"]
        assert trigger in _V1_TRIGGERS, f"Invalid trigger: {trigger}"
        assert trigger == "Stop", f'Expected trigger == "Stop", got "{trigger}"'

    def test_action_type_is_command(self, hook_data: dict) -> None:
        """action.type is command — a deterministic runtime hook, not an agent prompt.

        This is the crux of the guarantee: the runtime runs the ensure script
        itself, so the artifacts are produced whether or not the agent acts.
        """
        assert hook_data["action"]["type"] == "command", (
            f'Expected action.type == "command", got '
            f'"{hook_data["action"]["type"]}"'
        )

    def test_no_agent_prompt(self, hook_data: dict) -> None:
        """A command hook carries no agent prompt."""
        assert "prompt" not in hook_data["action"], (
            "A command hook must not carry an agent 'prompt'"
        )


class TestEnforceCriticalArtifactsCommand:
    """Verify the command runs the ensure orchestrator in --stop-hook mode.

    **Validates: Requirements 2.1, 2.3, 2.7**
    """

    def test_runs_ensure_orchestrator(self, command: str) -> None:
        """The command invokes ensure_graduation_artifacts.py."""
        assert "ensure_graduation_artifacts.py" in command, (
            "Command does not invoke ensure_graduation_artifacts.py"
        )

    def test_uses_stop_hook_mode(self, command: str) -> None:
        """The command runs the deterministic --stop-hook mode."""
        assert "--stop-hook" in command, (
            "Command does not run ensure_graduation_artifacts.py in --stop-hook mode"
        )

    def test_invokes_python(self, command: str) -> None:
        """The command runs the script through a Python interpreter."""
        assert "python3" in command or "python" in command, (
            "Command does not invoke the script via python/python3"
        )

    def test_degrades_gracefully_when_script_absent(self, command: str) -> None:
        """The command guards on the script's existence so a missing script no-ops.

        Mirrors the session-log-events command hook: an ``[ -f ... ]`` guard so a
        workspace without the bundled script degrades to a silent no-op rather
        than a raw 'No such file or directory' error.
        """
        script = "senzing-bootcamp/scripts/ensure_graduation_artifacts.py"
        assert "[ -f" in command and script in command, (
            "Command should guard on the script path existing before running it"
        )

    def test_declares_a_timeout(self, hook_data: dict) -> None:
        """The hook declares a timeout so a slow render cannot hang the stop."""
        timeout = hook_data.get("timeout")
        assert isinstance(timeout, int) and timeout > 0, (
            f"Command hook should declare a positive integer timeout, got {timeout!r}"
        )
