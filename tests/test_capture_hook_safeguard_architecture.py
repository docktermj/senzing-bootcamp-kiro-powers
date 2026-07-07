"""Architecture-guardrail tests for the capture-hook-completion-safeguard feature.

These example-based (non-Hypothesis) structural tests assert the safeguard feature
preserves the deliberate no-per-write-cost architecture: the Module_Completion_Safeguard
is invoked by module-completion steering only, never by a hook and never via a per-write
interception. Concretely:

- No ``preToolUse`` write-tool hook references the safeguard script
  (``capture_hook_safeguard``) — the feature must not turn absence detection into a
  per-write interception (Requirement 3.3).
- The feature adds NO new write-tool hook referencing the safeguard — in fact, no
  ``*.kiro.hook`` file references ``capture_hook_safeguard`` at all, because the
  safeguard is steering-invoked, never a hook (Requirement 3.3).
- The three capture-critical hook files (``session-log-events``, ``module-recap-append``,
  ``ask-bootcamper``) exist and are unchanged by this feature — none references the
  safeguard (Requirement 3.3).

Per the project structure rule, tests validating real hook files on disk live in the
repo-root ``tests/`` directory (not ``senzing-bootcamp/tests/``).

**Validates: Requirements 3.3**
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths resolved relative to this file (repo-root ``tests/`` -> project root).
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_HOOKS_DIR: Path = _PROJECT_ROOT / "senzing-bootcamp" / "hooks"

# The safeguard entry point. A hook (any hook, but especially a preToolUse write
# hook) referencing this string would indicate the feature wired the safeguard
# into a hook / per-write interception — exactly what the design forbids.
_SAFEGUARD_MARKER: str = "capture_hook_safeguard"

# The three capture-critical hooks the feature must leave unchanged.
_CAPTURE_CRITICAL_HOOKS: tuple[str, ...] = (
    "session-log-events",
    "module-recap-append",
    "ask-bootcamper",
)


def _hook_files() -> list[Path]:
    """Return all ``*.kiro.hook`` files under the hooks directory.

    Returns:
        Sorted list of hook file paths.
    """
    return sorted(_HOOKS_DIR.glob("*.kiro.hook"))


def _load_hook(path: Path) -> dict:
    """Parse a ``.kiro.hook`` JSON file.

    Args:
        path: Path to the hook file.

    Returns:
        The parsed hook object.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _is_write_tool_hook(hook: dict) -> bool:
    """Return True if the hook targets tool-write events (pre/postToolUse write).

    A "write-tool hook" is one whose ``when`` block fires on ``write`` tool
    operations — i.e. ``when.type`` is a tool-use trigger and its ``toolTypes``
    include ``"write"``.

    Args:
        hook: Parsed hook object.

    Returns:
        True when the hook fires on write-tool events.
    """
    when = hook.get("when", {})
    when_type = when.get("type")
    tool_types = when.get("toolTypes", []) or []
    return when_type in {"preToolUse", "postToolUse"} and "write" in tool_types


def _is_pre_write_tool_hook(hook: dict) -> bool:
    """Return True if the hook is specifically a ``preToolUse`` write hook.

    Args:
        hook: Parsed hook object.

    Returns:
        True when ``when.type == "preToolUse"`` and ``"write"`` is targeted.
    """
    when = hook.get("when", {})
    return when.get("type") == "preToolUse" and "write" in (
        when.get("toolTypes", []) or []
    )


def _hook_id(path: Path) -> str:
    """Return the hook id (file name without the ``.kiro.hook`` suffix).

    Args:
        path: Path to the hook file.

    Returns:
        The hook id, e.g. ``session-log-events``.
    """
    return path.name[: -len(".kiro.hook")]


