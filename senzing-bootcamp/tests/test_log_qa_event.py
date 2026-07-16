"""Property and example tests for the Q&A capture helper.

Feature: guaranteed-qa-capture

Exercises ``senzing-bootcamp/scripts/log_qa_event.py`` in an isolated temp
workspace: paired question/answer events, text-hash dedupe, answer self-heal,
no-orphan-answer and empty/no-pending no-ops, and non-blocking (exit 0)
behavior on unreadable/malformed inputs. All fixtures are synthetic and
PII-free.

The helper reads and writes cwd-relative state files under ``config/`` via
module-level path constants (``_QUESTION_PENDING_PATH``, ``_SIDECAR_PATH``,
``_SESSION_LOG_PATH``, ``_PROGRESS_PATH``). Rather than change the process cwd,
each test/example points those constants at a fresh temporary ``config/``
directory through the :func:`isolated_workspace` context manager, so no test
ever touches the real workspace and Hypothesis examples never share state.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Scripts import via sys.path (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import log_qa_event  # noqa: E402  (path manipulated above)

# ---------------------------------------------------------------------------
# Workspace isolation
# ---------------------------------------------------------------------------

_STATE_ATTRS: tuple[str, ...] = (
    "_PROGRESS_PATH",
    "_SESSION_LOG_PATH",
    "_QUESTION_PENDING_PATH",
    "_SIDECAR_PATH",
)


@contextlib.contextmanager
def isolated_workspace():
    """Point the helper's state-file constants at a fresh temp ``config/`` dir.

    Saves the module-level path constants, redirects each at a throwaway
    per-invocation ``config/`` directory, and restores them (and removes the
    temp tree) on exit. Yields the temp workspace root so callers can seed and
    inspect the ``config/`` state files the helper uses.

    Yields:
        The temporary workspace root ``Path`` (its ``config/`` subdir holds the
        state files the helper reads and writes).
    """
    root = Path(tempfile.mkdtemp(prefix="qa_capture_"))
    config = root / "config"
    config.mkdir(parents=True, exist_ok=True)
    saved = {attr: getattr(log_qa_event, attr) for attr in _STATE_ATTRS}
    log_qa_event._PROGRESS_PATH = str(config / "bootcamp_progress.json")
    log_qa_event._SESSION_LOG_PATH = str(config / "session_log.jsonl")
    log_qa_event._QUESTION_PENDING_PATH = str(config / ".question_pending")
    log_qa_event._SIDECAR_PATH = str(config / ".qa_capture.json")
    try:
        yield root
    finally:
        for attr, value in saved.items():
            setattr(log_qa_event, attr, value)
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# State-file helpers (operate on the temp workspace's config/ dir)
# ---------------------------------------------------------------------------


def write_pending(root: Path, text: str, question_type: str = "reflection") -> None:
    """Write ``config/.question_pending`` (type on line 1, text on lines 2+)."""
    (root / "config" / ".question_pending").write_text(
        f"{question_type}\n{text}", encoding="utf-8"
    )


def write_progress(root: Path, current_module: int) -> None:
    """Write a minimal ``config/bootcamp_progress.json`` with ``current_module``."""
    (root / "config" / "bootcamp_progress.json").write_text(
        json.dumps({"current_module": current_module}), encoding="utf-8"
    )


def write_sidecar_raw(root: Path, content: str) -> None:
    """Write raw ``config/.qa_capture.json`` content (may be malformed)."""
    (root / "config" / ".qa_capture.json").write_text(content, encoding="utf-8")


def read_events(root: Path) -> list[dict]:
    """Read the parsed ``question``/``answer`` events from the session log."""
    log_path = root / "config" / "session_log.jsonl"
    if not log_path.exists():
        return []
    events: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def read_sidecar(root: Path) -> dict | None:
    """Return the parsed sidecar dict, or None when absent/unreadable."""
    sidecar = root / "config" / ".qa_capture.json"
    if not sidecar.exists():
        return None
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


class _TtyStdin(io.StringIO):
    """A stdin stand-in that reports ``isatty() == True`` (no piped input).

    Mirrors the command-hook case where ``record-answer`` is invoked with a
    terminal (or otherwise-interactive) stdin and no data is piped in, so the
    helper must treat the answer as empty rather than block on ``read()``.
    """

    def isatty(self) -> bool:
        """Report an interactive terminal so the helper reads no answer."""
        return True


def run_main(argv: list[str], stdin_text: str | None = None) -> int:
    """Invoke ``log_qa_event.main`` with an optional stdin payload.

    Args:
        argv: The argument vector (e.g. ``["record-answer"]``).
        stdin_text: When provided, feeds this text on stdin (as the helper's
            CLI reads the answer from stdin). A ``StringIO`` reports
            ``isatty() == False`` so the helper reads it.

    Returns:
        The helper's exit code (always 0 by contract).
    """
    old_stdin = sys.stdin
    if stdin_text is not None:
        sys.stdin = io.StringIO(stdin_text)
    try:
        return log_qa_event.main(argv)
    finally:
        sys.stdin = old_stdin


def run_main_no_stdin(argv: list[str]) -> int:
    """Invoke ``log_qa_event.main`` with a tty-like stdin (no piped answer).

    Args:
        argv: The argument vector (e.g. ``["record-answer"]``).

    Returns:
        The helper's exit code (always 0 by contract).
    """
    old_stdin = sys.stdin
    sys.stdin = _TtyStdin()
    try:
        return log_qa_event.main(argv)
    finally:
        sys.stdin = old_stdin


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


def st_blank_text() -> st.SearchStrategy[str]:
    """A whitespace-only (or empty) string the helper must treat as no answer."""
    return st.text(alphabet=" \t\n", min_size=0, max_size=8)


# ---------------------------------------------------------------------------
# Example tests
# ---------------------------------------------------------------------------


class TestPairedEvents:
    """A recorded question and its answer share one ``question_id``.

    **Validates: Requirements 2.3**
    """

    def test_question_then_answer_are_paired(self) -> None:
        """record-question then record-answer yields one paired Q/A exchange."""
        with isolated_workspace() as root:
            write_progress(root, 5)
            write_pending(root, "What is entity resolution?")

            log_qa_event.record_question()
            log_qa_event.record_answer("Resolving records to real-world entities")

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question", "answer"]

            question, answer = events
            # The exchange is paired by a shared question_id.
            assert question["data"]["question_id"] == answer["data"]["question_id"]
            assert question["data"]["question_id"]
            # Text round-trips and the module comes from bootcamp_progress.json.
            assert question["data"]["text"] == "What is entity resolution?"
            assert answer["data"]["text"] == "Resolving records to real-world entities"
            assert question["module"] == 5
            assert answer["module"] == 5
            # The sidecar is cleared once the pair is recorded.
            assert read_sidecar(root) is None

    def test_answer_via_stdin_cli_is_paired(self) -> None:
        """The CLI plumbing (stdin answer) produces a paired exchange, exit 0."""
        with isolated_workspace() as root:
            write_pending(root, "Which database will you use?")

            assert run_main(["record-question"]) == 0
            assert run_main(["record-answer"], stdin_text="SQLite for the demo") == 0

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question", "answer"]
            assert (
                events[0]["data"]["question_id"] == events[1]["data"]["question_id"]
            )
            assert events[1]["data"]["text"] == "SQLite for the demo"


class TestTextHashDedupe:
    """A re-presented pending question is not double-logged.

    **Validates: Requirements 1.3**
    """

    def test_re_presented_question_logs_once(self) -> None:
        """Calling record-question repeatedly logs a single question event."""
        with isolated_workspace() as root:
            write_pending(root, "What problem are you solving?")

            log_qa_event.record_question()
            log_qa_event.record_question()
            log_qa_event.record_question()

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]

    def test_changed_pending_text_logs_a_new_question(self) -> None:
        """A different pending question (new text hash) logs a fresh event."""
        with isolated_workspace() as root:
            write_pending(root, "First question?")
            log_qa_event.record_question()

            write_pending(root, "A different, second question?")
            log_qa_event.record_question()

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question", "question"]
            assert events[0]["data"]["text"] == "First question?"
            assert events[1]["data"]["text"] == "A different, second question?"
            # Distinct questions get distinct ids.
            assert (
                events[0]["data"]["question_id"] != events[1]["data"]["question_id"]
            )


class TestSelfHeal:
    """record-answer self-heals when the question was never logged.

    **Validates: Requirements 2.3**
    """

    def test_answer_logs_question_first_when_no_sidecar(self) -> None:
        """Pending present but no sidecar: log the question, then pair the answer."""
        with isolated_workspace() as root:
            write_pending(root, "Why does pairing matter?")
            assert read_sidecar(root) is None  # question was never logged

            log_qa_event.record_answer("So the transcript reads as an exchange")

            events = read_events(root)
            # Self-heal logs the question first, then the answer.
            assert [e["event_type"] for e in events] == ["question", "answer"]
            assert (
                events[0]["data"]["question_id"] == events[1]["data"]["question_id"]
            )
            assert events[0]["data"]["text"] == "Why does pairing matter?"
            assert events[1]["data"]["text"] == "So the transcript reads as an exchange"
            assert read_sidecar(root) is None


class TestNoOrphanAnswers:
    """record-answer never appends an answer with no question to pair.

    **Validates: Requirements 2.4**
    """

    def test_answer_without_pending_or_sidecar_is_noop(self) -> None:
        """Neither sidecar nor pending question: no answer event is appended."""
        with isolated_workspace() as root:
            log_qa_event.record_answer("an answer with nothing to pair to")

            assert read_events(root) == []
            assert read_sidecar(root) is None


class TestNoOps:
    """No-op paths make no change to the log or sidecar.

    **Validates: Requirements 1.3, 2.4**
    """

    def test_record_question_without_pending_is_noop(self) -> None:
        """No ``.question_pending``: record-question makes no change."""
        with isolated_workspace() as root:
            log_qa_event.record_question()

            assert read_events(root) == []
            assert read_sidecar(root) is None

    def test_empty_pending_body_is_noop(self) -> None:
        """A pending marker with only a type line (no body) logs nothing."""
        with isolated_workspace() as root:
            # Type line only — no question text on lines 2+.
            (root / "config" / ".question_pending").write_text(
                "reflection\n", encoding="utf-8"
            )

            log_qa_event.record_question()

            assert read_events(root) == []
            assert read_sidecar(root) is None

    def test_empty_answer_leaves_pair_open(self) -> None:
        """An empty answer appends no answer event and preserves the sidecar."""
        with isolated_workspace() as root:
            write_pending(root, "A question awaiting a real answer?")
            log_qa_event.record_question()
            sidecar_before = read_sidecar(root)

            log_qa_event.record_answer("")
            log_qa_event.record_answer("   \t  ")

            events = read_events(root)
            # Only the original question was logged; no answer event appended.
            assert [e["event_type"] for e in events] == ["question"]
            # The sidecar is untouched so a later real answer can still pair.
            assert read_sidecar(root) == sidecar_before


class TestNonBlocking:
    """The helper exits 0 on every path and never makes a destructive change.

    **Validates: Requirements 4.1**
    """

    def test_malformed_sidecar_record_question_exits_zero(self) -> None:
        """A corrupt sidecar does not block record-question (exit 0)."""
        with isolated_workspace() as root:
            write_pending(root, "Question with a broken sidecar?")
            write_sidecar_raw(root, "{ this is not valid json")

            assert run_main(["record-question"]) == 0
            # Unreadable sidecar is treated as "not yet logged": the question is
            # captured and a valid sidecar written.
            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]
            assert read_sidecar(root) is not None

    def test_malformed_progress_defaults_module_and_exits_zero(self) -> None:
        """A corrupt progress file yields exit 0 and a default module of 0."""
        with isolated_workspace() as root:
            write_pending(root, "Question with a broken progress file?")
            (root / "config" / "bootcamp_progress.json").write_text(
                "{not valid json", encoding="utf-8"
            )

            assert run_main(["record-question"]) == 0
            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]
            assert events[0]["module"] == 0

    def test_unknown_and_missing_subcommand_exit_zero(self) -> None:
        """argparse errors (bad/missing subcommand) never block: exit 0."""
        with isolated_workspace():
            assert run_main(["not-a-real-mode"]) == 0
            assert run_main([]) == 0

    def test_write_error_is_swallowed_and_non_destructive(self, monkeypatch) -> None:
        """An I/O error while appending is swallowed (exit 0), log untouched."""
        with isolated_workspace() as root:
            write_pending(root, "Question that fails to persist?")

            def _boom(*_args, **_kwargs):
                raise RuntimeError("simulated write failure")

            monkeypatch.setattr(
                log_qa_event.session_logger, "append_completion_entry", _boom
            )

            assert run_main(["record-question"]) == 0
            # Nothing was persisted and no sidecar was left behind.
            assert read_events(root) == []
            assert read_sidecar(root) is None


class TestCommandHookInvocation:
    """The CLI, as a command-backed hook runs it, always exits 0.

    These exercise ``main`` through its argv/stdin surface (the way the
    ``capture-qa-events`` command hook invokes it) rather than the module
    functions directly, asserting exit code 0 on every path and the correct
    event shape whenever a question or answer is captured.

    **Validates: Requirements 2.1, 3.2, 3.3, 3.4**
    """

    def test_record_question_with_pending_exits_zero_and_logs_shape(self) -> None:
        """record-question with a pending marker: exit 0, one shaped question."""
        with isolated_workspace() as root:
            write_progress(root, 3)
            write_pending(root, "What data sources will you load?")

            assert run_main(["record-question"]) == 0

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]
            question = events[0]
            # Event shape: module + data.{text, question_id}.
            assert question["module"] == 3
            assert question["data"]["text"] == "What data sources will you load?"
            assert question["data"]["question_id"]
            # A sidecar is written so a later answer can pair to this question.
            sidecar = read_sidecar(root)
            assert sidecar is not None
            assert sidecar["question_id"] == question["data"]["question_id"]

    def test_record_question_without_pending_exits_zero_and_logs_nothing(self) -> None:
        """record-question with no pending marker: exit 0, no event, no sidecar."""
        with isolated_workspace() as root:
            assert run_main(["record-question"]) == 0

            assert read_events(root) == []
            assert read_sidecar(root) is None

    def test_record_answer_with_sidecar_pairs_to_logged_question(self) -> None:
        """record-answer via stdin with an existing sidecar pairs to its id."""
        with isolated_workspace() as root:
            write_progress(root, 4)
            write_pending(root, "Which entity type matters most?")
            # Log the question first so a sidecar (with question_id) exists.
            assert run_main(["record-question"]) == 0
            sidecar = read_sidecar(root)
            assert sidecar is not None
            expected_qid = sidecar["question_id"]

            assert run_main(["record-answer"], stdin_text="PERSON records") == 0

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question", "answer"]
            answer = events[1]
            # The answer pairs to the sidecar's question_id and is shaped right.
            assert answer["data"]["question_id"] == expected_qid
            assert answer["data"]["text"] == "PERSON records"
            assert answer["module"] == 4
            # The sidecar is cleared once the pair is recorded.
            assert read_sidecar(root) is None

    def test_record_answer_without_sidecar_self_heals(self) -> None:
        """record-answer via stdin, no sidecar: log the question first, then pair."""
        with isolated_workspace() as root:
            write_pending(root, "Why capture Q&A durably?")
            assert read_sidecar(root) is None  # question was never logged

            assert (
                run_main(["record-answer"], stdin_text="So the recap is complete")
                == 0
            )

            events = read_events(root)
            # Self-heal logs the question first, then the paired answer.
            assert [e["event_type"] for e in events] == ["question", "answer"]
            assert (
                events[0]["data"]["question_id"] == events[1]["data"]["question_id"]
            )
            assert events[0]["data"]["text"] == "Why capture Q&A durably?"
            assert events[1]["data"]["text"] == "So the recap is complete"
            assert read_sidecar(root) is None

    def test_record_answer_empty_stdin_exits_zero_and_logs_nothing(self) -> None:
        """record-answer with empty piped stdin: exit 0, no answer event."""
        with isolated_workspace() as root:
            write_pending(root, "An open question awaiting a real answer?")
            assert run_main(["record-question"]) == 0
            sidecar_before = read_sidecar(root)

            assert run_main(["record-answer"], stdin_text="") == 0

            events = read_events(root)
            # Only the question is logged; the empty answer is a no-op.
            assert [e["event_type"] for e in events] == ["question"]
            # The sidecar is preserved so a later real answer can still pair.
            assert read_sidecar(root) == sidecar_before

    def test_record_answer_no_stdin_tty_exits_zero_without_crash(self) -> None:
        """record-answer with a tty stdin (no piped input): exit 0, no crash."""
        with isolated_workspace() as root:
            write_pending(root, "A question with no answer piped in?")
            assert run_main(["record-question"]) == 0
            sidecar_before = read_sidecar(root)

            # A tty stdin means no answer was piped: the helper must not block
            # on read() and must treat the answer as empty.
            assert run_main_no_stdin(["record-answer"]) == 0

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]
            assert read_sidecar(root) == sidecar_before


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestPairedEventsProperty:
    """For any question/answer, the recorded exchange is paired by id.

    **Validates: Requirements 2.3**
    """

    @given(question=st_qa_text(), answer=st_qa_text())
    def test_recorded_exchange_is_paired(self, question: str, answer: str) -> None:
        with isolated_workspace() as root:
            write_pending(root, question)

            log_qa_event.record_question()
            log_qa_event.record_answer(answer)

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question", "answer"]
            q_event, a_event = events
            assert q_event["data"]["question_id"] == a_event["data"]["question_id"]
            assert q_event["data"]["text"] == question
            assert a_event["data"]["text"] == answer
            assert read_sidecar(root) is None


class TestDedupeProperty:
    """For any pending question, repeated captures log exactly one event.

    **Validates: Requirements 1.3**
    """

    @given(question=st_qa_text(), repeats=st.integers(min_value=1, max_value=6))
    def test_repeated_record_question_logs_once(
        self, question: str, repeats: int
    ) -> None:
        with isolated_workspace() as root:
            write_pending(root, question)

            for _ in range(repeats):
                log_qa_event.record_question()

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]
            assert events[0]["data"]["text"] == question


class TestSelfHealProperty:
    """For any question/answer, record-answer self-heals a missing question.

    **Validates: Requirements 2.3**
    """

    @given(question=st_qa_text(), answer=st_qa_text())
    def test_answer_self_heals(self, question: str, answer: str) -> None:
        with isolated_workspace() as root:
            write_pending(root, question)  # no sidecar: question not yet logged

            log_qa_event.record_answer(answer)

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question", "answer"]
            q_event, a_event = events
            assert q_event["data"]["question_id"] == a_event["data"]["question_id"]
            assert q_event["data"]["text"] == question
            assert a_event["data"]["text"] == answer


class TestNoOrphanAnswerProperty:
    """For any answer, no pending question means no answer event.

    **Validates: Requirements 2.4**
    """

    @given(answer=st_qa_text())
    def test_answer_without_pending_is_noop(self, answer: str) -> None:
        with isolated_workspace() as root:
            log_qa_event.record_answer(answer)

            assert read_events(root) == []
            assert read_sidecar(root) is None


class TestNonBlockingProperty:
    """For any inputs (incl. malformed sidecar), the helper exits 0.

    **Validates: Requirements 4.1**
    """

    @given(
        pending=st.one_of(st.none(), st_qa_text()),
        sidecar=st.text(max_size=80),
        answer=st.text(max_size=80),
    )
    def test_main_always_exits_zero(
        self, pending: str | None, sidecar: str, answer: str
    ) -> None:
        with isolated_workspace() as root:
            if pending is not None:
                write_pending(root, pending)
            write_sidecar_raw(root, sidecar)  # arbitrary/possibly-malformed

            # Both subcommands must return 0 regardless of input shape.
            assert run_main(["record-question"]) == 0
            assert run_main(["record-answer"], stdin_text=answer) == 0

    @given(blank=st_blank_text())
    def test_empty_answer_never_orphans(self, blank: str) -> None:
        """A blank answer with an open pair never appends an answer event."""
        with isolated_workspace() as root:
            write_pending(root, "An open question?")
            log_qa_event.record_question()
            sidecar_before = read_sidecar(root)

            log_qa_event.record_answer(blank)

            events = read_events(root)
            assert [e["event_type"] for e in events] == ["question"]
            assert read_sidecar(root) == sidecar_before
