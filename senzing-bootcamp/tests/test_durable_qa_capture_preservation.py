"""Preservation property tests for the durable-qa-capture bugfix (power).

These tests follow the bugfix workflow's *observation-first* methodology: they
observe the behavior of the UNFIXED ``log_qa_event.py`` and encode it, so they
PASS on the current code and thereby pin down the baseline the fix must
preserve. They map to the design's "Preservation Requirements" and Correctness
Properties 3-8.

The design's ``isBugCondition`` covers only the *durability* defect (a Q&A
cadence event that is never persisted because capture rode on an agent-voluntary
hook). Everything these tests exercise is on the NOT-``isBugCondition`` side of
that line — the existing, correct capture semantics of ``log_qa_event.py``:

    Property 3 - Non-Blocking Capture (this task): for any error-inducing input,
        both ``record-question`` and ``record-answer`` exit 0 and raise nothing.

    Property 4 - Idempotent Question Logging          (added by task 4)
    Property 5 - Answer-to-Question Pairing/Self-Heal (added by task 4)
    Property 6 - Byte-for-Byte Append-Around          (added by task 4)
    Property 7 - Real-Q&A Rendering Unchanged         (added by task 5)
    Property 8 - Standard Library Only                (added by task 5)

The shared workspace/invocation helpers below are intentionally generic so the
later tasks can extend this file without reworking the harness.

Feature: durable-qa-capture
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable, then import the helper under test.
# (conftest also does this; repeated here so the module imports standalone.)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts  # noqa: E402
import generate_transcript  # noqa: E402
import log_qa_event  # noqa: E402

# Workspace-relative state paths (mirroring the helper's own constants).
_PROGRESS: str = "config/bootcamp_progress.json"
_SESSION_LOG: str = "config/session_log.jsonl"
_QUESTION_PENDING: str = "config/.question_pending"
_SIDECAR: str = "config/.qa_capture.json"


# ---------------------------------------------------------------------------
# Shared workspace + invocation helpers
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _workspace(current_module: int = 1):
    """Yield a throwaway workspace and run inside it as the current directory.

    ``log_qa_event.py`` resolves every state file relative to the process cwd
    (``config/session_log.jsonl`` etc.), so each example runs in its own
    temporary directory. The prior working directory is always restored and the
    temporary tree is removed on exit.

    Args:
        current_module: The ``current_module`` written to a minimal
            ``config/bootcamp_progress.json`` (``0`` writes no progress file).

    Yields:
        The workspace root ``Path``.
    """
    root = Path(tempfile.mkdtemp(prefix="durable_qa_preserve_"))
    (root / "config").mkdir(parents=True, exist_ok=True)
    if current_module:
        (root / _PROGRESS).write_text(
            json.dumps({"current_module": current_module, "modules_completed": []}),
            encoding="utf-8",
        )
    prior = os.getcwd()
    try:
        os.chdir(root)
        yield root
    finally:
        os.chdir(prior)
        # Best-effort cleanup; never let teardown fail a test.
        for path in sorted(root.rglob("*"), reverse=True):
            try:
                path.rmdir() if path.is_dir() else path.unlink()
            except OSError:
                pass
        try:
            root.rmdir()
        except OSError:
            pass


def _run_record_question() -> int:
    """Invoke ``log_qa_event.py record-question`` in-process; return exit code."""
    return log_qa_event.main(["record-question"])


def _run_record_answer(answer_text: str) -> int:
    """Invoke ``log_qa_event.py record-answer`` with *answer_text* piped on stdin.

    Replaces ``sys.stdin`` with an in-memory stream (``isatty()`` is ``False``,
    so the helper reads it) exactly as the command-backed hook would pipe the
    bootcamper's message, then restores the real stdin.

    Args:
        answer_text: The stdin payload delivered to ``record-answer``.

    Returns:
        The helper's exit code.
    """
    real_stdin = sys.stdin
    sys.stdin = io.StringIO(answer_text)
    try:
        return log_qa_event.main(["record-answer"])
    finally:
        sys.stdin = real_stdin


def _read_qa_events(workspace: Path) -> list[dict]:
    """Return parsed ``question``/``answer`` events from the session log.

    Args:
        workspace: The workspace root to read ``config/session_log.jsonl`` from.

    Returns:
        A list of ``question``/``answer`` completion events (empty when the log
        is absent or unreadable).
    """
    log_path = workspace / _SESSION_LOG
    if not log_path.is_file():
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


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_TEXT_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 .,?!\n"
)


def st_text_blob() -> st.SearchStrategy[str]:
    """Arbitrary short text, possibly empty or whitespace-only.

    Used both as answer stdin payloads and as raw file contents for the
    error-inducing states, so it deliberately includes newlines and blanks.

    Returns:
        A Hypothesis strategy producing text of length 0-80.
    """
    return st.text(alphabet=_TEXT_ALPHABET, min_size=0, max_size=80)


def st_pending_state() -> st.SearchStrategy[str]:
    """The state of ``config/.question_pending`` to materialize.

    - ``absent``    : the marker file does not exist.
    - ``empty``     : the file exists but has no question body.
    - ``unreadable``: the path is a directory, so ``read_text`` raises.
    - ``valid``     : a well-formed ``<type>\\n<question>`` marker.

    Returns:
        A Hypothesis strategy over the four state labels.
    """
    return st.sampled_from(["absent", "empty", "unreadable", "valid"])


def st_sidecar_state() -> st.SearchStrategy[str]:
    """The state of ``config/.qa_capture.json`` to materialize.

    - ``absent``    : no sidecar.
    - ``malformed`` : non-JSON bytes, so parsing raises (swallowed).
    - ``unreadable``: the path is a directory, so ``read_text`` raises.
    - ``valid``     : a well-formed sidecar dict.

    Returns:
        A Hypothesis strategy over the four state labels.
    """
    return st.sampled_from(["absent", "malformed", "unreadable", "valid"])


def st_session_log_state() -> st.SearchStrategy[str]:
    """The state of ``config/session_log.jsonl`` to materialize.

    - ``absent``    : no log yet (the common first-write case).
    - ``unreadable``: the path is a directory, so appending raises (swallowed).

    Returns:
        A Hypothesis strategy over the two state labels.
    """
    return st.sampled_from(["absent", "unreadable"])


def _materialize_error_state(
    workspace: Path,
    pending: str,
    sidecar: str,
    session_log: str,
    filler: str,
) -> None:
    """Set up the on-disk error-inducing state inside *workspace*.

    Args:
        workspace: The workspace root.
        pending: A :func:`st_pending_state` label.
        sidecar: A :func:`st_sidecar_state` label.
        session_log: A :func:`st_session_log_state` label.
        filler: Arbitrary text used to fill "valid/empty" file bodies.
    """
    q_path = workspace / _QUESTION_PENDING
    if pending == "empty":
        q_path.write_text("reflection\n", encoding="utf-8")
    elif pending == "unreadable":
        q_path.mkdir(parents=True, exist_ok=True)
    elif pending == "valid":
        body = filler.strip() or "What is entity resolution?"
        q_path.write_text(f"reflection\n{body}", encoding="utf-8")

    s_path = workspace / _SIDECAR
    if sidecar == "malformed":
        s_path.write_text("}{ not json" + filler, encoding="utf-8")
    elif sidecar == "unreadable":
        s_path.mkdir(parents=True, exist_ok=True)
    elif sidecar == "valid":
        s_path.write_text(
            json.dumps({"question_id": "q-existing", "text_hash": "deadbeef"}),
            encoding="utf-8",
        )

    if session_log == "unreadable":
        (workspace / _SESSION_LOG).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Property 3 - Preservation: Non-Blocking Capture
# ---------------------------------------------------------------------------


class TestNonBlockingCapturePreservation:
    """``log_qa_event.py`` is non-blocking for any error-inducing input.

    **Validates: Requirements 3.2**

    Observed baseline on the UNFIXED helper: whatever error-inducing combination
    of missing/unreadable ``config/.question_pending``, absent/unreadable
    ``config/session_log.jsonl``, and absent/malformed/unreadable
    ``config/.qa_capture.json`` is present, both ``record-question`` and
    ``record-answer`` swallow the error, exit 0, and raise nothing — never
    interrupting the bootcamp flow. These tests encode that baseline so the fix
    must preserve it.
    """

    @given(
        pending=st_pending_state(),
        sidecar=st_sidecar_state(),
        session_log=st_session_log_state(),
        filler=st_text_blob(),
    )
    def test_record_question_is_non_blocking(
        self, pending: str, sidecar: str, session_log: str, filler: str
    ) -> None:
        """``record-question`` exits 0 and raises nothing for any error state."""
        with _workspace() as workspace:
            _materialize_error_state(workspace, pending, sidecar, session_log, filler)
            exit_code = _run_record_question()
            assert exit_code == 0, (
                "record-question must be non-blocking (exit 0) for error-inducing "
                f"input pending={pending!r} sidecar={sidecar!r} "
                f"session_log={session_log!r}; got exit {exit_code}"
            )

    @given(
        pending=st_pending_state(),
        sidecar=st_sidecar_state(),
        session_log=st_session_log_state(),
        answer=st_text_blob(),
    )
    def test_record_answer_is_non_blocking(
        self, pending: str, sidecar: str, session_log: str, answer: str
    ) -> None:
        """``record-answer`` exits 0 and raises nothing for any error state."""
        with _workspace() as workspace:
            _materialize_error_state(workspace, pending, sidecar, session_log, answer)
            exit_code = _run_record_answer(answer)
            assert exit_code == 0, (
                "record-answer must be non-blocking (exit 0) for error-inducing "
                f"input pending={pending!r} sidecar={sidecar!r} "
                f"session_log={session_log!r} answer_len={len(answer)}; "
                f"got exit {exit_code}"
            )

    @given(
        pending=st_pending_state(),
        sidecar=st_sidecar_state(),
        session_log=st_session_log_state(),
        answer=st_text_blob(),
    )
    def test_full_cadence_is_non_blocking(
        self, pending: str, sidecar: str, session_log: str, answer: str
    ) -> None:
        """A record-question then record-answer cadence never blocks.

        Runs both modes in sequence against the same error-inducing state (the
        real command-hook cadence), asserting each invocation exits 0.
        """
        with _workspace() as workspace:
            _materialize_error_state(workspace, pending, sidecar, session_log, answer)
            assert _run_record_question() == 0
            assert _run_record_answer(answer) == 0


# ---------------------------------------------------------------------------
# Additional strategies + helpers for Properties 4, 5, 6 (added by task 4)
# ---------------------------------------------------------------------------
#
# These reuse the shared harness above (``_workspace``, ``_run_record_question``,
# ``_run_record_answer``, ``_read_qa_events``) and only add the small pieces the
# idempotency / pairing / append-around observations need: a strategy for
# non-empty question/answer text, a strategy for arbitrary pre-existing file
# bytes, and a helper that materializes the ``config/.question_pending`` marker
# the way the Stop hook would before ``record-question`` runs.


def st_nonempty_text() -> st.SearchStrategy[str]:
    """Non-empty (after strip) short text usable as a question or answer body.

    Excludes payloads that are blank or whitespace-only, because both
    ``record-question`` (no pending body) and ``record-answer`` (empty stdin)
    intentionally no-op on those — they are covered by the non-blocking property
    above, not by the idempotency/pairing observations here.

    Returns:
        A Hypothesis strategy producing text whose ``strip()`` is non-empty.
    """
    return st.text(alphabet=_TEXT_ALPHABET, min_size=1, max_size=80).filter(
        lambda s: bool(s.strip())
    )


def st_preexisting_blob() -> st.SearchStrategy[str]:
    """Arbitrary pre-existing file content, possibly empty or multi-line.

    Used to seed ``config/session_log.jsonl`` and ``docs/bootcamp_recap.md``
    before a capture so the append-around observation can assert prior bytes are
    preserved. Deliberately includes newlines and non-JSON text: the capture
    path only ever appends, so whatever bytes are present must survive verbatim.

    Returns:
        A Hypothesis strategy producing text of length 0-200.
    """
    return st.text(alphabet=_TEXT_ALPHABET, min_size=0, max_size=200)


def _write_pending_question(workspace: Path, question_text: str) -> None:
    """Materialize ``config/.question_pending`` as the Stop hook would.

    Writes the marker in the helper's expected ``<type>\\n<question>`` shape so a
    subsequent ``record-question`` (or self-healing ``record-answer``) reads
    *question_text* as the outstanding question.

    Args:
        workspace: The workspace root.
        question_text: The pending question body to record.
    """
    (workspace / _QUESTION_PENDING).write_text(
        f"reflection\n{question_text}", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Property 4 - Preservation: Idempotent Question Logging
# ---------------------------------------------------------------------------


class TestIdempotentQuestionLoggingPreservation:
    """The same pending question is logged exactly once, however many times seen.

    **Validates: Requirements 3.3**

    Observed baseline on the UNFIXED helper: ``record-question`` dedupes via the
    ``config/.qa_capture.json`` sidecar (question text hash), so re-presenting
    the identical pending question across N turns / session boundaries yields
    exactly ONE ``question`` event. These tests encode that baseline so the fix
    must preserve it.
    """

    @given(question_text=st_nonempty_text(), presentations=st.integers(1, 8))
    def test_repeated_presentation_logs_one_question(
        self, question_text: str, presentations: int
    ) -> None:
        """Presenting the same pending question N times logs exactly one event."""
        with _workspace() as workspace:
            _write_pending_question(workspace, question_text)
            for _ in range(presentations):
                # The marker persists between calls, mirroring the same pending
                # question surviving across turns / a session boundary.
                assert _run_record_question() == 0

            events = _read_qa_events(workspace)
            questions = [e for e in events if e.get("event_type") == "question"]
            assert len(questions) == 1, (
                f"the same pending question presented {presentations} times must "
                f"be logged exactly once; got {len(questions)} question events"
            )

    @given(question_text=st_nonempty_text(), presentations=st.integers(2, 8))
    def test_sidecar_dedupe_is_stable_across_calls(
        self, question_text: str, presentations: int
    ) -> None:
        """The logged question id is stable across repeated presentations.

        After the first ``record-question`` the sidecar pins the question id and
        text hash; every later presentation is a no-op, so the single logged
        event keeps the same ``question_id``.
        """
        with _workspace() as workspace:
            _write_pending_question(workspace, question_text)
            assert _run_record_question() == 0
            first = _read_qa_events(workspace)
            first_questions = [e for e in first if e.get("event_type") == "question"]
            assert len(first_questions) == 1
            first_qid = first_questions[0]["data"]["question_id"]

            for _ in range(presentations - 1):
                assert _run_record_question() == 0

            after = _read_qa_events(workspace)
            after_questions = [e for e in after if e.get("event_type") == "question"]
            assert len(after_questions) == 1
            assert after_questions[0]["data"]["question_id"] == first_qid


# ---------------------------------------------------------------------------
# Property 5 - Preservation: Answer-to-Question Pairing and Self-Heal
# ---------------------------------------------------------------------------


class TestAnswerPairingAndSelfHealPreservation:
    """Answers pair to their question's id, self-healing when none was logged.

    **Validates: Requirements 3.4**

    Observed baseline on the UNFIXED helper: ``record-answer`` pairs the answer
    to the pending question's id. When a question was already logged it reuses
    the sidecar id; when no question was logged first it self-heals by logging
    the pending question, then pairs the answer to that freshly generated id. In
    both cases the log ends with a ``question`` event ahead of its ``answer``
    event sharing one ``question_id``. These tests encode that baseline.
    """

    @given(question_text=st_nonempty_text(), answer_text=st_nonempty_text())
    def test_answer_pairs_to_logged_question(
        self, question_text: str, answer_text: str
    ) -> None:
        """record-question then record-answer pairs the answer to that question."""
        with _workspace() as workspace:
            _write_pending_question(workspace, question_text)
            assert _run_record_question() == 0
            assert _run_record_answer(answer_text) == 0

            events = _read_qa_events(workspace)
            questions = [e for e in events if e.get("event_type") == "question"]
            answers = [e for e in events if e.get("event_type") == "answer"]
            assert len(questions) == 1
            assert len(answers) == 1
            assert (
                answers[0]["data"]["question_id"]
                == questions[0]["data"]["question_id"]
            ), "answer must carry the logged question's id"

    @given(question_text=st_nonempty_text(), answer_text=st_nonempty_text())
    def test_answer_self_heals_when_question_absent(
        self, question_text: str, answer_text: str
    ) -> None:
        """record-answer with no prior record-question logs the question first.

        This is the self-heal case: only the pending marker exists (the Stop
        hook's ``record-question`` never ran), yet the answer must not be
        orphaned — the helper logs the question first and pairs the answer to it.
        """
        with _workspace() as workspace:
            _write_pending_question(workspace, question_text)
            # Note: no _run_record_question() here — the self-heal path.
            assert _run_record_answer(answer_text) == 0

            events = _read_qa_events(workspace)
            questions = [e for e in events if e.get("event_type") == "question"]
            answers = [e for e in events if e.get("event_type") == "answer"]
            assert len(questions) == 1, "self-heal must log the question first"
            assert len(answers) == 1
            assert (
                answers[0]["data"]["question_id"]
                == questions[0]["data"]["question_id"]
            )
            # The question event is appended before its answer event.
            q_index = events.index(questions[0])
            a_index = events.index(answers[0])
            assert q_index < a_index, "question must be logged before its answer"


# ---------------------------------------------------------------------------
# Property 6 - Preservation: Byte-for-Byte Append-Around
# ---------------------------------------------------------------------------


class TestAppendAroundPreservation:
    """Prior on-disk bytes survive a capture verbatim (append-around, no overwrite).

    **Validates: Requirements 3.5**

    Observed baseline on the UNFIXED helper: capture only ever appends to
    ``config/session_log.jsonl`` and never touches ``docs/bootcamp_recap.md``.
    So arbitrary pre-existing session-log bytes remain a byte-for-byte prefix of
    the log after a full capture cadence, and an existing recap is left entirely
    unchanged. These tests encode that baseline.
    """

    @given(
        preexisting=st_preexisting_blob(),
        question_text=st_nonempty_text(),
        answer_text=st_nonempty_text(),
    )
    def test_session_log_prior_bytes_preserved(
        self, preexisting: str, question_text: str, answer_text: str
    ) -> None:
        """Existing session-log bytes are preserved as a prefix after capture."""
        with _workspace() as workspace:
            log_path = workspace / _SESSION_LOG
            original_bytes = preexisting.encode("utf-8")
            log_path.write_bytes(original_bytes)

            _write_pending_question(workspace, question_text)
            assert _run_record_question() == 0
            assert _run_record_answer(answer_text) == 0

            new_bytes = log_path.read_bytes()
            assert new_bytes.startswith(original_bytes), (
                "capture must append-around: prior session_log.jsonl bytes must "
                "be preserved byte-for-byte as a prefix, never overwritten"
            )
            # And the capture actually appended (question + answer) beyond it.
            assert len(new_bytes) > len(original_bytes)

    @given(
        recap_content=st_preexisting_blob(),
        question_text=st_nonempty_text(),
        answer_text=st_nonempty_text(),
    )
    def test_existing_recap_is_untouched(
        self, recap_content: str, question_text: str, answer_text: str
    ) -> None:
        """An existing docs/bootcamp_recap.md is byte-for-byte unchanged by capture."""
        with _workspace() as workspace:
            recap_path = workspace / "docs" / "bootcamp_recap.md"
            recap_path.parent.mkdir(parents=True, exist_ok=True)
            original_bytes = recap_content.encode("utf-8")
            recap_path.write_bytes(original_bytes)

            _write_pending_question(workspace, question_text)
            assert _run_record_question() == 0
            assert _run_record_answer(answer_text) == 0

            assert recap_path.read_bytes() == original_bytes, (
                "capture must not overwrite or modify docs/bootcamp_recap.md"
            )


# ---------------------------------------------------------------------------
# Additional strategies + helpers for Properties 7, 8 (added by task 5)
# ---------------------------------------------------------------------------
#
# Property 7 observes the *real-Q&A rendering path*: it durably captures a
# sequence of question/answer exchanges through ``log_qa_event.py`` (exactly the
# events the command-backed hook will write), then renders them two ways and
# pins the observed baseline:
#
#   1. ``generate_transcript.build_model`` — the pairing/ordering engine that
#      groups durably captured Q&A into ordered pairs, each answer paired to its
#      own question by ``question_id`` in ascending ask order.
#   2. ``completion_artifacts.render_recap_section`` /
#      ``parse_recap_sections`` — the Consolidated_Log real-Q&A renderer, whose
#      ``### Questions & Responses`` round-trip must preserve those same ordered
#      pairs.
#
# Property 8 asserts the stdlib-only constraint by statically scanning the
# capture/validation scripts' imports.

# Alphabet for Q&A bodies: letters, digits, and a few punctuation marks, but no
# newlines or leading/trailing whitespace after the ``.map(str.strip)`` below, so
# what the helper stores (it strips question/answer text) compares exactly to
# what was generated. This keeps the rendering observation about *ordering and
# pairing*, not about whitespace normalization.
_QA_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 .,?!"
)


def st_qa_text() -> st.SearchStrategy[str]:
    """Non-empty, single-line Q&A text with no leading/trailing whitespace.

    The capture helper strips question and answer text before logging, so
    generating already-stripped, newline-free text lets Property 7 assert exact
    equality of the rendered pairs without modeling whitespace handling.

    Returns:
        A Hypothesis strategy producing stripped, non-empty text of length 1-60.
    """
    return (
        st.text(alphabet=_QA_ALPHABET, min_size=1, max_size=60)
        .map(str.strip)
        .filter(bool)
    )


def st_qa_exchanges() -> st.SearchStrategy[list[tuple[str, str]]]:
    """A sequence of ``(question, answer)`` exchanges for one module.

    Each exchange is a distinct question paired with its answer; the list order
    is the ask order the durable capture will preserve.

    Returns:
        A Hypothesis strategy producing 1-6 ``(question, answer)`` pairs.
    """
    return st.lists(
        st.tuples(st_qa_text(), st_qa_text()),
        min_size=1,
        max_size=6,
    )


def _durably_capture_exchanges(
    workspace: Path, exchanges: list[tuple[str, str]]
) -> None:
    """Durably capture each ``(question, answer)`` exchange via ``log_qa_event``.

    Mirrors the command-backed Q&A cadence: for each exchange the pending
    question marker is written, ``record-question`` logs the question, then
    ``record-answer`` logs the answer paired to it and clears the sidecar. The
    result is a ``config/session_log.jsonl`` holding the durably captured Q&A in
    ask order.

    Args:
        workspace: The workspace root (current working directory).
        exchanges: The ordered ``(question, answer)`` pairs to capture.
    """
    for question_text, answer_text in exchanges:
        _write_pending_question(workspace, question_text)
        assert _run_record_question() == 0
        assert _run_record_answer(answer_text) == 0


# ---------------------------------------------------------------------------
# Property 7 - Preservation: Real-Q&A Rendering Unchanged
# ---------------------------------------------------------------------------


class TestRealQARenderingPreservation:
    """Durably captured Q&A renders as the same ordered, paired real exchanges.

    **Validates: Requirements 3.1**

    Observed baseline: when a module's Q&A was durably captured (as the
    command-backed hook will capture it), the real-Q&A renderer pairs each
    answer to its own question by ``question_id`` and emits the pairs in
    ascending ask order — no placeholder text. These tests capture that baseline
    across both the ``generate_transcript`` pairing engine and the
    ``completion_artifacts`` Consolidated_Log real-Q&A round-trip, so the fix
    (which only adds durability + validation) must leave real-Q&A rendering
    exactly as it is.
    """

    @given(exchanges=st_qa_exchanges())
    def test_build_model_pairs_in_ascending_ask_order(
        self, exchanges: list[tuple[str, str]]
    ) -> None:
        """Each answer pairs to its own question, pairs stay in ask order."""
        with _workspace() as workspace:
            _durably_capture_exchanges(workspace, exchanges)

            events = generate_transcript.read_events(_SESSION_LOG)
            model = generate_transcript.build_model(events)

            # Every exchange is a real, answered pair — no orphans, no gaps.
            assert model.question_count == len(exchanges)
            assert model.answered_count == len(exchanges)
            assert len(model.pairs) == len(exchanges)
            assert model.orphan_answers == []

            # Pairs render in ascending ask order, each response paired to its
            # own question id, with the real captured text (no placeholder).
            expected_questions = [q for q, _ in exchanges]
            expected_answers = [a for _, a in exchanges]
            assert [p.question_text for p in model.pairs] == expected_questions
            assert [p.answer_text for p in model.pairs] == expected_answers
            for pair in model.pairs:
                assert pair.answer_text is not None
                assert pair.question_id  # answer is paired by this id

            # Ask timestamps are non-decreasing (ascending ask order).
            timestamps = [p.q_timestamp for p in model.pairs]
            assert timestamps == sorted(timestamps)

    @given(exchanges=st_qa_exchanges())
    def test_recap_section_round_trip_preserves_real_pairs(
        self, exchanges: list[tuple[str, str]]
    ) -> None:
        """completion_artifacts renders/parses the real Q&A pairs unchanged.

        Feeds the durably captured, ordered pairs through the Consolidated_Log
        real-Q&A renderer (``render_recap_section``) and back
        (``parse_recap_sections``); the ``### Questions & Responses`` pairs must
        survive byte-stably in the same ascending ask order.
        """
        with _workspace() as workspace:
            _durably_capture_exchanges(workspace, exchanges)
            events = generate_transcript.read_events(_SESSION_LOG)
            model = generate_transcript.build_model(events)
            pairs = [(p.question_text, p.answer_text or "") for p in model.pairs]

            section = completion_artifacts.ParsedRecapSection(
                module_number=1,
                module_name="Test Module",
                timestamp="",
                information_shared=[],
                questions_responses=pairs,
                actions_taken=[],
                duration=None,
                journal=None,
            )
            rendered = completion_artifacts.render_recap_section(section)
            reparsed = completion_artifacts.parse_recap_sections(rendered)

            assert len(reparsed) == 1
            assert reparsed[0].questions_responses == pairs


# ---------------------------------------------------------------------------
# Property 8 - Preservation: Standard Library Only
# ---------------------------------------------------------------------------

# Scripts whose imports this property scans. ``validate_qa_capture.py`` does not
# exist on the unfixed code; it is checked conditionally (see below) so this
# property passes now and also covers the new file once the fix adds it.
_CAPTURE_SCRIPTS = ("log_qa_event.py", "validate_qa_capture.py")


def _local_script_modules() -> set[str]:
    """Return the importable module names of sibling scripts in ``scripts/``.

    These are the repo's own stdlib-only helpers (e.g. ``session_logger``,
    ``generate_transcript``); importing one is not a third-party dependency.

    Returns:
        The set of ``.py`` file stems in the scripts directory.
    """
    scripts_dir = Path(_SCRIPTS_DIR)
    return {path.stem for path in scripts_dir.glob("*.py")}


def _top_level_imports(source_path: Path) -> set[str]:
    """Return the top-level module names imported by a Python source file.

    Parses the file with ``ast`` and collects the first dotted component of each
    ``import x.y`` / ``from x.y import z`` statement (absolute imports only;
    relative imports carry no third-party dependency).

    Args:
        source_path: Path to the Python source file to scan.

    Returns:
        The set of top-level imported module names.
    """
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


class TestStdlibOnlyPreservation:
    """The Q&A capture/validation scripts import only the standard library.

    **Validates: Requirements 3.6**

    Every module imported by ``log_qa_event.py`` (and, once it exists,
    ``validate_qa_capture.py``) must be either a Python 3.11+ standard-library
    module (``sys.stdlib_module_names``) or one of the repo's own sibling
    scripts — never a third-party (pip) dependency. ``validate_qa_capture.py``
    does not exist on the unfixed code, so it is scanned only when present: the
    property therefore passes now and will also cover the new file after the
    fix adds it.
    """

    def test_capture_scripts_import_only_stdlib_or_local(self) -> None:
        """No capture/validation script introduces a third-party import."""
        allowed = set(sys.stdlib_module_names) | _local_script_modules()
        scripts_dir = Path(_SCRIPTS_DIR)

        scanned: list[str] = []
        for script_name in _CAPTURE_SCRIPTS:
            script_path = scripts_dir / script_name
            if not script_path.is_file():
                # validate_qa_capture.py is absent on unfixed code — skip it
                # gracefully; it will be covered once the fix creates it.
                continue
            scanned.append(script_name)
            imported = _top_level_imports(script_path)
            third_party = sorted(imported - allowed)
            assert not third_party, (
                f"{script_name} must import only the Python 3.11+ standard "
                f"library (or sibling scripts); found third-party imports: "
                f"{third_party}"
            )

        # ``log_qa_event.py`` always exists and must always be scanned.
        assert "log_qa_event.py" in scanned, (
            "log_qa_event.py must be present and scanned for the stdlib-only "
            "constraint"
        )