class TestNoPreToolUseWriteHookReferencesSafeguard:
    """No preToolUse write hook may invoke the safeguard (Requirement 3.3).

    **Validates: Requirements 3.3**
    """

    def test_hooks_directory_exists(self) -> None:
        """The real hooks directory must exist for the guardrail to be meaningful."""
        assert _HOOKS_DIR.is_dir(), f"Hooks directory not found: {_HOOKS_DIR}"

    def test_no_pre_write_tool_hook_references_safeguard(self) -> None:
        """No preToolUse write hook may reference the safeguard script (Req 3.3).

        Scan every ``*.kiro.hook`` file; for any hook whose ``when`` block targets
        ``preToolUse`` write-tool events, assert its raw content contains no
        reference to ``capture_hook_safeguard``. The safeguard must run only at the
        module-completion boundary via steering, never via a write-tool hook.
        """
        offenders: list[str] = []
        for path in _hook_files():
            raw = path.read_text(encoding="utf-8")
            hook = json.loads(raw)
            if _is_pre_write_tool_hook(hook) and _SAFEGUARD_MARKER in raw:
                offenders.append(path.name)

        assert not offenders, (
            "No preToolUse write-tool hook may reference the capture-hook "
            f"safeguard, but these do: {offenders}. The safeguard is invoked by "
            "module-completion steering only, never a per-write interception "
            "(Requirement 3.3)."
        )


class TestNoWriteToolHookAddedForSafeguard:
    """The feature adds no write-tool hook referencing the safeguard (Requirement 3.3).

    **Validates: Requirements 3.3**
    """

    def test_no_hook_file_references_safeguard(self) -> None:
        """No ``*.kiro.hook`` file may reference the safeguard at all (Req 3.3).

        The safeguard is steering-invoked, never a hook. Therefore the feature adds
        no new write-tool hook referencing it — and, more strongly, no hook file of
        any event type references ``capture_hook_safeguard``.
        """
        offenders: list[str] = []
        for path in _hook_files():
            raw = path.read_text(encoding="utf-8")
            if _SAFEGUARD_MARKER in raw:
                offenders.append(path.name)

        assert not offenders, (
            "No .kiro.hook file may reference the capture-hook safeguard, but "
            f"these do: {offenders}. The safeguard is invoked by steering only; the "
            "feature adds no new hook for it (Requirement 3.3)."
        )

    def test_no_write_tool_hook_references_safeguard(self) -> None:
        """No write-tool (pre/postToolUse) hook may reference the safeguard (Req 3.3).

        Narrower, explicit restatement of the design's core guarantee: the feature
        introduces no write-tool hook wired to the safeguard.
        """
        offenders: list[str] = []
        for path in _hook_files():
            raw = path.read_text(encoding="utf-8")
            hook = json.loads(raw)
            if _is_write_tool_hook(hook) and _SAFEGUARD_MARKER in raw:
                offenders.append(path.name)

        assert not offenders, (
            "No write-tool hook may reference the capture-hook safeguard, but "
            f"these do: {offenders} (Requirement 3.3)."
        )


class TestCaptureCriticalHooksUnchanged:
    """The three capture-critical hook files are unchanged by this feature (Req 3.3).

    **Validates: Requirements 3.3**
    """

    def test_capture_critical_hook_files_exist(self) -> None:
        """Each capture-critical hook file must still be present (Req 3.3)."""
        for hook_id in _CAPTURE_CRITICAL_HOOKS:
            path = _HOOKS_DIR / f"{hook_id}.kiro.hook"
            assert path.is_file(), (
                f"Capture-critical hook file not found: {path}. The feature must "
                "not remove any capture-critical hook (Requirement 3.3)."
            )

    def test_capture_critical_hooks_do_not_reference_safeguard(self) -> None:
        """No capture-critical hook may reference the safeguard (Req 3.3).

        The feature must not change the behavior of the capture-critical hooks
        themselves; in particular it must not modify them to invoke the safeguard.
        """
        offenders: list[str] = []
        for hook_id in _CAPTURE_CRITICAL_HOOKS:
            raw = (_HOOKS_DIR / f"{hook_id}.kiro.hook").read_text(encoding="utf-8")
            if _SAFEGUARD_MARKER in raw:
                offenders.append(hook_id)

        assert not offenders, (
            "The feature must not modify the capture-critical hooks to reference "
            f"the safeguard, but these do: {offenders} (Requirement 3.3)."
        )
