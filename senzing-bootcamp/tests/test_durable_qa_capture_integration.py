"""End-to-end INTEGRATION tests for the durable-qa-capture fix (power).

These tests wire the fix's two coordinated halves together and exercise them the
way the runtime does, rather than unit-testing a single helper:

- **End-to-end durability** (Requirements 2.1, 2.2): drive a full Q&A cadence
  through the real, command-backed capture hook
  (``senzing-bootcamp/hooks/capture-qa-events.json``) -- present a question,
  run the ``Stop`` capture command (no agent narration), submit an answer, run
  the ``UserPromptSubmit`` capture command -- and assert both the ``question``
  and the ``answer`` land durably in ``config/session_log.jsonl`` and are paired
  by ``question_id``.
- **Cross-session durability** (Requirements 2.2, 3.5): capture Q&A for several
  modules in "session A", then -- with only the on-disk log surviving into
  "session B" -- capture more, complete the track, and run the graduation
  completeness gate; assert every completed module has recoverable Q&A (no
  unrecoverable gap) and the prior log bytes were preserved append-around.
- **Graduation gate** (Requirements 2.3, 2.4, 3.1, 3.5): a completed module with
  a real Q&A gap makes ``ensure_graduation_artifacts.main()`` halt and name the
  module BEFORE any recap/transcript/PDF is rendered (no placeholder emitted);
  a fully-captured track passes the gate and renders its real Q&A unchanged with
  no placeholder text.

The graduation-gate assertions focus on the GATE behavior and the recap Markdown
path so the suite stays hermetic and fast -- they never trigger a real PDF
autoinstall (the halt case returns before rendering; the pass case drives the
Markdown renderer and asserts on the recap text and gate outcome).

Feature: durable-qa-capture

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.1, 3.5**
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

# ---------------------------------------------------------------------------
# Scripts import via sys.path (scripts aren't packages).
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_SCRIPTS_DIR: str = str(_POWER_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts  # noqa: E402  (path manipulated above)
import ensure_graduation_artifacts  # noqa: E402  (path manipulated above)
import generate_completion_summary  # noqa: E402  (path manipulated above)
import generate_transcript  # noqa: E402  (path manipulated above)
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
_RECAP: str = "docs/bootcamp_recap.md"
_TRANSCRIPT: str = "docs/bootcamp_transcript.md"
_PDF: str = "docs/bootcamp_recap.pdf"

# The exact placeholder the backfill emits for a module with no recoverable Q&A.
_PLACEHOLDER: str = (
    "N/A (section backfilled at track completion; "
    "original session content unavailable)"
)


# ---------------------------------------------------------------------------
# Command-backed capture harness (mirrors tasks 1/11 so the runtime path is
# exercised exactly as the runtime would run it).
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
def _capture_workspace(prefix: str = "durable_qa_integ_"):
    """Yield a throwaway workspace seeded for command-backed capture.

    Creates ``config/`` and ``docs/`` and copies the capture scripts into
    ``senzing-bootcamp/scripts/``. Removed on exit.

    Args:
        prefix: The temp-directory name prefix (aids debugging).

    Yields:
        The workspace root ``Path``.
    """
    root = Path(tempfile.mkdtemp(prefix=prefix))
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    _seed_scripts(root)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _set_current_module(workspace: Path, module: int) -> None:
    """Write ``config/bootcamp_progress.json`` with ``current_module``."""
    (workspace / _PROGRESS).write_text(
        json.dumps({"current_module": module, "modules_completed": []}),
        encoding="utf-8",
    )


def _write_progress(
    workspace: Path, modules_completed: list[int], current_module: int | None = None
) -> None:
    """Write ``config/bootcamp_progress.json`` with completed modules.

    Args:
        workspace: The workspace root.
        modules_completed: The completed-module list to record.
        current_module: The current module; defaults to the max completed
            module (or 1 when none are completed).
    """
    if current_module is None:
        current_module = max(modules_completed) if modules_completed else 1
    (workspace / _PROGRESS).write_text(
        json.dumps(
            {
                "current_module": current_module,
                "modules_completed": sorted(modules_completed),
            }
        ),
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


def _capture_exchange(
    workspace: Path, module: int, question: str, answer: str
) -> None:
    """Drive one full command-backed Q&A cadence for *module*.

    Sets ``current_module``, presents the question, runs the ``Stop`` capture
    command (record-question) and then the ``UserPromptSubmit`` capture command
    (record-answer) -- no agent narration between them.

    Args:
        workspace: The workspace root.
        module: The module the exchange belongs to.
        question: The question text presented at the Stop boundary.
        answer: The answer text submitted at the next prompt.
    """
    _set_current_module(workspace, module)
    _present_question(workspace, question)
    _run_capture_hook(workspace, "Stop")
    _run_capture_hook(workspace, "UserPromptSubmit", stdin_text=answer)


def _read_events(workspace: Path) -> list[dict]:
    """Return all parsed JSONL events from the workspace session log.

    Args:
        workspace: The workspace root.

    Returns:
        The parsed event dicts (empty when the log is absent).
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
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _events_of_type(events: list[dict], event_type: str) -> list[dict]:
    """Return the events whose ``event_type`` equals *event_type*."""
    return [e for e in events if e.get("event_type") == event_type]


