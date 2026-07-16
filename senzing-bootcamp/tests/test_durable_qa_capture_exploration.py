"""Bug-condition EXPLORATION tests for the durable-qa-capture bugfix (power).

These tests exercise the Q&A cadence (a question is presented at the Stop
boundary, an answer is submitted at the next ``UserPromptSubmit``) in the case
the design's ``isBugCondition`` describes:

    isBugCondition(input) ==
        input.isQACadenceEvent
        AND NOT persistedDeterministically(input)   # capture rode on an
                                                     # agent-voluntary hook
        AND eventMissingFrom("config/session_log.jsonl", input)

Today capture is *agent-voluntary*: the two Q&A hooks (``ask-bootcamper`` ->
``record-question``, ``review-bootcamper-input`` -> ``record-answer``) are
``type: agent`` hooks whose ``action.prompt`` merely *asks* the agent to run
``log_qa_event.py``. When the agent skips that instruction, or a session
boundary / context compaction / restart intervenes, the event is never written.

These tests deliberately DO NOT call ``log_qa_event.py`` on behalf of the agent.
Instead they model the *fixed* durability guarantee: a deterministic,
command-backed capture hook (``senzing-bootcamp/hooks/capture-qa-events.json``,
modeled on ``session-log-events.json``) that the runtime executes on the Q&A
cadence regardless of any agent narration. ``_run_durable_capture`` discovers
that command hook and runs its command exactly as the runtime would. When no
such command hook is wired (the current, unfixed state), nothing runs and the
Q&A events never reach ``config/session_log.jsonl``.

They encode the EXPECTED (fixed) behavior from design Property 1 (Durable
Write-Through Capture): every Q&A cadence event is durably persisted to
``config/session_log.jsonl`` at ask/answer time, independent of the agent.

**They are AUTHORED TO FAIL on the current (unfixed) code** — there is no
``capture-qa-events.json`` command hook, so ``_run_durable_capture`` runs
nothing and the log stays empty. Those failures CONFIRM the bug (capture rode on
the agent-voluntary hook); they must NOT be "fixed" here. After the fix lands
(task 6.1 adds the command-backed hook), these same tests will pass.

Feature: durable-qa-capture

**Validates: Requirements 2.1, 2.2** (the fixed durable-capture behavior these
encode). Explores defect Requirements 1.1, 1.2.
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
# Paths to the REAL installed power. The throwaway workspace gets its own copy
# of the two capture scripts under ``senzing-bootcamp/scripts/`` so the command
# hook's workspace-relative command resolves.
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_INSTALLED_SCRIPTS: Path = _POWER_ROOT / "scripts"
_CAPTURE_HOOK: Path = _POWER_ROOT / "hooks" / "capture-qa-events.json"

# Scripts the command hook depends on (copied into each workspace).
_REQUIRED_SCRIPTS: tuple[str, ...] = ("log_qa_event.py", "session_logger.py")

# Workspace-relative state files (matching the helper's constants).
_SESSION_LOG: str = "config/session_log.jsonl"
_PROGRESS: str = "config/bootcamp_progress.json"
_QUESTION_PENDING: str = "config/.question_pending"

# The concrete reported case: Modules 1-3 completed, each with a Q&A exchange
# that the agent never voluntarily logged.
_MODULES_1_TO_3_FIXTURE: tuple[tuple[int, str, str], ...] = (
    (1, "What business problem are you solving?", "Deduplicating our customer list"),
    (2, "Which Senzing license will you use?", "The free trial license to start"),
    (3, "What did the first entity graph reveal?", "Two records resolved to one person"),
)


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------


def _seed_scripts(workspace: Path) -> None:
    """Copy the capture scripts into ``workspace/senzing-bootcamp/scripts/``.

    The command-backed capture hook invokes
    ``senzing-bootcamp/scripts/log_qa_event.py`` relative to the workspace cwd,
    so the two scripts it needs are copied in. ``log_qa_event.py`` imports
    ``session_logger`` from its own directory, hence both are copied together.

    Args:
        workspace: The workspace root to seed.
    """
    dest = workspace / "senzing-bootcamp" / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    for name in _REQUIRED_SCRIPTS:
        shutil.copy2(_INSTALLED_SCRIPTS / name, dest / name)


def _python_env(workspace: Path) -> dict[str, str]:
    """Return an environment whose ``python3`` resolves to this interpreter.

    The command hook literally invokes ``python3``. To make the deterministic
    command reproducible under any runner, a ``python3`` shim pointing at
    :data:`sys.executable` is placed on a workspace-local ``.bin`` directory and
    prepended to ``PATH``.

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
def _workspace(current_module: int = 1):
    """Yield a throwaway workspace seeded with scripts and a progress file.

    Creates ``config/`` with a minimal ``bootcamp_progress.json`` and copies the
    capture scripts into ``senzing-bootcamp/scripts/``. The workspace is removed
    on exit.

    Args:
        current_module: The ``current_module`` written to the progress file.

    Yields:
        The workspace root ``Path``.
    """
    root = Path(tempfile.mkdtemp(prefix="durable_qa_expl_"))
    (root / "config").mkdir(parents=True, exist_ok=True)
    _seed_scripts(root)
    _set_current_module(root, current_module)
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
    question is posed — WITHOUT the agent voluntarily logging it.

    Args:
        workspace: The workspace root.
        text: The question text (stored on lines 2+).
        qtype: The question type (stored on line 1).
    """
    (workspace / _QUESTION_PENDING).write_text(f"{qtype}\n{text}", encoding="utf-8")


def _run_durable_capture(
    workspace: Path, trigger: str, stdin_text: str | None = None
) -> int:
    """Run the deterministic, command-backed Q&A capture for *trigger*.

    Models the runtime executing the ``type: command`` capture hook on the Q&A
    cadence, independent of any agent narration. Discovers
    ``senzing-bootcamp/hooks/capture-qa-events.json`` in the installed power,
    finds the hook entries matching *trigger*, and runs each ``action.command``
    exactly as the runtime would (in the workspace cwd, with an optional stdin
    payload for the answer).

    When no such command hook is wired (the current, unfixed state), there is
    nothing to run — capture rode on the agent-voluntary hook — so this is a
    no-op and no event is persisted. That absence is precisely the bug the
    exploration tests surface.

    Args:
        workspace: The workspace to run the capture command in.
        trigger: The hook trigger to run (``"Stop"`` or ``"UserPromptSubmit"``).
        stdin_text: Optional stdin payload (the bootcamper's answer text).

    Returns:
        The number of command-backed capture invocations executed (``0`` when no
        command hook is wired for *trigger*).
    """
    if not _CAPTURE_HOOK.exists():
        return 0
    try:
        data = json.loads(_CAPTURE_HOOK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    env = _python_env(workspace)
    ran = 0
    for entry in data.get("hooks", []):
        if entry.get("trigger") != trigger:
            continue
        action = entry.get("action", {})
        if action.get("type") != "command":
            continue
        command = action.get("command")
        if not command:
            continue
        subprocess.run(
            ["bash", "-c", command],
            cwd=str(workspace),
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        ran += 1
    return ran


def _read_qa_events(workspace: Path) -> list[dict]:
    """Return the parsed ``question``/``answer`` events from the session log.

    Args:
        workspace: The workspace root.

    Returns:
        A list of ``question``/``answer`` completion events (empty when the log
        is absent).
    """
    log_path = workspace / _SESSION_LOG
    if not log_path.exists():
        return []
    events: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("event_type") in ("question", "answer"):
            events.append(entry)
    return events


def _texts(events: list[dict], event_type: str) -> list[str]:
    """Return the sorted ``data.text`` values for events of *event_type*."""
    return sorted(
        e["data"]["text"] for e in events if e.get("event_type") == event_type
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
    unchanged — making round-trip text assertions exact.

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
    the next cadence boundary. Kept short (1-4 exchanges) so the subprocess-
    driven capture stays fast.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty list of ``(module, question, answer)`` triples.
    """
    n = draw(st.integers(min_value=1, max_value=4))
    cadence: list[tuple[int, str, str]] = []
    for _ in range(n):
        module = draw(st.integers(min_value=1, max_value=11))
        question = draw(st_qa_text())
        answer = draw(st_qa_text())
        cadence.append((module, question, answer))
    return cadence


# ---------------------------------------------------------------------------
# Example bug-condition tests (deterministic, reproducible)
# ---------------------------------------------------------------------------


class TestAgentSkipCaptureExploration:
    """A Q&A cadence with no agent-voluntary logging must still be durable.

    **Validates: Requirements 2.1**

    Present a question and submit an answer without the agent running
    ``log_qa_event.py``; the deterministic, command-backed capture must persist
    both events to ``config/session_log.jsonl``.

    AUTHORED TO FAIL on unfixed code: with no ``capture-qa-events.json`` command
    hook, ``_run_durable_capture`` runs nothing and the log stays empty — the
    cadence event produced no durable event because capture rode on the
    agent-voluntary hook.
    """

    def test_agent_skip_capture_still_persists_qa(self) -> None:
        """Question and answer are durably logged even when the agent skips it."""
        question = "What is entity resolution?"
        answer = "Resolving records to real-world entities"
        with _workspace(current_module=5) as workspace:
            # A question is presented (Stop-boundary marker written).
            _present_question(workspace, question)

            # The agent does NOT voluntarily run log_qa_event.py. The
            # deterministic, command-backed capture fires on the cadence.
            _run_durable_capture(workspace, "Stop")  # record-question
            _run_durable_capture(
                workspace, "UserPromptSubmit", stdin_text=answer
            )  # record-answer

            events = _read_qa_events(workspace)
            questions = _texts(events, "question")
            answers = _texts(events, "answer")

            assert question in questions, (
                "Q&A cadence event produced no durable question event because "
                "capture rode on the agent-voluntary hook (no command-backed "
                f"capture ran); expected {question!r} in "
                f"config/session_log.jsonl, found questions={questions!r}"
            )
            assert answer in answers, (
                "Q&A cadence event produced no durable answer event because "
                "capture rode on the agent-voluntary hook (no command-backed "
                f"capture ran); expected {answer!r} in "
                f"config/session_log.jsonl, found answers={answers!r}"
            )


class TestCrossSessionLossExploration:
    """Modules 1-3 completed in an earlier session must retain their Q&A.

    **Validates: Requirements 2.2**

    Reproduces the reported case: Modules 1-3 were completed under the
    agent-voluntary hooks. If capture were durable and write-through, each
    module's Q&A would have been persisted at ask/answer time and would survive
    the session boundary.

    AUTHORED TO FAIL on unfixed code: with no command-backed capture, no Q&A was
    ever persisted for those modules and the log is empty across the boundary.
    """

    def test_modules_1_to_3_retain_durable_qa(self) -> None:
        """Each of Modules 1-3 has its durable question/answer after the boundary."""
        with _workspace() as workspace:
            # "Session A": complete Modules 1-3, each with a Q&A cadence the
            # agent never voluntarily logs. Durable capture should persist each.
            for module, question, answer in _MODULES_1_TO_3_FIXTURE:
                _set_current_module(workspace, module)
                _present_question(workspace, question)
                _run_durable_capture(workspace, "Stop")
                _run_durable_capture(
                    workspace, "UserPromptSubmit", stdin_text=answer
                )

            # A session boundary / restart intervenes — the on-disk log is all
            # that survives into the next session.
            events = _read_qa_events(workspace)
            questions = _texts(events, "question")
            answers = _texts(events, "answer")

            for module, question, answer in _MODULES_1_TO_3_FIXTURE:
                assert question in questions, (
                    f"Module {module} Q&A was lost across the session boundary: "
                    f"question {question!r} is absent from config/session_log.jsonl "
                    "because capture rode on the agent-voluntary hook; "
                    f"found questions={questions!r}"
                )
                assert answer in answers, (
                    f"Module {module} Q&A was lost across the session boundary: "
                    f"answer {answer!r} is absent from config/session_log.jsonl "
                    "because capture rode on the agent-voluntary hook; "
                    f"found answers={answers!r}"
                )


# ---------------------------------------------------------------------------
# Property-based bug-condition test
# ---------------------------------------------------------------------------


class TestDurableCaptureProperty:
    """For any Q&A cadence, deterministic capture persists every event.

    **Validates: Requirements 2.1, 2.2**

    Generates arbitrary Q&A cadence sequences and, for each exchange, presents
    the question and submits the answer WITHOUT the agent voluntarily logging.
    The deterministic, command-backed capture must persist one durable
    ``question`` and one durable ``answer`` per exchange.

    AUTHORED TO FAIL on unfixed code: with no command-backed capture hook, no
    event is ever persisted, so the log is empty for every generated cadence —
    surfacing the bug across the whole input domain.
    """

    @given(cadence=st_qa_cadence())
    def test_every_cadence_event_is_durably_persisted(
        self, cadence: list[tuple[int, str, str]]
    ) -> None:
        with _workspace() as workspace:
            for module, question, answer in cadence:
                _set_current_module(workspace, module)
                _present_question(workspace, question)
                _run_durable_capture(workspace, "Stop")
                _run_durable_capture(
                    workspace, "UserPromptSubmit", stdin_text=answer
                )

            events = _read_qa_events(workspace)
            logged_questions = _texts(events, "question")
            logged_answers = _texts(events, "answer")

            expected_questions = sorted(q for _, q, _ in cadence)
            expected_answers = sorted(a for _, _, a in cadence)

            assert logged_questions == expected_questions, (
                "not every cadence question was durably persisted (capture rode "
                "on the agent-voluntary hook; no command-backed capture ran): "
                f"expected {expected_questions!r}, got {logged_questions!r}"
            )
            assert logged_answers == expected_answers, (
                "not every cadence answer was durably persisted (capture rode "
                "on the agent-voluntary hook; no command-backed capture ran): "
                f"expected {expected_answers!r}, got {logged_answers!r}"
            )
