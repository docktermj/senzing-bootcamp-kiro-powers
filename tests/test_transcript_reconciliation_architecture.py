"""Architecture-guardrail tests for the transcript-reconciliation feature.

These example-based (non-Hypothesis) structural tests assert the
transcript-reconciliation feature preserves the deliberate no-per-write-cost
architecture and wires the reconciliation pass into the graduation flow:

- The feature adds NO new ``postToolUse`` write-tool hook that references
  transcript reconciliation (Requirement 2.2).
- The feature does NOT modify the ``session-log-events`` hook to call
  reconciliation — i.e. that hook contains no reference to
  ``reconcile_transcript`` (Requirements 2.2, 2.3).
- ``graduation.md`` Step 0b.4 invokes ``reconcile_transcript.py`` immediately
  BEFORE ``generate_transcript.py`` (Requirement 3.1).

Per the project structure rule, hook tests validating real hook files live in
the repo-root ``tests/`` directory (not ``senzing-bootcamp/tests/``).

**Validates: Requirements 2.2, 2.3, 3.1**
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths resolved relative to this file (repo-root ``tests/`` -> project root).
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_HOOKS_DIR: Path = _PROJECT_ROOT / "senzing-bootcamp" / "hooks"
_SESSION_LOG_HOOK: Path = _HOOKS_DIR / "session-log-events.kiro.hook"
_GRADUATION_DOC: Path = _PROJECT_ROOT / "senzing-bootcamp" / "steering" / "graduation.md"

# The feature's reconciliation entry point. A write-tool hook or the
# session-log-events hook referencing this string would indicate the feature
# introduced per-write reconciliation — exactly what the design forbids.
_RECONCILE_MARKER: str = "reconcile_transcript"


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
    operations — i.e. ``when.type`` is a tool-use trigger and its
    ``toolTypes`` include ``"write"``.

    Args:
        hook: Parsed hook object.

    Returns:
        True when the hook fires on write-tool events.
    """
    when = hook.get("when", {})
    when_type = when.get("type")
    tool_types = when.get("toolTypes", []) or []
    return when_type in {"preToolUse", "postToolUse"} and "write" in tool_types