# ---------------------------------------------------------------------------
# Real-Q&A seeding for the graduation-path tests (production event schema).
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# End-to-end durability
# ---------------------------------------------------------------------------


class TestEndToEndDurability:
    """A full Q&A cadence is durably captured and paired by the command hook.

    **Validates: Requirements 2.1, 2.2**

    Present a question, run the ``Stop`` capture command (no agent narration),
    submit an answer, run the ``UserPromptSubmit`` capture command; both events
    must land in ``config/session_log.jsonl`` and be paired by ``question_id``.
    """

    def test_single_cadence_persists_paired_question_and_answer(self) -> None:
        """One cadence yields one question + one answer, paired by id."""
        question = "What business problem are you solving?"
        answer = "Deduplicating our customer master list"
        with _capture_workspace() as workspace:
            _capture_exchange(workspace, module=1, question=question, answer=answer)

            events = _read_events(workspace)
            questions = _events_of_type(events, "question")
            answers = _events_of_type(events, "answer")

            assert len(questions) == 1, (
                "expected exactly one durable question event from the "
                f"command-backed hook, got {len(questions)}"
            )
            assert len(answers) == 1, (
                "expected exactly one durable answer event from the "
                f"command-backed hook, got {len(answers)}"
            )
            assert questions[0]["data"]["text"] == question
            assert answers[0]["data"]["text"] == answer

            # The answer is paired to its question by question_id.
            assert (
                answers[0]["data"]["question_id"]
                == questions[0]["data"]["question_id"]
            ), (
                "the durable answer was not paired to its question by "
                f"question_id: question={questions[0]['data']!r}, "
                f"answer={answers[0]['data']!r}"
            )

    def test_multiple_cadences_persist_and_pair_each_exchange(self) -> None:
        """Each of several cadences persists its own paired question/answer."""
        exchanges = [
            (1, "Which data sources will you load?", "Customers and vendors"),
            (2, "Which SDK language did you pick?", "Python for the first pass"),
            (3, "What did entity resolution reveal?", "Two records were one person"),
        ]
        with _capture_workspace() as workspace:
            for module, question, answer in exchanges:
                _capture_exchange(workspace, module, question, answer)

            events = _read_events(workspace)
            questions = _events_of_type(events, "question")
            answers = _events_of_type(events, "answer")

            assert len(questions) == len(exchanges)
            assert len(answers) == len(exchanges)

            # Every answer pairs to a distinct question that carries the right
            # text (build the id->text maps and check the round trip).
            q_by_id = {q["data"]["question_id"]: q["data"]["text"] for q in questions}
            assert len(q_by_id) == len(exchanges), "question ids were not unique"

            paired_texts = {
                q_by_id[a["data"]["question_id"]]: a["data"]["text"]
                for a in answers
            }
            expected = {q: a for _, q, a in exchanges}
            assert paired_texts == expected, (
                "durable answers were not paired to the right questions; "
                f"expected {expected!r}, got {paired_texts!r}"
            )


# ---------------------------------------------------------------------------
# Cross-session durability
# ---------------------------------------------------------------------------


