"""Preservation property tests for the missing-bundled-scripts bugfix (hooks).

These tests capture the baseline behavior of the ``session-log-events`` hook's
``runCommand`` invocation when the bundled script it shells out to
(``senzing-bootcamp/scripts/log_write_event.py``) IS present — the
``NOT isBugCondition(X)`` domain (``fileExists(X.scriptPath)``). They follow the
observation-first methodology: each present-script invocation is run against the
CURRENT (unfixed) code and the actual outputs are asserted, establishing the
behavior the fix must preserve.

They encode design Property 2 (Preservation):

    FOR ALL X WHERE NOT isBugCondition(X):
        F(X) = F'(X)

Covered preservation property (from design Preservation Requirements):
- Bundled logger preservation (Req 3.1): with ``log_write_event.py`` present, the
  ``session-log-events`` hook invokes the bundled script, which records the write
  event (timestamp + current module read from ``config/bootcamp_progress.json``,
  clamped 0–11) to ``config/session_log.jsonl`` and exits 0.

**These tests are EXPECTED TO PASS on the current (unfixed) code** (the script is
present, so the bug condition does not hold) and must continue to pass after the
fix.

Feature: missing-bundled-scripts

**Validates: Requirements 3.1**
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — the REAL power hook file (read for its runCommand string) and the
# installed bundled scripts (copied into each throwaway workspace so the
# referenced script is PRESENT — the non-bug-condition case).
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_HOOK_FILE: Path = (
    _PROJECT_ROOT / "senzing-bootcamp" / "hooks" / "session-log-events.kiro.hook"
)
_INSTALLED_SCRIPTS: Path = _PROJECT_ROOT / "senzing-bootcamp" / "scripts"

_WORKSPACE_SCRIPTS: str = "senzing-bootcamp/scripts"
_PROGRESS_PATH: str = "config/bootcamp_progress.json"
_SESSION_LOG_PATH: str = "config/session_log.jsonl"

# The bundled logger plus its sibling import; both must be present for the
# present-script (non-bug-condition) baseline.
_LOGGER_SCRIPTS: tuple[str, ...] = ("log_write_event.py", "session_logger.py")

_MIN_MODULE: int = 0
_MAX_MODULE: int = 11

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
    """Create a throwaway workspace with the bundled logger scripts PRESENT.

    Copies ``log_write_event.py`` and its ``session_logger.py`` sibling into the
    workspace's ``senzing-bootcamp/scripts/`` so the hook's runCommand resolves
    the bundled script (the non-bug-condition case).

    Returns:
        Path to the new workspace root.
    """
    workspace = Path(tempfile.mkdtemp(prefix="present_scripts_hook_"))
    (workspace / "config").mkdir(parents=True, exist_ok=True)
    dest_dir = workspace / _WORKSPACE_SCRIPTS
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in _LOGGER_SCRIPTS:
        shutil.copy2(_INSTALLED_SCRIPTS / name, dest_dir / name)
    return workspace


def _run_hook_command(workspace: Path) -> subprocess.CompletedProcess[str]:
    """Run the hook's runCommand exactly as the IDE would, in *workspace*.

    Args:
        workspace: The working directory to run the command in (its bundled
            ``senzing-bootcamp/scripts/log_write_event.py`` is present).

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
    """Compute the module the bundled logger records for *spec*.

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
# Hypothesis strategies (present-script input domain)
# ---------------------------------------------------------------------------


@st.composite
def st_progress_spec(draw) -> tuple[str, int | None]:
    """Draw a progress-file state spanning valid, clamped, and missing cases.

    Generates ``current_module`` values across and beyond the 0–11 range (so
    clamping is exercised) plus the missing-file, invalid-JSON, and missing-key
    states the bundled logger defaults to module 0 for.

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
# Preservation — present bundled logger records the write event (Req 3.1)
# ---------------------------------------------------------------------------


class TestBundledLoggerPreservation:
    """Preservation — present ``log_write_event.py`` records the write event.

    **Validates: Requirements 3.1**

    For every progress-file state, running the ``session-log-events`` runCommand
    in a workspace where the bundled script is PRESENT exits 0, emits no
    file-not-found error, and appends exactly one ``{timestamp, event_type,
    module, data}`` event to ``config/session_log.jsonl`` with the module equal
    to the clamped ``current_module``. This is the baseline behavior the fix must
    preserve.
    """

    @given(spec=st_progress_spec())
    def test_present_logger_records_event_for_all_progress_states(
        self, spec: tuple[str, int | None]
    ) -> None:
        """For all progress states, the present bundled logger records one event."""
        workspace = _make_workspace()
        _materialize_progress(workspace, spec)

        result = _run_hook_command(workspace)

        assert result.returncode == 0, (
            "present-logger invocation must exit 0, got "
            f"returncode={result.returncode}; stderr={result.stderr!r}"
        )
        assert not _emitted_file_not_found(result), (
            "present-logger invocation must not emit a file-not-found error; "
            f"stderr={result.stderr!r}"
        )

        entries = _read_log_entries(workspace)
        assert len(entries) == 1, (
            "the bundled logger must append exactly one session event to "
            f"{_SESSION_LOG_PATH}, got {len(entries)} entries"
        )
        entry = entries[0]
        assert entry.get("timestamp"), "session event must carry a timestamp"
        assert entry.get("event_type") == "action", (
            "session event must record a write 'action', got "
            f"event_type={entry.get('event_type')!r}"
        )
        assert entry.get("module") == _expected_module(spec), (
            "session event module must equal the clamped current_module "
            f"({_expected_module(spec)}), got {entry.get('module')!r}"
        )


# ---------------------------------------------------------------------------
# Example-based preservation (concrete baselines)
# ---------------------------------------------------------------------------


class TestBundledLoggerPreservationExamples:
    """Concrete present-logger baselines that the fix must preserve.

    **Validates: Requirements 3.1**
    """

    def test_hook_command_targets_bundled_script(self) -> None:
        """Sanity: the hook shells out to the bundled log_write_event.py path."""
        command = _hook_command()
        assert "log_write_event.py" in command, (
            "session-log-events hook must invoke log_write_event.py, got "
            f"command={command!r}"
        )

    def test_present_logger_with_module_5_records_module_5(self) -> None:
        """A present progress file (module 5) yields one module-5 event."""
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

    def test_present_logger_clamps_out_of_range_module(self) -> None:
        """An out-of-range current_module (99) is clamped to 11 by the bundled logger."""
        workspace = _make_workspace()
        _materialize_progress(workspace, ("valid", 99))

        result = _run_hook_command(workspace)

        assert result.returncode == 0, (
            f"expected exit 0, got {result.returncode}; stderr={result.stderr!r}"
        )
        entries = _read_log_entries(workspace)
        assert len(entries) == 1 and entries[0].get("module") == _MAX_MODULE, (
            f"expected one module-{_MAX_MODULE} (clamped) event, got {entries!r}"
        )

    def test_present_logger_without_progress_file_defaults_module_zero(self) -> None:
        """With no progress file, the bundled logger records module 0."""
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