def _is_post_write_tool_hook(hook: dict) -> bool:
    """Return True if the hook is specifically a ``postToolUse`` write hook.

    Args:
        hook: Parsed hook object.

    Returns:
        True when ``when.type == "postToolUse"`` and ``"write"`` is targeted.
    """
    when = hook.get("when", {})
    return when.get("type") == "postToolUse" and "write" in (
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


class TestNoNewWriteToolReconciliationHook:
    """The feature must add no write-tool hook invoking reconciliation.

    **Validates: Requirements 2.2, 2.3**
    """

    def test_hooks_directory_exists(self) -> None:
        """The real hooks directory must exist for the guardrail to be meaningful."""
        assert _HOOKS_DIR.is_dir(), f"Hooks directory not found: {_HOOKS_DIR}"

    def test_no_write_tool_hook_references_reconciliation(self) -> None:
        """No pre/postToolUse write hook may reference transcript reconciliation.

        Scan every ``*.kiro.hook`` file; for any hook whose ``when`` block
        targets write-tool events, assert its raw content contains no reference
        to ``reconcile_transcript`` / transcript reconciliation. The feature
        must run reconciliation only at graduation / stopping points, never via
        a write-tool hook (Requirements 2.2, 2.3).
        """
        offenders: list[str] = []
        for path in _hook_files():
            raw = path.read_text(encoding="utf-8")
            hook = json.loads(raw)
            if _is_write_tool_hook(hook) and (
                _RECONCILE_MARKER in raw
                or "transcript reconciliation" in raw.lower()
            ):
                offenders.append(path.name)

        assert not offenders, (
            "No write-tool hook may invoke transcript reconciliation, but "
            f"these do: {offenders}. Reconciliation must run only at "
            "graduation / stopping points (Requirements 2.2, 2.3)."
        )

    def test_only_expected_post_write_hook_exists(self) -> None:
        """The only ``postToolUse`` write hook is the pre-existing session logger.

        The feature must introduce NO new ``postToolUse`` write-tool hook. The
        sole such hook in the repo is ``session-log-events`` (part of the
        established architecture), so the set of postToolUse write hooks must
        not grow beyond it.
        """
        post_write_hooks = {
            _hook_id(path)
            for path in _hook_files()
            if _is_post_write_tool_hook(_load_hook(path))
        }
        assert post_write_hooks == {"session-log-events"}, (
            "The feature must add no new postToolUse write-tool hook. Expected "
            "exactly {'session-log-events'} but found "
            f"{post_write_hooks}."
        )


class TestSessionLogEventsHookUnmodified:
    """The ``session-log-events`` hook must not be changed to call reconciliation.

    **Validates: Requirements 2.2, 2.3**
    """

    def test_session_log_hook_exists(self) -> None:
        """The session-log-events hook file must be present."""
        assert _SESSION_LOG_HOOK.is_file(), (
            f"session-log-events hook not found: {_SESSION_LOG_HOOK}"
        )

    def test_session_log_hook_is_still_a_post_write_logger(self) -> None:
        """The hook must remain a postToolUse write logger (its original shape)."""
        hook = _load_hook(_SESSION_LOG_HOOK)
        assert _is_post_write_tool_hook(hook), (
            "session-log-events must remain a postToolUse write-tool hook"
        )
        # It logs; it must not have been repurposed into a reconciliation trigger.
        assert hook.get("then", {}).get("type") == "runCommand", (
            "session-log-events must remain a runCommand logging hook"
        )

    def test_session_log_hook_does_not_reference_reconciliation(self) -> None:
        """The hook content must contain no reference to transcript reconciliation.

        The feature must not modify ``session-log-events`` to invoke the
        reconciliation pass (that would reintroduce per-write cost, violating
        Requirements 2.2 and 2.3).
        """
        raw = _SESSION_LOG_HOOK.read_text(encoding="utf-8")
        assert _RECONCILE_MARKER not in raw, (
            "session-log-events hook must not reference "
            f"'{_RECONCILE_MARKER}'. The feature must not modify it to call "
            "reconciliation (Requirements 2.2, 2.3)."
        )
        assert "transcript reconciliation" not in raw.lower(), (
            "session-log-events hook must not reference transcript "
            "reconciliation"
        )


class TestGraduationStep0b4Ordering:
    """Step 0b.4 must invoke reconcile immediately before generate_transcript.

    **Validates: Requirements 3.1**
    """

    _RECONCILE_CMD = "python scripts/reconcile_transcript.py"
    _GENERATE_CMD = "python scripts/generate_transcript.py"

    def _step_0b4_text(self) -> str:
        """Extract the Step 0b.4 section text from graduation.md.

        Returns:
            The text from the Step 0b.4 heading up to the next ``### Step``
            heading (exclusive).
        """
        content = _GRADUATION_DOC.read_text(encoding="utf-8")
        start = content.find("### Step 0b.4")
        assert start >= 0, "graduation.md must contain a '### Step 0b.4' section"
        # Find the next '### Step' heading after the 0b.4 heading.
        next_heading = content.find("### Step", start + len("### Step 0b.4"))
        end = next_heading if next_heading >= 0 else len(content)
        return content[start:end]

    def test_graduation_doc_exists(self) -> None:
        """The graduation steering document must exist."""
        assert _GRADUATION_DOC.is_file(), (
            f"graduation.md not found: {_GRADUATION_DOC}"
        )

    def test_step_0b4_invokes_reconcile_transcript(self) -> None:
        """Step 0b.4 must invoke the reconcile script (Req 3.1)."""
        section = self._step_0b4_text()
        assert self._RECONCILE_CMD in section, (
            f"Step 0b.4 must invoke '{self._RECONCILE_CMD}'"
        )

    def test_step_0b4_invokes_generate_transcript(self) -> None:
        """Step 0b.4 must invoke the transcript renderer (Req 3.1)."""
        section = self._step_0b4_text()
        assert self._GENERATE_CMD in section, (
            f"Step 0b.4 must invoke '{self._GENERATE_CMD}'"
        )

    def test_reconcile_runs_before_generate_transcript(self) -> None:
        """Reconcile must appear BEFORE generate_transcript within Step 0b.4 (Req 3.1).

        Parse the Step 0b.4 section and assert the index of the reconcile
        command line is strictly less than the index of the generate_transcript
        command line — the immediately-before ordering the design requires.
        """
        section = self._step_0b4_text()
        reconcile_idx = section.find(self._RECONCILE_CMD)
        generate_idx = section.find(self._GENERATE_CMD)
        assert reconcile_idx >= 0 and generate_idx >= 0, (
            "Both reconcile and generate_transcript commands must appear in "
            "Step 0b.4"
        )
        assert reconcile_idx < generate_idx, (
            "Step 0b.4 must invoke reconcile_transcript.py BEFORE "
            "generate_transcript.py (Requirement 3.1); found reconcile at "
            f"index {reconcile_idx} and generate at {generate_idx}."
        )