class TestCrossSessionDurability:
    """Q&A captured in an earlier session survives into graduation with no gap.

    **Validates: Requirements 2.2, 3.5**

    Capture Q&A for several modules in "session A", then -- with only the on-disk
    ``config/session_log.jsonl`` surviving -- capture more in "session B",
    complete the track, and run the graduation completeness gate. Every
    completed module must have recoverable Q&A (no unrecoverable gap), and the
    "session A" log bytes must be preserved append-around by "session B".
    """

    def test_events_survive_across_sessions_and_track_completes_without_gap(
        self,
    ) -> None:
        """Session-A Q&A persists, session B appends, and graduation finds no gap."""
        session_a = [
            (1, "What outcome defines success?", "A clean, deduplicated list"),
            (2, "Which license will you use?", "The trial license to start"),
        ]
        session_b = [
            (3, "What did the first graph reveal?", "Cross-source matches"),
        ]
        with _capture_workspace() as workspace:
            # "Session A": capture Modules 1-2 through the command-backed hook.
            for module, question, answer in session_a:
                _capture_exchange(workspace, module, question, answer)

            # Only the on-disk log survives into the next session. Snapshot the
            # exact bytes to prove append-around preservation afterwards.
            log_path = workspace / _SESSION_LOG
            session_a_bytes = log_path.read_bytes()

            # "Session B": a fresh cadence run against the same on-disk workspace
            # (a new process per subprocess invocation) captures Module 3.
            for module, question, answer in session_b:
                _capture_exchange(workspace, module, question, answer)

            # The track is completed: all three modules are recorded complete.
            completed = [m for m, _, _ in session_a + session_b]
            _write_progress(workspace, modules_completed=completed)

            # Append-around preservation: the session-A bytes are still an exact
            # prefix of the log after session B appended to it (Req 3.5).
            after_bytes = log_path.read_bytes()
            assert after_bytes.startswith(session_a_bytes), (
                "session B did not preserve the session-A log bytes "
                "append-around; the earlier session's events were rewritten"
            )
            assert len(after_bytes) > len(session_a_bytes), (
                "session B captured nothing new to the durable log"
            )

            # Graduation completeness gate: no completed module ends with an
            # unrecoverable Q&A gap.
            report = validate_qa_capture.build_report(
                str(workspace / _PROGRESS), str(log_path)
            )
            assert report.ok, (
                "graduation found an unrecoverable Q&A gap across sessions; "
                f"missing modules={report.missing_modules!r}"
            )
            assert report.missing_modules == [], (
                "no module should be missing Q&A after cross-session capture; "
                f"got {report.missing_modules!r}"
            )
            # Each completed module is backed by a real, paired exchange.
            model = generate_transcript.build_model(
                generate_transcript.read_events(str(log_path))
            )
            captured_modules = {pair.module for pair in model.pairs}
            assert captured_modules == set(completed), (
                "not every completed module has a recoverable Q&A pair; "
                f"expected {set(completed)!r}, got {captured_modules!r}"
            )


# ---------------------------------------------------------------------------
# Graduation gate: halt-before-render on a real gap; render real Q&A when whole
# ---------------------------------------------------------------------------


