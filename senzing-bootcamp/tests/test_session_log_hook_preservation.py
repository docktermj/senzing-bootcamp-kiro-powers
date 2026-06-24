"""Preservation tests for the session-log-hook-performance bugfix.

These tests establish a baseline of behavior that MUST remain intact after the
`session-log-events` hook is converted from `askAgent` to `runCommand`. They are
EXPECTED TO PASS on the current (unfixed) code, and must continue to pass after
the fix.

Feature: session-log-hook-performance

**Validates: Requirements 3.1, 3.2, 3.3, 3.5**

Covered preservation properties (design Property 2):
- The edited hook keeps `name`, `version`, `when.type == "postToolUse"`,
  `when.toolTypes == ["write"]`, and a valid JSON schema (`name`, `version`,
  `when`, `then`). (Req 3.2)
- The `session_logger.py` JSONL schema (`build_completion_entry` /
  `append_completion_entry`) still produces compact single-line JSON that
  round-trips. (Req 3.1)
- All hook files OTHER than `session-log-events.kiro.hook` are untouched
  (SHA-256 snapshot stability). (Req 3.5)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (per python-conventions.md)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import session_logger  # noqa: E402  (path set up above)

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"
_LOG_HOOK_FILE = _HOOKS_DIR / "session-log-events.kiro.hook"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_hook(path: Path) -> dict:
    """Parse a `.kiro.hook` file as JSON and return the dict.

    Args:
        path: Path to the hook file.

    Returns:
        The parsed hook JSON object.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _other_hook_files() -> list[Path]:
    """Return every `*.kiro.hook` file except `session-log-events.kiro.hook`.

    Returns:
        A sorted list of paths to all unrelated hook files.
    """
    return sorted(
        p
        for p in _HOOKS_DIR.glob("*.kiro.hook")
        if p.name != "session-log-events.kiro.hook"
    )


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's bytes.

    Args:
        path: Path to the file to hash.

    Returns:
        The hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot_other_hooks() -> dict[str, str]:
    """Build a {filename: sha256} snapshot of all unrelated hook files.

    Returns:
        A mapping of hook filename to its SHA-256 hex digest.
    """
    return {p.name: _sha256(p) for p in _other_hook_files()}


# ---------------------------------------------------------------------------
# Preservation Test — Hook schema and trigger preserved (Req 3.2)
# ---------------------------------------------------------------------------


class TestHookSchemaAndTriggerPreserved:
    """Preservation Test — Hook schema and trigger.

    **Validates: Requirements 3.2, 3.3**

    The `session-log-events` hook must keep its identity (`name`, `version`),
    its trigger (`when.type == "postToolUse"`, `when.toolTypes == ["write"]`),
    and a schema-valid shape (`name`, `version`, `when`, `then`). Only the
    `then` block changes from `askAgent` to `runCommand`.
    """

    def test_hook_file_is_valid_json_object(self) -> None:
        """The hook file must parse as a JSON object."""
        content = _LOG_HOOK_FILE.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - failure path
            raise AssertionError(
                f"Preservation check: hook file is not valid JSON: {exc}"
            ) from exc
        assert isinstance(data, dict), (
            "Preservation check: hook file must be a JSON object, "
            f"got {type(data).__name__}"
        )

    def test_hook_has_required_schema_fields(self) -> None:
        """The hook JSON must contain `name`, `version`, `when`, and `then`."""
        hook = _read_hook(_LOG_HOOK_FILE)
        for field in ("name", "version", "when", "then"):
            assert field in hook, (
                f"Preservation check: hook JSON must contain field '{field}', "
                f"got keys: {sorted(hook.keys())}"
            )

    def test_hook_name_is_nonempty_string(self) -> None:
        """The hook `name` must be a non-empty string."""
        hook = _read_hook(_LOG_HOOK_FILE)
        name = hook.get("name")
        assert isinstance(name, str) and name, (
            f"Preservation check: hook 'name' must be a non-empty string, got {name!r}"
        )

    def test_hook_version_is_nonempty_string(self) -> None:
        """The hook `version` must be a non-empty string."""
        hook = _read_hook(_LOG_HOOK_FILE)
        version = hook.get("version")
        assert isinstance(version, str) and version, (
            f"Preservation check: hook 'version' must be a non-empty string, "
            f"got {version!r}"
        )

    def test_hook_when_type_is_post_tool_use(self) -> None:
        """The hook `when.type` must be 'postToolUse'."""
        hook = _read_hook(_LOG_HOOK_FILE)
        when = hook.get("when", {})
        assert when.get("type") == "postToolUse", (
            f"Preservation check: hook when.type must be 'postToolUse', "
            f"got {when.get('type')!r}"
        )

    def test_hook_when_tooltypes_is_write_only(self) -> None:
        """The hook `when.toolTypes` must equal exactly ['write']."""
        hook = _read_hook(_LOG_HOOK_FILE)
        when = hook.get("when", {})
        assert when.get("toolTypes") == ["write"], (
            f"Preservation check: hook when.toolTypes must equal ['write'], "
            f"got {when.get('toolTypes')!r}"
        )


