"""Bug-condition EXPLORATION tests for the missing-bundled-scripts bugfix (hooks).

These tests simulate the ``session-log-events`` postToolUse hook's ``runCommand``
invocation in a workspace where the bundled script it shells out to
(``senzing-bootcamp/scripts/log_write_event.py``) does NOT exist — the
``isBugCondition(X)`` domain (``NOT fileExists(X.scriptPath)``).

They encode the EXPECTED (fixed) behavior from design Property 1:

    FOR ALL X WHERE isBugCondition(X):
        result.exitCode == 0
        NOT result.emittedFileNotFoundError
        downstreamEffectPreserved(X)   # a {ts, action, module} event is still
                                       # appended to config/session_log.jsonl

**They are AUTHORED TO FAIL on the current (unfixed) code** — the IDE runs
``python3 senzing-bootcamp/scripts/log_write_event.py`` unconditionally, so an
absent script makes the interpreter exit 2 with
``can't open file '.../log_write_event.py': [Errno 2] No such file or directory``
and no session event is appended. That failure CONFIRMS the bug; it must NOT be
"fixed" here. After the fix (the hook guards with an existence check and routes
to a self-contained inline appender), these same tests will pass.

Feature: missing-bundled-scripts

**Validates: Requirements 2.1, 2.2** (the fixed behavior these encode)
Explores defect Requirements 1.1, 1.2.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — the REAL power hook file (read for its runCommand string). The bundled
# script path inside the command is resolved relative to each test's throwaway
# workspace cwd, where it deliberately does not exist.
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_HOOK_FILE: Path = (
    _PROJECT_ROOT / "senzing-bootcamp" / "hooks" / "session-log-events.kiro.hook"
)

_PROGRESS_PATH: str = "config/bootcamp_progress.json"
_SESSION_LOG_PATH: str = "config/session_log.jsonl"

_MIN_MODULE: int = 0
_MAX_MODULE: int = 11

# Substrings that indicate the interpreter could not open the bundled script —
# the file-not-found signature of the bug.
_FILE_NOT_FOUND_MARKERS: tuple[str, ...] = (
    "No such file or directory",
    "can't open file",
    "cannot find the file",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hook_command() -> str:
    """Return the ``then.command`` the session-log-events hook runs after a write.

    Returns:
        The raw command string from the real hook file (e.g.
        ``python3 senzing-bootcamp/scripts/log_write_event.py``).
    """
    hook = json.loads(_HOOK_FILE.read_text(encoding="utf-8"))
    return hook.get("then", {}).get("command", "")


def _make_workspace() -> Path:
    """Create a fresh throwaway workspace with a ``config/`` dir and NO scripts.

    The bundled ``senzing-bootcamp/scripts/`` directory is intentionally absent
    so that any hook/step shelling out to it hits the bug condition.

    Returns:
        Path to the new workspace root.
    """
    workspace = Path(tempfile.mkdtemp(prefix="missing_scripts_hook_"))
    (workspace / "config").mkdir(parents=True, exist_ok=True)
    return workspace


def _run_hook_command(workspace: Path) -> subprocess.CompletedProcess[str]:
    """Run the hook's runCommand exactly as the IDE would, in *workspace*.

    Args:
        workspace: The working directory to run the command in (its
            ``senzing-bootcamp/scripts/`` directory does not exist).

    Returns:
        The completed process with captured stdout/stderr and return code.
    """
    command = _hook_command()
    return subprocess.run(
        command,
        shell=True,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=30,
    )


def _emitted_file_not_found(result: subprocess.CompletedProcess[str]) -> bool:
    """Return True if the process emitted a file-not-found error.

    Args:
        result: A completed process from :func:`_run_hook_command`.

    Returns:
        True when stdout or stderr contains a file-not-found signature.
    """
    blob = f"{result.stdout}\n{result.stderr}"
    return any(marker in blob for marker in _FILE_NOT_FOUND_MARKERS)


def _read_log_entries(workspace: Path) -> list[dict]:
    """Parse all JSON entries appended to the session log in *workspace*.

    Args:
        workspace: The workspace whose ``config/session_log.jsonl`` to read.

    Returns:
        A list of parsed JSON objects (empty when the log file is absent).
    """
    log_file = workspace / _SESSION_LOG_PATH
    if not log_file.exists():
        return []
    entries: list[dict] = []
    for line in log_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _expected_module(spec: tuple[str, int | None]) -> int:
    """Compute the module a fixed inline logger should record for *spec*.

    Args:
        spec: A ``(kind, raw_module)`` progress-file specification.

    Returns:
        The clamped module number (0–11); 0 for any non-readable state.
    """
    kind, raw = spec
    if kind == "valid" and raw is not None:
        return max(_MIN_MODULE, min(_MAX_MODULE, raw))
    return _MIN_MODULE


def _materialize_progress(workspace: Path, spec: tuple[str, int | None]) -> None:
    """Write (or omit) ``config/bootcamp_progress.json`` per *spec* in *workspace*.

    Args:
        workspace: The workspace to write the progress file into.
        spec: A ``(kind, raw_module)`` specification describing the file state.
    """
    kind, raw = spec
    progress_file = workspace / _PROGRESS_PATH
    if kind == "absent":
        return
    if kind == "invalid":
        progress_file.write_text("{ this is not valid json", encoding="utf-8")
        return
    if kind == "no_module_key":
        progress_file.write_text(json.dumps({"language": "python"}), encoding="utf-8")
        return
    # kind == "valid"
    progress_file.write_text(json.dumps({"current_module": raw}), encoding="utf-8")


# ---------------------------------------------------------------------------
# Hypothesis strategies (bug-condition input domain)
# ---------------------------------------------------------------------------


@st.composite
def st_progress_spec(draw) -> tuple[str, int | None]:
    """Draw a progress-file state spanning valid, clamped, and missing cases.

    Generates ``current_module`` values across and beyond the 0–11 range (so
    clamping is exercised) plus the missing-file, invalid-JSON, and missing-key
    states the inline logger must default to module 0 for.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(kind, raw_module)`` tuple consumed by :func:`_materialize_progress`.
    """
    kind = draw(
        st.sampled_from(["valid", "valid", "absent", "invalid", "no_module_key"])
    )
    if kind == "valid":
        return ("valid", draw(st.integers(min_value=-5, max_value=20)))
    return (kind, None)


# ---------------------------------------------------------------------------
# Property 1 (bug condition → expected behavior) — PBT over progress states
# ---------------------------------------------------------------------------


class TestMissingSessionLoggerExploration:
    """Missing ``log_write_event.py`` must still append a session event.

    **Validates: Requirements 2.1, 2.2**

    For every progress-file state, simulating the ``session-log-events``
    runCommand in a workspace lacking ``senzing-bootcamp/scripts/`` must exit 0,
    emit no file-not-found error, and still append a ``{ts, action, module}``
    event to ``config/session_log.jsonl`` via the inline fallback.

    AUTHORED TO FAIL on unfixed code (exit 2, file-not-found, no append).
    """

    @given(spec=st_progress_spec())
    def test_missing_logger_appends_event_for_all_progress_states(
        self, spec: tuple[str, int | None]
    ) -> None:
        """For all progress states, the missing-logger invocation degrades gracefully."""
        workspace = _make_workspace()
        _materialize_progress(workspace, spec)

        result = _run_hook_command(workspace)

        assert result.returncode == 0, (
            "missing-logger invocation must exit 0 (graceful degradation), got "
            f"returncode={result.returncode}; stderr={result.stderr!r}"
        )
        assert not _emitted_file_not_found(result), (
            "missing-logger invocation must not emit a file-not-found error; "
            f"stderr={result.stderr!r}"
        )

        entries = _read_log_entries(workspace)
        assert len(entries) == 1, (
            "inline fallback must append exactly one session event to "
            f"{_SESSION_LOG_PATH}, got {len(entries)} entries"
        )
        entry = entries[0]
        assert entry.get("timestamp"), "session event must carry a timestamp (ts)"
        assert entry.get("event_type") == "action", (
            "session event must record a write 'action', got "
            f"event_type={entry.get('event_type')!r}"
        )
        assert entry.get("module") == _expected_module(spec), (
            "session event module must equal the clamped current_module "
            f"({_expected_module(spec)}), got {entry.get('module')!r}"
        )


# ---------------------------------------------------------------------------
# Example-based exploration (concrete counterexamples)
# ---------------------------------------------------------------------------


class TestMissingSessionLoggerExamples:
    """Concrete missing-logger cases that demonstrate the bug counterexamples.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_hook_command_targets_bundled_script(self) -> None:
        """Sanity: the hook shells out to the bundled log_write_event.py path."""
        command = _hook_command()
        assert "log_write_event.py" in command, (
            "session-log-events hook must invoke log_write_event.py, got "
            f"command={command!r}"
        )

    def test_missing_logger_with_module_5_appends_event(self) -> None:
        """A present progress file (module 5) still yields a module-5 event."""
        workspace = _make_workspace()
        _materialize_progress(workspace, ("valid", 5))

        result = _run_hook_command(workspace)

        assert result.returncode == 0, (
            f"expected exit 0, got {result.returncode}; stderr={result.stderr!r}"
        )
        assert not _emitted_file_not_found(result), (
            f"expected no file-not-found error; stderr={result.stderr!r}"
        )
        entries = _read_log_entries(workspace)
        assert len(entries) == 1 and entries[0].get("module") == 5, (
            f"expected one module-5 event, got {entries!r}"
        )

    def test_missing_logger_without_progress_file_defaults_module_zero(self) -> None:
        """With no progress file, the inline fallback records module 0."""
        workspace = _make_workspace()  # no progress file written

        result = _run_hook_command(workspace)

        assert result.returncode == 0, (
            f"expected exit 0, got {result.returncode}; stderr={result.stderr!r}"
        )
        assert not _emitted_file_not_found(result), (
            f"expected no file-not-found error; stderr={result.stderr!r}"
        )
        entries = _read_log_entries(workspace)
        assert len(entries) == 1 and entries[0].get("module") == 0, (
            f"expected one module-0 event, got {entries!r}"
        )