class TestGraduationGate:
    """The pre-render gate halts on a real gap and passes a fully-captured track.

    **Validates: Requirements 2.3, 2.4, 3.1, 3.5**

    - A completed module with a real Q&A gap makes
      ``ensure_graduation_artifacts.main()`` return exit 1 and name the module
      BEFORE any recap/transcript/PDF is rendered -- no placeholder is emitted.
    - A fully-captured track passes the gate and its real Q&A renders unchanged
      with no placeholder text (asserted on the recap Markdown path and the gate
      outcome, avoiding any PDF autoinstall).
    """

    def test_real_gap_halts_before_any_artifact_is_rendered(self, capsys) -> None:
        """A gap module halts graduation and names it; nothing is rendered."""
        with _capture_workspace() as workspace:
            # Module 1 has real Q&A; Module 2 is completed but a genuine gap.
            _write_real_qa(workspace, 1, "What is your goal?", "Dedupe customers")
            _write_progress(workspace, modules_completed=[1, 2])

            recap_path = workspace / _RECAP
            transcript_path = workspace / _TRANSCRIPT
            pdf_path = workspace / _PDF
            # None of the artifacts exist before graduation runs.
            assert not recap_path.exists()
            assert not transcript_path.exists()
            assert not pdf_path.exists()

            exit_code = ensure_graduation_artifacts.main(
                [
                    "--progress",
                    str(workspace / _PROGRESS),
                    "--log",
                    str(workspace / _SESSION_LOG),
                    "--recap",
                    str(recap_path),
                    "--transcript",
                    str(transcript_path),
                    "--pdf",
                    str(pdf_path),
                ]
            )

            assert exit_code == 1, (
                "graduation did not halt on a completed module with a real Q&A "
                f"gap; expected exit 1, got {exit_code}"
            )

            captured = capsys.readouterr()
            combined = captured.out + captured.err
            assert "Module 2" in combined, (
                "graduation halted but did not name the missing module; "
                f"output was: {combined!r}"
            )

            # Halt-before-render: no artifact was created, so no placeholder
            # could have been emitted for the gap.
            assert not recap_path.exists(), (
                "the recap was rendered despite a real Q&A gap; the gate must "
                "halt BEFORE any rendering/backfill"
            )
            assert not transcript_path.exists(), (
                "the transcript was rendered despite a real Q&A gap"
            )
            assert not pdf_path.exists(), (
                "the recap PDF was rendered despite a real Q&A gap"
            )
            assert _PLACEHOLDER not in combined, (
                "the backfill placeholder was emitted for a real gap instead of "
                "halting loudly"
            )

    def test_fully_captured_track_passes_gate_and_renders_real_qa(self) -> None:
        """A whole track passes the gate; its real Q&A renders, no placeholder."""
        exchanges = [
            (1, "What business problem are you solving?", "Deduping our CRM"),
            (2, "Which SDK language did you choose?", "Python to prototype"),
            (3, "What surprised you in the results?", "A hidden duplicate merged"),
        ]
        with _capture_workspace() as workspace:
            for module, question, answer in exchanges:
                _write_real_qa(workspace, module, question, answer)
            _write_progress(workspace, modules_completed=[m for m, _, _ in exchanges])

            progress_path = str(workspace / _PROGRESS)
            log_path = str(workspace / _SESSION_LOG)

            # 1) The pre-render completeness gate passes for a whole track.
            gate = ensure_graduation_artifacts.qa_completeness_gate(
                ensure_graduation_artifacts.ArtifactPaths(
                    log=log_path, progress=progress_path
                )
            )
            assert gate is not None and gate.ok, (
                "a fully-captured track should pass the completeness gate; "
                f"missing modules={None if gate is None else gate.missing_modules!r}"
            )
            assert (
                validate_qa_capture.main(
                    ["--progress", progress_path, "--log", log_path, "--check"]
                )
                == 0
            ), "the validator CLI should exit 0 for a fully-captured track"

            # 2) The real-Q&A renderer emits the actual exchanges (no placeholder).
            entries = generate_completion_summary.parse_session_log(log_path)
            narrative = generate_completion_summary.build_narrative(
                entries,
                progress_path,
                "config/bootcamp_preferences.yaml",  # absent -> defaults
            )
            recap_markdown = generate_completion_summary.render_markdown(narrative)

            for _, question, answer in exchanges:
                assert question in recap_markdown, (
                    f"real question {question!r} did not render in the recap"
                )
                assert answer in recap_markdown, (
                    f"real answer {answer!r} did not render in the recap"
                )
            assert _PLACEHOLDER not in recap_markdown, (
                "a fully-captured track's recap must not contain the backfill "
                "placeholder"
            )

            # 3) Backfilling a recap that already covers every completed module
            #    is a no-op: no missing sections, no placeholder, bytes unchanged.
            recap_path = workspace / _RECAP
            recap_path.write_text(recap_markdown, encoding="utf-8")
            before = recap_path.read_bytes()
            backfilled = completion_artifacts.backfill_recap_sections(
                progress_path, str(recap_path)
            )
            assert backfilled == [], (
                "no section should be backfilled for a fully-captured track; "
                f"backfilled {backfilled!r}"
            )
            assert recap_path.read_bytes() == before, (
                "backfill rewrote a recap that already covered every module"
            )
            assert _PLACEHOLDER not in recap_path.read_text(encoding="utf-8"), (
                "backfill introduced a placeholder into a complete recap"
            )
