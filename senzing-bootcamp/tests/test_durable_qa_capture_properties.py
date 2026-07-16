"""Bug-condition PROPERTY tests for the durable-qa-capture fix (power).

This suite expresses the two bug-condition correctness properties from
``design.md`` as clean, general property-based tests against the FIXED code, so
both are expected to PASS:

- **Property 1 - Durable Write-Through Capture** (Requirements 2.1, 2.2): for
  any Q&A cadence sequence, the deterministic, command-backed capture hook
  (``senzing-bootcamp/hooks/capture-qa-events.json``) durably persists every
  ``question``/``answer`` event to ``config/session_log.jsonl`` at ask/answer
  time -- independent of any agent narration.
- **Property 2 - Loud Graduation Validation** (Requirements 2.3, 2.4): for any
  ``(modules_completed, session_log)`` state, the completeness validator
  (``senzing-bootcamp/scripts/validate_qa_capture.py``) halts (``report.ok`` is
  ``False``) and names exactly the completed modules that are genuine Q&A gaps,
  and passes (``report.ok`` is ``True``) when every completed module has real
  Q&A or an explicit "no substantive questions" marker.

These are distinct from the exploration tests (tasks 1-2), which are authored to
fail on the unfixed wiring. Here the focus is broad-domain property coverage of
the expected, fixed behavior.

Feature: durable-qa-capture

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Scripts import via sys.path (scripts aren't packages).
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_SCRIPTS_DIR: str = str(_POWER_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import session_logger  # noqa: E402  (path manipulated above)
import validate_qa_capture  # noqa: E402  (path manipulated above)

# The deterministic, command-backed capture hook the fix introduces.
_CAPTURE_HOOK: Path = _POWER_ROOT / "hooks" / "capture-qa-events.json"
_INSTALLED_SCRIPTS: Path = _POWER_ROOT / "scripts"

# Scripts the command hook depends on (copied into each throwaway workspace).
_REQUIRED_SCRIPTS: tuple[str, ...] = ("log_qa_event.py", "session_logger.py")

# Workspace-relative state files (matching the scripts' conventions).
_SESSION_LOG: str = "config/session_log.jsonl"
_PROGRESS: str = "config/bootcamp_progress.json"
_QUESTION_PENDING: str = "config/.question_pending"


# ---------------------------------------------------------------------------
# Property 1 harness: run the real command-backed capture hook
# ---------------------------------------------------------------------------


def _seed_scripts(workspace: Path) -> None:
    """Copy the capture scripts into ``workspace/senzing-bootcamp/scripts/``.

    The command-backed capture hook invokes
    ``senzing-bootcamp/scripts/log_qa_event.py`` relative to the workspace cwd,
    so the two scripts it needs are copied in (``log_qa_event.py`` imports
    ``session_logger`` from its own directory).

    Args:
        workspace: The workspace root to seed.
    """
    dest = workspace / "senzing-bootcamp" / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    for name in _REQUIRED_SCRIPTS:
        shutil.copy2(_INSTALLED_SCRIPTS / name, dest / name)


def _python_env(workspace: Path) -> dict[str, str]:
    """Return an environment whose ``python3`` resolves to this interpreter.

    The command hook literally invokes ``python3``. A workspace-local ``python3``
    shim pointing at :data:`sys.executable` is placed on ``PATH`` so the
    deterministic command is reproducible under any runner.

    Args:
        workspace: The workspace root (holds the shim ``.bin`` directory).

    Returns:
        A copy of the current environment with the shim directory on ``PATH``.
    """
    bindir = workspace / ".bin"
    bindir.mkdir(exist_ok=True)
    shim = bindir / "python3"
    if not shim.exists():
        try:
            shim.symlink_to(sys.executable)
        except OSError:
            shim.write_text(
                f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8"
            )
            shim.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    return env


@contextlib.contextmanager
def _capture_workspace():
    """Yield a throwaway workspace seeded for command-backed capture.

    Creates ``config/`` and copies the capture scripts into
    ``senzing-bootcamp/scripts/``. Removed on exit.

    Yields:
        The workspace root ``Path``.
    """
    root = Path(tempfile.mkdtemp(prefix="durable_qa_prop_"))
    (root / "config").mkdir(parents=True, exist_ok=True)
    _seed_scripts(root)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _set_current_module(workspace: Path, module: int) -> None:
    """Write a minimal ``config/bootcamp_progress.json`` with ``current_module``."""
    (workspace / _PROGRESS).write_text(
        json.dumps({"current_module": module, "modules_completed": []}),
        encoding="utf-8",
    )


def _present_question(workspace: Path, text: str, qtype: str = "reflection") -> None:
    """Present a question: write ``config/.question_pending`` (type + text).

    Models the Stop-boundary marker the runtime writes deterministically when a
    question is posed -- WITHOUT the agent voluntarily logging it.

    Args:
        workspace: The workspace root.
        text: The question text (stored on lines 2+).
        qtype: The question type (stored on line 1).
    """
    (workspace / _QUESTION_PENDING).write_text(f"{qtype}\n{text}", encoding="utf-8")


def _run_capture_hook(
    workspace: Path, trigger: str, stdin_text: str | None = None
) -> None:
    """Run the deterministic, command-backed capture hook for *trigger*.

    Models the runtime executing the ``type: command`` capture hook on the Q&A
    cadence, independent of any agent narration: it reads the real
    ``capture-qa-events.json``, finds the entries matching *trigger*, and runs
    each ``action.command`` exactly as the runtime would (in the workspace cwd,
    with an optional stdin payload for the answer).

    Args:
        workspace: The workspace to run the capture command in.
        trigger: The hook trigger to run (``"Stop"`` or ``"UserPromptSubmit"``).
        stdin_text: Optional stdin payload (the bootcamper's answer text).
    """
    data = json.loads(_CAPTURE_HOOK.read_text(encoding="utf-8"))
    env = _python_env(workspace)
    for entry in data.get("hooks", []):
        if entry.get("trigger") != trigger:
            continue
        action = entry.get("action", {})
        if action.get("type") != "command" or not action.get("command"):
            continue
        subprocess.run(
            ["bash", "-c", action["command"]],
            cwd=str(workspace),
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )


def _logged_texts(workspace: Path, event_type: str) -> list[str]:
    """Return the sorted ``data.text`` values for events of *event_type*.

    Args:
        workspace: The workspace root.
        event_type: The completion event type (``"question"`` or ``"answer"``).

    Returns:
        The sorted list of logged texts (empty when the log is absent).
    """
    log_path = workspace / _SESSION_LOG
    if not log_path.exists():
        return []
    texts: list[str] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("event_type") == event_type:
            texts.append(entry["data"]["text"])
    return sorted(texts)


# ---------------------------------------------------------------------------
# Property 2 harness: build the graduation completeness report
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _grad_workspace():
    """Yield a throwaway workspace with a ``config/`` directory. Removed on exit.

    Yields:
        The workspace root ``Path``.
    """
    root = Path(tempfile.mkdtemp(prefix="grad_qa_prop_"))
    (root / "config").mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _write_progress(workspace: Path, modules_completed: list[int]) -> None:
    """Write ``config/bootcamp_progress.json`` with the completed modules."""
    (workspace / _PROGRESS).write_text(
        json.dumps(
            {
                "current_module": (max(modules_completed) if modules_completed else 1),
                "modules_completed": sorted(modules_completed),
            }
        ),
        encoding="utf-8",
    )


def _write_real_qa(workspace: Path, module: int, question: str, answer: str) -> None:
    """Append a real, paired ``question``/``answer`` exchange for *module*.

    Uses the production event schema so the events are indistinguishable from
    those captured during a live session.

    Args:
        workspace: The workspace root.
        module: The module the exchange belongs to.
        question: The question text.
        answer: The answer text.
    """
    log_path = str(workspace / _SESSION_LOG)
    qid = session_logger.generate_question_id()
    session_logger.append_completion_entry(
        log_path,
        session_logger.build_completion_entry(
            "question", module, {"text": question, "question_id": qid}
        ),
    )
    session_logger.append_completion_entry(
        log_path,
        session_logger.build_completion_entry(
            "answer", module, {"text": answer, "question_id": qid}
        ),
    )


def _write_marker(workspace: Path, module: int) -> None:
    """Append an explicit "no substantive questions" marker for *module*.

    Args:
        workspace: The workspace root.
        module: The module to mark as legitimately question-free.
    """
    session_logger.append_completion_entry(
        str(workspace / _SESSION_LOG),
        session_logger.build_completion_entry(
            "action",
            module,
            {
                "action_type": "command_run",
                "description": (
                    f"Module {module} had {validate_qa_capture.NO_QUESTIONS_MARKER} "
                    "for the bootcamper this session."
                ),
            },
        ),
    )


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_SAFE_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 .,?!"
)


def st_qa_text() -> st.SearchStrategy[str]:
    """A single-line, PII-free, non-empty question/answer string.

    The alphabet excludes newlines and the value is stripped, so it survives the
    helper's ``.question_pending`` normalization (join of lines 2+, then strip)
    unchanged -- making round-trip text assertions exact.

    Returns:
        A Hypothesis strategy producing non-empty, whitespace-trimmed text.
    """
    return (
        st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=60)
        .map(str.strip)
        .filter(bool)
    )


@st.composite
def st_qa_cadence(draw) -> list[tuple[int, str, str]]:
    """Draw an arbitrary Q&A cadence sequence.

    Each element is a ``(module, question, answer)`` triple: a question is
    presented while ``current_module == module`` and an answer is submitted at
    the next cadence boundary. Kept short (1-3 exchanges) so the subprocess-
    driven capture stays fast.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty list of ``(module, question, answer)`` triples.
    """
    n = draw(st.integers(min_value=1, max_value=3))
    cadence: list[tuple[int, str, str]] = []
    for _ in range(n):
        module = draw(st.integers(min_value=1, max_value=11))
        question = draw(st_qa_text())
        answer = draw(st_qa_text())
        cadence.append((module, question, answer))
    return cadence


@st.composite
def st_graduation_state(draw) -> dict[int, str]:
    """Draw a graduation state mapping each completed module to a Q&A role.

    Each completed module is assigned one of three roles:

    - ``"real"``  -- has a real, paired ``question``/``answer`` exchange.
    - ``"gap"``   -- has no Q&A and no marker (a genuine capture gap).
    - ``"marker"`` -- carries an explicit "no substantive questions" marker.

    The mix is arbitrary (any combination of roles, including all-passing or
    all-gap states), so the property covers both the halt-and-name and the
    pass-clean branches.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty ``{module: role}`` mapping.
    """
    modules = draw(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=1,
            max_size=6,
            unique=True,
        )
    )
    roles: dict[int, str] = {}
    for module in modules:
        roles[module] = draw(st.sampled_from(("real", "gap", "marker")))
    return roles


# ---------------------------------------------------------------------------
# Property 1 - Durable Write-Through Capture
# ---------------------------------------------------------------------------


class TestDurableWriteThroughCaptureProperty:
    """The command-backed hook durably persists every Q&A cadence event.

    **Validates: Requirements 2.1, 2.2**

    For any generated Q&A cadence, each question is presented and each answer is
    submitted WITHOUT the agent voluntarily logging. The deterministic,
    command-backed capture hook must persist exactly one durable ``question``
    and one durable ``answer`` per exchange to ``config/session_log.jsonl``.
    """

    @given(cadence=st_qa_cadence())
    def test_every_cadence_event_is_durably_persisted(
        self, cadence: list[tuple[int, str, str]]
    ) -> None:
        with _capture_workspace() as workspace:
            for module, question, answer in cadence:
                _set_current_module(workspace, module)
                _present_question(workspace, question)
                _run_capture_hook(workspace, "Stop")  # record-question
                _run_capture_hook(
                    workspace, "UserPromptSubmit", stdin_text=answer
                )  # record-answer

            expected_questions = sorted(q for _, q, _ in cadence)
            expected_answers = sorted(a for _, _, a in cadence)

            assert _logged_texts(workspace, "question") == expected_questions, (
                "not every cadence question was durably persisted by the "
                "command-backed capture hook; "
                f"expected {expected_questions!r}, got "
                f"{_logged_texts(workspace, 'question')!r}"
            )
            assert _logged_texts(workspace, "answer") == expected_answers, (
                "not every cadence answer was durably persisted by the "
                "command-backed capture hook; "
                f"expected {expected_answers!r}, got "
                f"{_logged_texts(workspace, 'answer')!r}"
            )


# ---------------------------------------------------------------------------
# Property 2 - Loud Graduation Validation
# ---------------------------------------------------------------------------


class TestLoudGraduationValidationProperty:
    """Validation halts and names exactly the gap modules, else passes clean.

    **Validates: Requirements 2.3, 2.4**

    For any ``(modules_completed, session_log)`` state, the completeness
    validator flags exactly the completed modules that are genuine Q&A gaps
    (``report.ok`` is ``False`` and ``report.missing_modules`` equals the gap
    set), and passes cleanly (``report.ok`` is ``True``) when every completed
    module has real Q&A or a "no substantive questions" marker.
    """

    @given(state=st_graduation_state(), question=st_qa_text(), answer=st_qa_text())
    def test_validation_names_exactly_the_gap_modules(
        self, state: dict[int, str], question: str, answer: str
    ) -> None:
        with _grad_workspace() as workspace:
            _write_progress(workspace, list(state))
            for module, role in state.items():
                if role == "real":
                    _write_real_qa(workspace, module, question, answer)
                elif role == "marker":
                    _write_marker(workspace, module)
                # "gap": write nothing.

            expected_gaps = sorted(m for m, role in state.items() if role == "gap")

            report = validate_qa_capture.build_report(
                str(workspace / _PROGRESS), str(workspace / _SESSION_LOG)
            )

            assert sorted(report.missing_modules) == expected_gaps, (
                "validator did not name exactly the gap modules; "
                f"expected {expected_gaps!r}, got {sorted(report.missing_modules)!r}"
            )
            assert report.ok is (not expected_gaps), (
                "report.ok must be False iff there is at least one gap module; "
                f"gaps={expected_gaps!r}, ok={report.ok!r}"
            )

            # The CLI surfaces the same verdict: exit 1 on any gap, else 0.
            exit_code = validate_qa_capture.main(
                [
                    "--progress",
                    str(workspace / _PROGRESS),
                    "--log",
                    str(workspace / _SESSION_LOG),
                    "--check",
                ]
            )
            assert exit_code == (1 if expected_gaps else 0), (
                "CLI exit code disagreed with the report verdict; "
                f"gaps={expected_gaps!r}, exit_code={exit_code}"
            )
