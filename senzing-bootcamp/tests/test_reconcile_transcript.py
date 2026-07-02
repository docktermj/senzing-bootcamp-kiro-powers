"""Property tests for the transcript reconciliation pass.

Feature: transcript-reconciliation

This module is self-contained: it defines the synthetic, PII-free ``st_*``
strategies (``st_recap_document`` and ``st_session_log``) used across the
reconciliation property tests and validates Property 1 — that the two
source-counting functions in ``reconcile_transcript`` return exactly the known
per-module tallies encoded by the generated inputs.

The recap markdown is rendered with the canonical ``format_qr_section``
formatter so it round-trips through ``generate_recap_pdf.parse_recap_markdown``,
and the session log is generated with a known per-module ``question``-event
count plus interspersed malformed/blank lines that the tolerant reader must
skip.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf  # noqa: E402
import reconcile_transcript  # noqa: E402
from recap_pdf_render import format_qr_section  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic input models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModuleSpec:
    """One module's synthetic QR pairs for a generated recap.

    Attributes:
        module: The (distinct) module number.
        pairs: Ordered ``(question, response)`` pairs. All questions are
            substantive, so ``format_qr_section`` keeps every pair.
    """

    module: int
    pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RecapSpec:
    """A synthetic recap: a set of modules each with known QR pairs."""

    modules: tuple[ModuleSpec, ...]


@dataclass(frozen=True)
class SessionLog:
    """A generated session log plus its known per-module question tally.

    Attributes:
        text: The raw JSONL log content (with interspersed malformed/blank
            lines that the tolerant reader must skip).
        expected: The exact per-module count of ``question`` events, omitting
            modules with zero logged questions (mirroring
            ``count_logged_questions``).
    """

    text: str
    expected: dict[int, int]


# Malformed / non-question lines the tolerant reader must skip. None of these is
# a valid ``question`` completion event, so none contributes to the tally.
_NOISE_LINES: tuple[str, ...] = (
    "",
    "   ",
    "not json at all",
    "{broken json",
    "[1, 2, 3]",
    "42",
    "null",
    '{"foo": "bar"}',
    '{"event_type": "action", "module": 2, "data": {}}',
    '{"event_type": "module_start", "module": 1}',
)

# Synthetic, PII-free text: letters, digits, and spaces only. This alphabet
# excludes the ``*`` used by the ``- **Q:**`` / ``- **R:**`` markers and any
# newline, so rendered pairs round-trip through the recap parser with an exact
# count.
_SAFE_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 ",
    min_size=1,
    max_size=40,
)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


def st_qr_text() -> st.SearchStrategy[str]:
    """A substantive, single-line, PII-free question or response string."""
    return _SAFE_TEXT.filter(lambda text: bool(text.strip()))


@composite
def st_recap_document(draw) -> RecapSpec:
    """Draw a synthetic recap with distinct modules and known QR-pair counts.

    Each module carries 0..4 substantive ``(question, response)`` pairs. Module
    numbers are distinct so each module's tally is unambiguous, and every pair's
    question is substantive so ``format_qr_section`` keeps it — making the
    rendered recap round-trip to exactly these per-module counts.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`RecapSpec` describing the synthetic recap.
    """
    module_numbers = draw(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=0,
            max_size=5,
            unique=True,
        )
    )
    modules: list[ModuleSpec] = []
    for number in module_numbers:
        pairs = draw(
            st.lists(
                st.tuples(st_qr_text(), st_qr_text()),
                min_size=0,
                max_size=4,
            )
        )
        modules.append(ModuleSpec(module=number, pairs=tuple(pairs)))
    return RecapSpec(modules=tuple(modules))


@composite
def st_session_log(draw, recap: RecapSpec) -> SessionLog:
    """Draw a session log logging a per-module subset of the recap's questions.

    For each recap module, a count ``k`` in ``0..len(pairs)`` of ``question``
    events is emitted (optionally each followed by its non-counted ``answer``
    event), and a handful of malformed/blank noise lines are interspersed. The
    resulting per-module ``question`` tally is recorded in ``expected`` so the
    test can assert ``count_logged_questions`` reproduces it exactly.

    Args:
        draw: The Hypothesis draw callable.
        recap: The recap whose questions may be logged.

    Returns:
        A :class:`SessionLog` with the raw JSONL text and its known tally.
    """
    expected: dict[int, int] = {}
    valid_lines: list[str] = []

    for module_spec in recap.modules:
        max_q = len(module_spec.pairs)
        k = draw(st.integers(min_value=0, max_value=max_q))
        if k > 0:
            expected[module_spec.module] = k
        for i in range(k):
            question_text, response_text = module_spec.pairs[i]
            qid = f"q{module_spec.module}_{i}"
            valid_lines.append(
                json.dumps(
                    {
                        "event_type": "question",
                        "module": module_spec.module,
                        "timestamp": f"2024-01-01T00:00:{i:02d}",
                        "data": {"text": question_text, "question_id": qid},
                    }
                )
            )
            # Optionally log the paired answer — it must NOT be counted.
            if draw(st.booleans()):
                valid_lines.append(
                    json.dumps(
                        {
                            "event_type": "answer",
                            "module": module_spec.module,
                            "timestamp": f"2024-01-01T00:00:{i:02d}",
                            "data": {"text": response_text, "question_id": qid},
                        }
                    )
                )

    noise = draw(st.lists(st.sampled_from(_NOISE_LINES), min_size=0, max_size=6))
    all_lines = draw(st.permutations(valid_lines + noise))
    text = "\n".join(all_lines) + "\n"
    return SessionLog(text=text, expected=expected)


# ---------------------------------------------------------------------------
# Rendering / expectation helpers
# ---------------------------------------------------------------------------


def render_recap_markdown(recap: RecapSpec) -> str:
    """Render a :class:`RecapSpec` to recap Markdown (Paired_Schema QR sections).

    Args:
        recap: The synthetic recap to render.

    Returns:
        Markdown text parseable by ``generate_recap_pdf.parse_recap_markdown``.
    """
    lines: list[str] = [
        "# Senzing Bootcamp Recap",
        "",
        "**Bootcamper:** Bootcamper",
        "**Started:** 2024-01-01",
        "**Total Duration:** 1h",
        "",
        "---",
        "",
    ]
    for module_spec in recap.modules:
        lines.append(
            f"## Module {module_spec.module}: Module {module_spec.module}"
            f" \u2014 2024-01-01T00:00:00"
        )
        lines.append("")
        lines.append(
            format_qr_section([(q, r) for q, r in module_spec.pairs])
        )
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def expected_recap_counts(recap: RecapSpec) -> dict[int, int]:
    """Return the per-module QR-pair tally, omitting modules with zero pairs.

    Mirrors ``count_recap_pairs``, which excludes modules contributing no pairs.

    Args:
        recap: The synthetic recap.

    Returns:
        A mapping of module number to its non-zero QR-pair count.
    """
    return {
        module_spec.module: len(module_spec.pairs)
        for module_spec in recap.modules
        if module_spec.pairs
    }


# ---------------------------------------------------------------------------
# Property 1: Accurate per-module counts
# ---------------------------------------------------------------------------


class TestAccurateCounts:
    """Validates: Requirements 1.1."""

    # Feature: transcript-reconciliation, Property 1: Accurate per-module counts
    # — For any generated recap with a known number of QR pairs per module and
    # any generated session log with a known number of `question` events per
    # module (including interspersed malformed or blank lines that must be
    # skipped), `count_recap_pairs` and `count_logged_questions` return exactly
    # those per-module tallies.
    #
    # Validates: Requirements 1.1
    @given(data=st.data())
    def test_counts_match_known_tallies(self, data: st.DataObject) -> None:
        recap = data.draw(st_recap_document())
        log = data.draw(st_session_log(recap))

        # count_recap_pairs reproduces the known per-module QR-pair tally.
        recap_doc = generate_recap_pdf.parse_recap_markdown(
            render_recap_markdown(recap)
        )
        assert reconcile_transcript.count_recap_pairs(recap_doc) == (
            expected_recap_counts(recap)
        )

        # count_logged_questions reproduces the known per-module question tally,
        # skipping the interspersed malformed/blank/non-question lines.
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            Path(path).write_text(log.text, encoding="utf-8")
            assert reconcile_transcript.count_logged_questions(path) == (
                log.expected
            )
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Property 2: Plan equals the per-module deficit
# ---------------------------------------------------------------------------


class TestPlanEqualsDeficit:
    """Validates: Requirements 1.2, 1.3."""

    # Feature: transcript-reconciliation, Property 2: Plan equals the per-module
    # deficit — For any pair of per-module logged-question counts and recap
    # QR-pair counts, `build_plan` produces a plan whose total missing pairs
    # equals `sum over modules of max(0, recap_pairs(N) - logged(N))`, and whose
    # `is_noop` flag is true if and only if that sum is zero.
    #
    # Validates: Requirements 1.2, 1.3
    @given(data=st.data())
    def test_plan_total_equals_summed_deficit(self, data: st.DataObject) -> None:
        recap = data.draw(st_recap_document())

        # A per-module logged-questions dict whose keys may or may not overlap
        # the recap's modules (extra modules must not affect the plan).
        logged = data.draw(
            st.dictionaries(
                keys=st.integers(min_value=1, max_value=15),
                values=st.integers(min_value=0, max_value=10),
                max_size=8,
            )
        )

        recap_doc = generate_recap_pdf.parse_recap_markdown(
            render_recap_markdown(recap)
        )
        recap_counts = expected_recap_counts(recap)

        expected_total = sum(
            max(0, recap_pairs - logged.get(module, 0))
            for module, recap_pairs in recap_counts.items()
        )

        plan = reconcile_transcript.build_plan(logged, recap_doc)

        actual_total = sum(len(s.missing_pairs) for s in plan.shortfalls)
        assert actual_total == expected_total
        assert plan.is_noop is (expected_total == 0)


# ---------------------------------------------------------------------------
# Property 5: A recap with no QR content is a no-op
# ---------------------------------------------------------------------------


@composite
def st_no_qr_recap_document(draw) -> RecapSpec:
    """Draw a synthetic recap that has NO QR content across all modules.

    Produces a recap whose modules (possibly zero of them) all carry empty
    ``pairs`` tuples. Rendered via ``render_recap_markdown`` and parsed with
    ``generate_recap_pdf.parse_recap_markdown``, such a recap contributes zero
    QR pairs, exercising the Requirement 3.3 no-op path.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`RecapSpec` whose every module has zero QR pairs (and which may
        have no modules at all).
    """
    module_numbers = draw(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=0,
            max_size=5,
            unique=True,
        )
    )
    modules = tuple(ModuleSpec(module=number, pairs=()) for number in module_numbers)
    return RecapSpec(modules=modules)


def st_logged_counts() -> st.SearchStrategy[dict[int, int]]:
    """An arbitrary per-module logged-question tally (possibly empty)."""
    return st.dictionaries(
        keys=st.integers(min_value=1, max_value=11),
        values=st.integers(min_value=0, max_value=10),
        max_size=11,
    )


class TestNoQrContentNoop:
    """Validates: Requirements 3.3."""

    # Feature: transcript-reconciliation, Property 5: A recap with no QR content
    # is a no-op — For any recap that contains no `### Questions & Responses`
    # content across all modules, the Reconciliation_Pass reports `recap_has_qr`
    # false, makes no changes to the session log, and thereby preserves the
    # existing `generate_transcript.py` behavior.
    #
    # Validates: Requirements 3.3
    @given(recap=st_no_qr_recap_document(), logged=st_logged_counts())
    def test_no_qr_recap_yields_noop_plan(
        self, recap: RecapSpec, logged: dict[int, int]
    ) -> None:
        recap_doc = generate_recap_pdf.parse_recap_markdown(
            render_recap_markdown(recap)
        )
        # Sanity: the generated recap genuinely contributes zero QR pairs.
        assert expected_recap_counts(recap) == {}

        plan = reconcile_transcript.build_plan(logged, recap_doc)

        # A recap with no QR content: no captured content to reconcile.
        assert plan.recap_has_qr is False
        # No modules can be short of a source that has no pairs.
        assert plan.shortfalls == []
        # With zero total deficit the pass is a no-op.
        assert plan.is_noop is True


# ---------------------------------------------------------------------------
# Property 4: Backfilled events conform to the existing schema and pair correctly
# ---------------------------------------------------------------------------


class TestBackfillSchemaAndPairing:
    """Validates: Requirements 2.1, 2.4."""

    # Feature: transcript-reconciliation, Property 4: Backfilled events conform
    # to the existing schema and pair correctly — For any detected shortfall,
    # every event appended by the backfill is a valid `question` or `answer`
    # completion entry (as produced by `build_completion_entry`), and re-reading
    # the log with the existing `generate_transcript` reader pairs each
    # backfilled question to its answer via `question_id` — increasing the
    # answered-pair count by exactly the number of backfilled pairs.
    #
    # Validates: Requirements 2.1, 2.4
    @given(data=st.data())
    def test_backfill_schema_and_pairing(self, data: st.DataObject) -> None:
        recap = data.draw(st_recap_document())
        log = data.draw(st_session_log(recap))

        recap_doc = generate_recap_pdf.parse_recap_markdown(
            render_recap_markdown(recap)
        )

        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            # Start from the (possibly short/empty) generated log.
            Path(path).write_text(log.text, encoding="utf-8")

            # Snapshot the raw lines and answered-pair count before backfill.
            before_lines = Path(path).read_text(encoding="utf-8").splitlines()
            before_answered = reconcile_transcript.generate_transcript.build_model(
                reconcile_transcript.generate_transcript.read_events(path)
            ).answered_count

            # Build and apply the backfill plan against the current log.
            logged = reconcile_transcript.count_logged_questions(path)
            plan = reconcile_transcript.build_plan(logged, recap_doc)
            backfilled = reconcile_transcript.apply_plan(plan, path)

            # --- Schema conformance of the appended events (Req 2.4) ---
            after_lines = Path(path).read_text(encoding="utf-8").splitlines()
            new_lines = after_lines[len(before_lines):]

            # Each backfilled pair contributes exactly one question + one answer.
            assert len(new_lines) == 2 * backfilled

            question_events = 0
            answer_events = 0
            for raw in new_lines:
                event = json.loads(raw)
                assert isinstance(event, dict)
                assert event["event_type"] in {"question", "answer"}
                # Module is a valid integer identifier.
                assert isinstance(event["module"], int)
                # A completion entry always carries a timestamp string.
                assert isinstance(event["timestamp"], str)
                assert event["timestamp"]
                # Data carries the paired text + linking question_id.
                assert isinstance(event["data"], dict)
                assert isinstance(event["data"]["text"], str)
                assert isinstance(event["data"]["question_id"], str)
                assert event["data"]["question_id"]
                if event["event_type"] == "question":
                    question_events += 1
                else:
                    answer_events += 1

            # Every backfilled question has a matching backfilled answer.
            assert question_events == backfilled
            assert answer_events == backfilled

            # Each appended question_id links exactly one question to one answer.
            new_question_ids = [
                json.loads(raw)["data"]["question_id"]
                for raw in new_lines
                if json.loads(raw)["event_type"] == "question"
            ]
            new_answer_ids = [
                json.loads(raw)["data"]["question_id"]
                for raw in new_lines
                if json.loads(raw)["event_type"] == "answer"
            ]
            assert len(set(new_question_ids)) == backfilled
            assert sorted(new_question_ids) == sorted(new_answer_ids)

            # --- Pairing via the existing reader (Req 2.1) ---
            after_answered = reconcile_transcript.generate_transcript.build_model(
                reconcile_transcript.generate_transcript.read_events(path)
            ).answered_count

            # Re-reading with the existing reader pairs every backfilled
            # question to its answer, increasing the answered-pair count by
            # exactly the number of backfilled pairs.
            assert after_answered == before_answered + backfilled
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Property 3: Reconciliation is idempotent
# ---------------------------------------------------------------------------


class TestIdempotence:
    """Validates: Requirements 1.3."""

    # Feature: transcript-reconciliation, Property 3: Reconciliation is
    # idempotent — For any recap and session log, running the Reconciliation_Pass
    # and then running it a second time leaves the log identical to its state
    # after the first run, and the second run's plan is a no-op.
    #
    # Validates: Requirements 1.3
    @given(data=st.data())
    def test_second_run_is_a_noop(self, data: st.DataObject) -> None:
        recap = data.draw(st_recap_document())
        # Start from a possibly-short (including empty) generated log so the
        # first run may backfill; the second run must then be a no-op.
        log = data.draw(st_session_log(recap))

        recap_text = render_recap_markdown(recap)

        recap_fd, recap_path = tempfile.mkstemp(suffix=".md")
        os.close(recap_fd)
        log_fd, log_path = tempfile.mkstemp(suffix=".jsonl")
        os.close(log_fd)
        try:
            Path(recap_path).write_text(recap_text, encoding="utf-8")
            Path(log_path).write_text(log.text, encoding="utf-8")

            # First run: may backfill missing pairs from the recap.
            assert (
                reconcile_transcript.main(
                    ["--recap", recap_path, "--log", log_path]
                )
                == 0
            )
            after_first = Path(log_path).read_bytes()

            # Second run: must leave the log byte-for-byte identical.
            assert (
                reconcile_transcript.main(
                    ["--recap", recap_path, "--log", log_path]
                )
                == 0
            )
            after_second = Path(log_path).read_bytes()
            assert after_second == after_first

            # And the second run's plan is a no-op: the log now covers every
            # recap QR pair per module, so there is no remaining deficit.
            recap_doc = generate_recap_pdf.parse_recap_markdown(recap_text)
            logged = reconcile_transcript.count_logged_questions(log_path)
            plan = reconcile_transcript.build_plan(logged, recap_doc)
            assert plan.is_noop is True
        finally:
            os.unlink(recap_path)
            os.unlink(log_path)


# ---------------------------------------------------------------------------
# Property 8: Any malformed input warns and continues
# ---------------------------------------------------------------------------


# Malformed content fragments: invalid JSON, corrupt Markdown markers, and
# random-but-PII-free "bytes-as-text" junk. None of these is a valid recap or a
# valid session-log event, so feeding them to ``main`` exercises the tolerant,
# non-blocking error paths.
_MALFORMED_FRAGMENTS: tuple[str, ...] = (
    "",
    "   ",
    "\t\t",
    "not json at all",
    "{broken json",
    "}{",
    "[1, 2, 3",
    '{"event_type": ',
    "\x00\x01\x02 garbage bytes as text",
    "## Module oops \u2014 not a real header",
    "- **Q:** dangling question with no response",
    "- **R:** dangling response with no question",
    "<<<>>> %%% ??? corrupt markdown",
    "\ufffd\ufffd invalid unicode-ish",
    "############",
    '{"module": "not-an-int", "event_type": 12345}',
)


@composite
def st_malformed_content(draw) -> str:
    """Draw junk/garbage text: invalid JSON, corrupt Markdown, or random bytes.

    Assembles 0..8 fragments (a mix of curated malformed samples and free-form
    PII-free text) into a single blob. May be empty. Nothing it produces is a
    valid recap document or a valid ``question``/``answer`` completion event, so
    both the recap parser and the tolerant log reader must handle it without
    raising.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A malformed content string.
    """
    fragments = draw(
        st.lists(
            st.one_of(
                st.sampled_from(_MALFORMED_FRAGMENTS),
                st.text(max_size=60),
            ),
            min_size=0,
            max_size=8,
        )
    )
    return "\n".join(fragments)


class TestWarnAndContinue:
    """Validates: Requirements 3.2."""

    # Feature: transcript-reconciliation, Property 8: Any malformed input warns
    # and continues — For any malformed or unreadable recap or session log
    # (invalid JSON lines, corrupt Markdown, missing files),
    # `reconcile_transcript.main` never raises, returns to its caller, and
    # leaves the session log readable by the transcript renderer.
    #
    # Validates: Requirements 3.2
    @given(
        recap_content=st.one_of(st.none(), st_malformed_content()),
        log_content=st.one_of(st.none(), st_malformed_content()),
    )
    def test_malformed_input_never_raises_and_log_stays_readable(
        self, recap_content: str | None, log_content: str | None
    ) -> None:
        # ``None`` means the file is absent (a nonexistent path); a string means
        # the file exists with malformed content. This covers a missing recap, a
        # missing log, and any combination of malformed-but-present inputs.
        tmpdir = tempfile.mkdtemp()
        try:
            recap_path = os.path.join(tmpdir, "bootcamp_recap.md")
            log_path = os.path.join(tmpdir, "session_log.jsonl")

            if recap_content is not None:
                Path(recap_path).write_text(recap_content, encoding="utf-8")
            if log_content is not None:
                Path(log_path).write_text(log_content, encoding="utf-8")

            # main() must never raise: it catches all failures internally and
            # returns an int exit code (0 on clean/no-op, 1 on handled error).
            result = reconcile_transcript.main(
                ["--recap", recap_path, "--log", log_path]
            )
            assert isinstance(result, int)

            # The log must remain readable by the transcript renderer: the
            # tolerant reader consumes whatever is there without raising.
            events = list(
                reconcile_transcript.generate_transcript.read_events(log_path)
            )
            assert isinstance(events, list)
        finally:
            for path in (
                os.path.join(tmpdir, "bootcamp_recap.md"),
                os.path.join(tmpdir, "session_log.jsonl"),
            ):
                if os.path.exists(path):
                    os.unlink(path)
            os.rmdir(tmpdir)


# ---------------------------------------------------------------------------
# Example-based unit tests for main() behavior and shortfall detection
# ---------------------------------------------------------------------------


def _read_qa_events(log_path: str) -> list[dict]:
    """Read raw ``question``/``answer`` events from a JSONL log in file order.

    Args:
        log_path: Path to the JSONL session log.

    Returns:
        The parsed event dicts (question/answer only) in the order written.
    """
    events: list[dict] = []
    for raw in Path(log_path).read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        obj = json.loads(raw)
        if obj.get("event_type") in {"question", "answer"}:
            events.append(obj)
    return events


class TestMainBehavior:
    """Example-based coverage of main() and the shortfall/plan logic.

    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 3.2.
    """

    # A small fixed recap: module 3 (two pairs) declared before module 1 (one
    # pair) so the tests also confirm the plan/backfill orders by ascending
    # module number regardless of document order.
    _FIXED_RECAP = RecapSpec(
        modules=(
            ModuleSpec(
                module=3,
                pairs=(
                    ("What is entity resolution", "Resolving records to entities"),
                    ("What is a data source", "A labeled origin of records"),
                ),
            ),
            ModuleSpec(
                module=1,
                pairs=(("What is Senzing", "An entity resolution engine"),),
            ),
        )
    )

    def _parsed_fixed_recap(self) -> generate_recap_pdf.RecapDocument:
        """Parse the fixed recap fixture into a ``RecapDocument``."""
        return generate_recap_pdf.parse_recap_markdown(
            render_recap_markdown(self._FIXED_RECAP)
        )

    # --- Shortfall detection on hand-built logs (Req 1.1, 1.2, 1.3) ---

    def test_consistent_log_is_noop(self) -> None:
        """A log matching the recap counts yields an idempotent no-op plan."""
        recap_doc = self._parsed_fixed_recap()
        # Recap has module 3 -> 2 pairs, module 1 -> 1 pair.
        logged = {3: 2, 1: 1}

        plan = reconcile_transcript.build_plan(logged, recap_doc)

        assert plan.recap_has_qr is True
        assert plan.is_noop is True
        assert plan.shortfalls == []

    def test_short_log_detects_shortfall(self) -> None:
        """An under-logged log produces the exact missing pairs per module."""
        recap_doc = self._parsed_fixed_recap()
        # Module 3 logged 1 of 2 (deficit 1); module 1 logged 0 of 1 (deficit 1).
        logged = {3: 1}

        plan = reconcile_transcript.build_plan(logged, recap_doc)

        assert plan.recap_has_qr is True
        assert plan.is_noop is False
        # Shortfalls are ordered by ascending module number.
        assert [s.module for s in plan.shortfalls] == [1, 3]

        module1 = plan.shortfalls[0]
        assert module1.missing_pairs == [
            ("What is Senzing", "An entity resolution engine")
        ]

        # Only the trailing (uncovered) pair of module 3 is missing.
        module3 = plan.shortfalls[1]
        assert module3.missing_pairs == [
            ("What is a data source", "A labeled origin of records")
        ]

    def test_over_logged_module_is_noop(self) -> None:
        """A module logged more than the recap captured is never a shortfall."""
        recap_doc = self._parsed_fixed_recap()
        # More logged questions than recap pairs in every module.
        logged = {3: 5, 1: 4}

        plan = reconcile_transcript.build_plan(logged, recap_doc)

        assert plan.is_noop is True
        assert plan.shortfalls == []

    # --- Backfill from a fixed recap: exact content + ordering (Req 2.1) ---

    def test_main_backfills_empty_log_in_module_order(self, tmp_path) -> None:
        """main() backfills an empty log with exact Q/A text in module order."""
        recap_path = tmp_path / "bootcamp_recap.md"
        recap_path.write_text(
            render_recap_markdown(self._FIXED_RECAP), encoding="utf-8"
        )
        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")

        rc = reconcile_transcript.main(
            ["--recap", str(recap_path), "--log", str(log_path)]
        )

        assert rc == 0

        events = _read_qa_events(str(log_path))
        # Three pairs total => six events, question-then-answer, module order.
        summary = [
            (e["event_type"], e["module"], e["data"]["text"]) for e in events
        ]
        assert summary == [
            ("question", 1, "What is Senzing"),
            ("answer", 1, "An entity resolution engine"),
            ("question", 3, "What is entity resolution"),
            ("answer", 3, "Resolving records to entities"),
            ("question", 3, "What is a data source"),
            ("answer", 3, "A labeled origin of records"),
        ]

        # Each backfilled question is linked to its answer by a shared id.
        for i in range(0, len(events), 2):
            q, a = events[i], events[i + 1]
            assert q["data"]["question_id"] == a["data"]["question_id"]

    # --- Idempotent no-op on a second run (Req 1.3) ---

    def test_main_is_idempotent(self, tmp_path) -> None:
        """A second main() run appends nothing to an already-reconciled log."""
        recap_path = tmp_path / "bootcamp_recap.md"
        recap_path.write_text(
            render_recap_markdown(self._FIXED_RECAP), encoding="utf-8"
        )
        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")

        argv = ["--recap", str(recap_path), "--log", str(log_path)]

        assert reconcile_transcript.main(argv) == 0
        after_first = log_path.read_text(encoding="utf-8")

        assert reconcile_transcript.main(argv) == 0
        after_second = log_path.read_text(encoding="utf-8")

        # The second run detects no shortfall and writes nothing new.
        assert after_second == after_first

    # --- Warn-and-continue on a missing recap file (Req 3.2 / 3.3) ---

    def test_main_missing_recap_warns_and_continues(
        self, tmp_path, capsys
    ) -> None:
        """A nonexistent recap path warns, writes nothing, and returns 0."""
        recap_path = tmp_path / "does_not_exist.md"
        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")

        rc = reconcile_transcript.main(
            ["--recap", str(recap_path), "--log", str(log_path)]
        )

        # Missing recap is treated as a no-op (existing behavior preserved).
        assert rc == 0
        captured = capsys.readouterr()
        assert "reconcile_transcript" in captured.err
        # No exception escaped and the log was left untouched.
        assert log_path.read_text(encoding="utf-8") == ""

    # --- Warn-and-continue on an OS/permission (write) error (Req 3.2) ---

    def test_main_write_error_warns_and_continues(
        self, tmp_path, capsys, monkeypatch
    ) -> None:
        """A write failure during backfill warns and does not raise."""
        recap_path = tmp_path / "bootcamp_recap.md"
        recap_path.write_text(
            render_recap_markdown(self._FIXED_RECAP), encoding="utf-8"
        )
        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")

        def _boom(*_args, **_kwargs):
            raise OSError("simulated permission denied")

        # Simulate an OS/permission error at the write boundary.
        monkeypatch.setattr(
            reconcile_transcript.session_logger,
            "append_completion_entry",
            _boom,
        )

        # main() must catch the failure internally rather than propagate it.
        rc = reconcile_transcript.main(
            ["--recap", str(recap_path), "--log", str(log_path)]
        )

        # Internally handled error path returns 1 (non-blocking by contract).
        assert rc == 1
        captured = capsys.readouterr()
        assert "reconcile_transcript" in captured.err


# ---------------------------------------------------------------------------
# End-to-end integration: reconcile a real recap into a real log, then render
# ---------------------------------------------------------------------------


class TestEndToEndReconcileAndRender:
    """End-to-end wiring of reconcile + render against a temp workspace.

    Exercises the real recap parser, real ``session_logger`` writers, the real
    ``reconcile_transcript`` pass, and the real ``generate_transcript`` renderer
    together: seed a recap and an empty log, reconcile, render, and assert the
    resulting ``bootcamp_transcript.md`` contains the recap's Q&A grouped by
    module in ascending module order. Fixtures are synthetic and PII-free.

    Validates: Requirements 4.2, 5.1, 5.2.
    """

    # A small fixed, synthetic recap. Modules are declared OUT of order
    # (module 2 before module 1 before module 4) so the test confirms the
    # rendered transcript groups modules in ascending numeric order regardless
    # of document order.
    _RECAP = RecapSpec(
        modules=(
            ModuleSpec(
                module=2,
                pairs=(
                    ("How do I map a data source", "Use the mapping helper"),
                    ("What is a record id", "A unique key per record"),
                ),
            ),
            ModuleSpec(
                module=1,
                pairs=(("What is Senzing", "An entity resolution engine"),),
            ),
            ModuleSpec(
                module=4,
                pairs=(
                    ("How do I search entities", "Call the search endpoint"),
                ),
            ),
        )
    )

    def test_reconcile_then_render_groups_qa_by_module_in_order(
        self, tmp_path
    ) -> None:
        """Seed recap + empty log, reconcile, render, assert grouped Q&A."""
        import re

        # 1. Temp workspace with docs/ and config/ subdirs.
        docs_dir = tmp_path / "docs"
        config_dir = tmp_path / "config"
        docs_dir.mkdir()
        config_dir.mkdir()

        # 2. Seed the recap markdown and an empty session log.
        recap_path = docs_dir / "bootcamp_recap.md"
        recap_path.write_text(
            render_recap_markdown(self._RECAP), encoding="utf-8"
        )
        log_path = config_dir / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")

        transcript_path = docs_dir / "bootcamp_transcript.md"

        # 3. Run the real reconciliation pass: backfills the empty log from the
        #    recap's QR pairs via the real session_logger writers.
        reconcile_rc = reconcile_transcript.main(
            ["--recap", str(recap_path), "--log", str(log_path)]
        )
        assert reconcile_rc == 0

        # 4. Render the transcript with the real generate_transcript. It accepts
        #    explicit --log/--output paths, so no CWD change is needed.
        render_rc = reconcile_transcript.generate_transcript.main(
            ["--log", str(log_path), "--output", str(transcript_path)]
        )
        assert render_rc == 0
        assert transcript_path.exists()

        transcript = transcript_path.read_text(encoding="utf-8")

        # 5a. Every recap question and response appears in the transcript.
        for module_spec in self._RECAP.modules:
            for question_text, response_text in module_spec.pairs:
                assert question_text in transcript
                assert response_text in transcript

        # 5b. Modules are grouped under ascending "## Module N" headings.
        heading_order = [
            int(number)
            for number in re.findall(
                r"^## Module (\d+)$", transcript, flags=re.MULTILINE
            )
        ]
        assert heading_order == [1, 2, 4]

        # 5c. Each question/response is grouped under its own module's heading
        #     (the text appears within that module's block, before the next
        #     module heading).
        for module_spec in self._RECAP.modules:
            heading = f"## Module {module_spec.module}"
            start = transcript.index(heading)
            next_starts = [
                transcript.index(f"## Module {other.module}")
                for other in self._RECAP.modules
                if transcript.index(f"## Module {other.module}") > start
            ]
            end = min(next_starts) if next_starts else len(transcript)
            block = transcript[start:end]
            for question_text, response_text in module_spec.pairs:
                assert question_text in block
                assert response_text in block


# ---------------------------------------------------------------------------
# Property 6: Reconciled transcript renders at least N pairs in module order
# ---------------------------------------------------------------------------

import re as _re  # noqa: E402


class TestReconciledRenderOrdering:
    """Validates: Requirements 2.1, 5.2."""

    # Feature: transcript-reconciliation, Property 6: Reconciled transcript
    # renders at least N pairs in module order — For any recap with N QR pairs
    # across modules, reconciling against an empty or short log and then
    # rendering the transcript yields at least N answered question/answer pairs
    # whose text matches the recap's QR pairs, presented grouped by module in
    # ascending module order.
    #
    # Validates: Requirements 2.1, 5.2
    @given(data=st.data())
    def test_reconciled_transcript_renders_pairs_in_module_order(
        self, data: st.DataObject
    ) -> None:
        recap = data.draw(st_recap_document())

        # Total QR pairs across all modules (the "N" of the property).
        n_pairs = sum(len(module_spec.pairs) for module_spec in recap.modules)

        # Multiset of the recap's (module, question, response) pairs.
        expected_pairs: dict[tuple[int, str, str], int] = {}
        for module_spec in recap.modules:
            for question, response in module_spec.pairs:
                key = (module_spec.module, question, response)
                expected_pairs[key] = expected_pairs.get(key, 0) + 1

        # Modules that carry at least one QR pair, in ascending order.
        expected_modules = sorted(
            module_spec.module
            for module_spec in recap.modules
            if module_spec.pairs
        )

        recap_text = render_recap_markdown(recap)

        recap_fd, recap_path = tempfile.mkstemp(suffix=".md")
        os.close(recap_fd)
        log_fd, log_path = tempfile.mkstemp(suffix=".jsonl")
        os.close(log_fd)
        out_fd, out_path = tempfile.mkstemp(suffix=".md")
        os.close(out_fd)
        try:
            Path(recap_path).write_text(recap_text, encoding="utf-8")
            # Start from an EMPTY log so every rendered pair originates from the
            # recap backfill, and the render's first-appearance module grouping
            # coincides with the reconciler's ascending-module backfill order.
            Path(log_path).write_text("", encoding="utf-8")

            # Reconcile: backfill the missing pairs from the recap.
            assert (
                reconcile_transcript.main(
                    ["--recap", recap_path, "--log", log_path]
                )
                == 0
            )

            # Inspect the reconciled log via the existing transcript reader.
            model = reconcile_transcript.generate_transcript.build_model(
                reconcile_transcript.generate_transcript.read_events(log_path)
            )

            # At least N answered question/answer pairs exist (Req 2.1, 5.2).
            assert model.answered_count >= n_pairs

            # Every recap QR pair appears among the answered pairs with matching
            # question/response text under its module (multiset containment).
            actual_pairs: dict[tuple[int, str, str], int] = {}
            for pair in model.pairs:
                if pair.answer_text is None:
                    continue
                key = (pair.module, pair.question_text, pair.answer_text)
                actual_pairs[key] = actual_pairs.get(key, 0) + 1
            for key, count in expected_pairs.items():
                assert actual_pairs.get(key, 0) >= count

            # The model's pairs are grouped by module in ascending module order.
            model_module_order: list[int] = []
            for pair in model.pairs:
                if pair.module not in model_module_order:
                    model_module_order.append(pair.module)
            assert model_module_order == sorted(model_module_order)
            assert model_module_order == expected_modules

            # Render the transcript and confirm the on-disk module headings are
            # emitted in ascending module order too (Req 5.2).
            assert (
                reconcile_transcript.generate_transcript.main(
                    ["--log", log_path, "--output", out_path]
                )
                == 0
            )
            if n_pairs > 0:
                rendered = Path(out_path).read_text(encoding="utf-8")
                heading_modules = [
                    int(match)
                    for match in _re.findall(
                        r"^## Module (\d+)$", rendered, flags=_re.MULTILINE
                    )
                ]
                assert heading_modules == expected_modules
                assert heading_modules == sorted(heading_modules)
        finally:
            for path in (recap_path, log_path, out_path):
                if os.path.exists(path):
                    os.unlink(path)


# ---------------------------------------------------------------------------
# Property 7: Secrets in reconciled content are redacted
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SecretResponse:
    """A synthetic response embedding a secret plus the raw secret value.

    Attributes:
        text: The single-line response text embedding ``secret`` inside a
            secret-looking carrier (connection string, bearer token, key/value
            pair, or a bare high-entropy key) that the existing transcript
            redaction detects.
        secret: The raw, synthetic secret substring that redaction must remove
            from the rendered transcript. It is PII-free and matches the
            renderer's redaction patterns.
    """

    text: str
    secret: str


@composite
def st_secret_token(draw) -> str:
    """Draw a synthetic, PII-free high-entropy secret token.

    The token is at least 32 characters of ASCII letters and digits and is
    guaranteed to contain both a letter and a digit, so it matches
    ``generate_transcript``'s generic high-entropy redaction rule in addition to
    whichever carrier (connection string / bearer / key=value) embeds it. It
    contains no whitespace, ``@``, ``/``, ``:``, or quote characters, so every
    carrier's redaction pattern consumes it whole.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A synthetic secret token string (length >= 32).
    """
    body = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            min_size=30,
            max_size=50,
        )
    )
    # Prefix guarantees length >= 32 and at least one letter + one digit.
    return f"a1{body}"


@composite
def st_secret_bearing_response(draw) -> SecretResponse:
    """Draw a single-line response embedding a secret-looking value.

    The secret is wrapped in one of several carriers the existing transcript
    redaction detects — a connection string with embedded credentials, a bearer
    token, a ``key=value`` secret, or a bare high-entropy key. The carrier text
    is synthetic and PII-free and stays on a single line (no ``*`` markers or
    newlines) so it round-trips through the recap QR formatter/parser unchanged.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`SecretResponse` carrying the response text and the raw secret.
    """
    token = draw(st_secret_token())
    carrier = draw(
        st.sampled_from(
            [
                f"The database connection is postgres://svcuser:{token}@db.internal:5432/appdb",
                f"Authenticate with the header Bearer {token} on each request",
                f"Set api_key={token} in the configuration file",
                f"The generated access key is {token}",
            ]
        )
    )
    return SecretResponse(text=carrier, secret=token)


class TestSecretRedaction:
    """Validates: Requirements 4.1."""

    # Feature: transcript-reconciliation, Property 7: Secrets in reconciled
    # content are redacted — For any recap response text containing a
    # secret-looking value (token, key, or connection string with credentials),
    # the reconciled-and-rendered transcript contains the redaction placeholder
    # and does not contain the original secret value.
    #
    # Validates: Requirements 4.1
    @given(data=st.data())
    def test_reconciled_transcript_redacts_secret_values(
        self, data: st.DataObject
    ) -> None:
        # A base recap of ordinary (secret-free) content, plus one injected
        # module whose QR pair carries a secret-bearing response. Injecting into
        # a module number not used by the base keeps the secret the ONLY secret
        # in the whole recap, so the absence assertion is unambiguous.
        base = data.draw(st_recap_document())
        secret_response = data.draw(st_secret_bearing_response())
        secret_question = data.draw(st_qr_text())

        used = {module_spec.module for module_spec in base.modules}
        free_module = next(n for n in range(1, 12) if n not in used)
        secret_module = ModuleSpec(
            module=free_module,
            pairs=((secret_question, secret_response.text),),
        )
        recap = RecapSpec(modules=base.modules + (secret_module,))

        recap_text = render_recap_markdown(recap)
        placeholder = reconcile_transcript.generate_transcript.REDACTION_PLACEHOLDER

        recap_fd, recap_path = tempfile.mkstemp(suffix=".md")
        os.close(recap_fd)
        log_fd, log_path = tempfile.mkstemp(suffix=".jsonl")
        os.close(log_fd)
        out_fd, out_path = tempfile.mkstemp(suffix=".md")
        os.close(out_fd)
        try:
            Path(recap_path).write_text(recap_text, encoding="utf-8")
            # Empty log so the secret-bearing pair is backfilled from the recap.
            Path(log_path).write_text("", encoding="utf-8")

            # Reconcile the empty log from the recap, then render the transcript.
            assert (
                reconcile_transcript.main(
                    ["--recap", recap_path, "--log", log_path]
                )
                == 0
            )
            assert (
                reconcile_transcript.generate_transcript.main(
                    ["--log", log_path, "--output", out_path]
                )
                == 0
            )

            rendered = Path(out_path).read_text(encoding="utf-8")

            # The reconciled-and-rendered transcript redacts the secret: the
            # placeholder is present and the raw secret value is gone (Req 4.1).
            assert placeholder in rendered
            assert secret_response.secret not in rendered
        finally:
            for path in (recap_path, log_path, out_path):
                if os.path.exists(path):
                    os.unlink(path)