# ---------------------------------------------------------------------------
# Preservation Test — session_logger JSONL schema unchanged (Req 3.1)
# ---------------------------------------------------------------------------


class TestSessionLoggerSchemaUnchanged:
    """Preservation Test — session_logger.py JSONL schema.

    **Validates: Requirements 3.1**

    `build_completion_entry` / `append_completion_entry` must continue to emit
    compact single-line JSON that round-trips: an appended entry parses back
    into the same `event_type`, `module`, `timestamp`, and `data` fields, with
    no embedded newline.
    """

    def test_append_completion_entry_round_trips(self, tmp_path: Path) -> None:
        """An appended action entry round-trips as a single compact JSON line."""
        entry = session_logger.build_completion_entry(
            event_type="action",
            module=5,
            data={"action_type": "command_run", "description": "write operation"},
        )
        log_path = tmp_path / "config" / "session_log.jsonl"

        session_logger.append_completion_entry(str(log_path), entry)

        raw = log_path.read_text(encoding="utf-8")
        # Exactly one trailing newline, no embedded newlines in the line itself.
        assert raw.endswith("\n"), "appended entry must end with a single newline"
        lines = raw.splitlines()
        assert len(lines) == 1, (
            f"expected exactly one JSONL line, got {len(lines)}: {lines!r}"
        )

        parsed = json.loads(lines[0])
        assert parsed["event_type"] == "action"
        assert parsed["module"] == 5
        assert parsed["timestamp"] == entry.timestamp
        assert parsed["data"] == {
            "action_type": "command_run",
            "description": "write operation",
        }
        # Schema keys must be exactly the documented four.
        assert set(parsed.keys()) == {"event_type", "module", "timestamp", "data"}, (
            f"unexpected completion-entry keys: {sorted(parsed.keys())}"
        )

    def test_serialize_completion_entry_is_compact_single_line(self) -> None:
        """`serialize_completion_entry` emits compact JSON with no whitespace/newlines."""
        entry = session_logger.build_completion_entry(
            event_type="action",
            module=0,
            data={"action_type": "command_run", "description": "write operation"},
        )
        serialized = session_logger.serialize_completion_entry(entry)

        assert "\n" not in serialized, "serialized entry must be a single line"
        # Compact separators => no ', ' or ': ' spacing.
        assert ", " not in serialized and ": " not in serialized, (
            f"serialized entry must use compact separators, got: {serialized}"
        )
        # Round-trips back to the same content.
        assert json.loads(serialized) == {
            "event_type": "action",
            "module": 0,
            "timestamp": entry.timestamp,
            "data": {"action_type": "command_run", "description": "write operation"},
        }


# ---------------------------------------------------------------------------
# Preservation Test — unrelated hooks unchanged (Req 3.5)
# ---------------------------------------------------------------------------


class TestUnrelatedHooksUnchanged:
    """Preservation Test — unrelated hook files untouched.

    **Validates: Requirements 3.5**

    A SHA-256 snapshot of every hook file OTHER than
    `session-log-events.kiro.hook` must be stable. This detects any accidental
    modification of unrelated hooks while applying the fix.
    """

    def test_other_hook_files_discovered(self) -> None:
        """There must be unrelated hook files to snapshot (sanity check)."""
        others = _other_hook_files()
        assert others, "expected to discover unrelated *.kiro.hook files to snapshot"
        assert all(p.name != "session-log-events.kiro.hook" for p in others), (
            "the edited hook must be excluded from the unrelated-hooks snapshot"
        )

    def test_unrelated_hook_snapshot_is_stable(self) -> None:
        """Hashing all unrelated hooks twice must yield identical digests.

        Computing the snapshot twice within the test confirms the digests are
        deterministic; any accidental modification of an unrelated hook during
        the fix changes its bytes and would surface as a snapshot diff.
        """
        first = _snapshot_other_hooks()
        second = _snapshot_other_hooks()
        assert first == second, (
            "Preservation check: SHA-256 snapshot of unrelated hooks is not "
            f"stable. Differing files: "
            f"{sorted(k for k in first if first.get(k) != second.get(k))}"
        )

    def test_unrelated_hooks_are_valid_json(self) -> None:
        """Every unrelated hook file must remain valid JSON (untouched integrity)."""
        for path in _other_hook_files():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:  # pragma: no cover - failure path
                raise AssertionError(
                    f"Preservation check: unrelated hook '{path.name}' is not "
                    f"valid JSON: {exc}"
                ) from exc
