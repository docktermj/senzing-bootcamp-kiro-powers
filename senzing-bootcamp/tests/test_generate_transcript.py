"""Tests for the Q&A transcript renderer (``generate_transcript.py``).

Feature: bootcamp-qa-transcript

This module hosts both example tests and Hypothesis property-based tests for
the transcript renderer. Property test classes document which correctness
property and requirement they validate.

All fixtures use synthetic, PII-free content (Requirement 8.3); no
secret-looking strings are placed in the generated data.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts are not a package).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_transcript  # noqa: E402

# Event types the renderer treats as Q&A events.
_QA_EVENT_TYPES = {"question", "answer"}

# Event types that are explicitly NOT Q&A events (used to build non-Q&A lines).
_NON_QA_EVENT_TYPES = ["turn", "correction", "module_start", "module_complete", "action", "artifact"]


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_qa_event(draw) -> dict:
    """Generate a valid Q&A completion event dict.

    Produces a ``question`` or ``answer`` event matching the
    ``session_logger`` schema: an ``event_type`` in {"question", "answer"}, an
    integer ``module``, an ISO-like ``timestamp`` string, and a ``data`` dict
    carrying ``text`` and ``question_id``. Content is synthetic and PII-free.
    """
    event_type = draw(st.sampled_from(sorted(_QA_EVENT_TYPES)))
    module = draw(st.integers(min_value=0, max_value=11))
    timestamp = draw(
        st.builds(
            lambda h, m, s: f"2024-01-01T{h:02d}:{m:02d}:{s:02d}+00:00",
            st.integers(min_value=0, max_value=23),
            st.integers(min_value=0, max_value=59),
            st.integers(min_value=0, max_value=59),
        )
    )
    text = draw(st.text(min_size=1, max_size=50))
    question_id = draw(st.text(alphabet="0123456789abcdef", min_size=1, max_size=8))
    return {
        "event_type": event_type,
        "module": module,
        "timestamp": timestamp,
        "data": {"text": text, "question_id": question_id},
    }


def _is_qa_event_line(line: str) -> bool:
    """Return True if *line* parses to a Q&A event dict.

    Guards the malformed-line generator so it never accidentally emits a line
    that read_events would (correctly) treat as a valid Q&A event, which would
    otherwise corrupt the expected-results computation.
    """
    stripped = line.strip()
    if not stripped:
        return False
    try:
        obj = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return False
    return isinstance(obj, dict) and obj.get("event_type") in _QA_EVENT_TYPES


@st.composite
def st_malformed_line(draw) -> str:
    """Generate a single malformed or non-Q&A JSONL line (no newlines).

    Covers: blank lines, invalid JSON, JSON objects with a non-Q&A
    ``event_type``, JSON arrays, and JSON scalars. The result is filtered to
    guarantee it is never a valid Q&A event line.
    """

    def _blank() -> str:
        return draw(st.sampled_from(["", "   ", "\t"]))

    def _invalid_json() -> str:
        # Unquoted prose / broken braces never parse as a Q&A event dict.
        return draw(
            st.sampled_from(
                [
                    "not valid json",
                    "{broken: ",
                    "][",
                    "<<<>>>",
                    "auto-logged write operation",
                    "{'single': 'quotes'}",
                ]
            )
        )

    def _non_qa_object() -> str:
        return json.dumps(
            {
                "event_type": draw(st.sampled_from(_NON_QA_EVENT_TYPES)),
                "module": draw(st.integers(min_value=0, max_value=11)),
                "message": draw(st.text(max_size=30)),
            }
        )

    def _json_array() -> str:
        return json.dumps(draw(st.lists(st.integers(), max_size=4)))

    def _json_scalar() -> str:
        return json.dumps(
            draw(st.one_of(st.integers(), st.booleans(), st.none(), st.text(max_size=20)))
        )

    builder = draw(
        st.sampled_from([_blank, _invalid_json, _non_qa_object, _json_array, _json_scalar])
    )
    line = builder()
    # Defensive: never let a generated "malformed" line be a real Q&A event.
    if _is_qa_event_line(line):
        return "not valid json"
    return line


# An item is either a valid Q&A event or a malformed/non-Q&A line.
st_item = st.one_of(
    st_qa_event().map(lambda e: ("valid", e)),
    st_malformed_line().map(lambda s: ("malformed", s)),
)


# ---------------------------------------------------------------------------
# Property 4: Robust parsing
# ---------------------------------------------------------------------------


class TestRobustParsing:
    """Validates Property 4 (Robust parsing) for ``read_events``.

    For any interleaving of valid Q&A events with malformed/non-Q&A lines,
    ``read_events`` returns exactly the valid Q&A events in file order and never
    raises.

    Validates: Requirements 5.1
    """

    @settings(max_examples=20)
    @given(items=st.lists(st_item, max_size=15))
    def test_returns_exactly_valid_qa_events(self, items: list[tuple[str, object]]) -> None:
        # Build the file content and the independently-known expected result.
        lines: list[str] = []
        expected: list[dict] = []
        for kind, value in items:
            if kind == "valid":
                assert isinstance(value, dict)
                lines.append(json.dumps(value))
                expected.append(value)
            else:
                assert isinstance(value, str)
                lines.append(value)

        content = ("\n".join(lines) + "\n") if lines else ""

        fd, raw_path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        path = Path(raw_path)
        try:
            path.write_text(content, encoding="utf-8")

            # Never raises on any interleaving.
            result = generate_transcript.read_events(str(path))
        finally:
            path.unlink(missing_ok=True)

        # Exactly the valid Q&A events, in file order.
        assert result == expected
        # Count matches the number of valid events injected.
        assert len(result) == len(expected)
        # Every returned dict is a Q&A event.
        for event in result:
            assert isinstance(event, dict)
            assert event.get("event_type") in _QA_EVENT_TYPES


# ---------------------------------------------------------------------------
# Requirement 8: Privacy and Distribution Safety (secret redaction)
# ---------------------------------------------------------------------------


class TestRedaction:
    """Validates secret redaction in answer text via ``redact_secrets``.

    Covers token / Bearer / API-key patterns and connection strings with
    embedded credentials: the matched secret value is replaced with the
    ``[REDACTED]`` placeholder and the raw secret never survives into the
    output.

    All secret values below are SYNTHETIC and obviously fake (Requirement 8.3).

    Validates: Requirements 8.1, 8.2
    """

    def test_bearer_token_value_is_redacted(self) -> None:
        secret = "FAKEbearertoken1234567890notreal"
        answer = f"Use the header Authorization: Bearer {secret} to call the API."

        result = generate_transcript.redact_secrets(answer)

        assert generate_transcript.REDACTION_PLACEHOLDER in result
        assert secret not in result
        # The non-secret framing text is preserved.
        assert "Authorization: Bearer" in result

    def test_api_key_value_is_redacted(self) -> None:
        secret = "FAKEapikeyvalue0987654321dummy"
        answer = f"Set api_key={secret} in your config file."

        result = generate_transcript.redact_secrets(answer)

        assert generate_transcript.REDACTION_PLACEHOLDER in result
        assert secret not in result
        # The key name itself is kept; only the value is scrubbed.
        assert "api_key=" in result

    def test_connection_string_credentials_are_redacted(self) -> None:
        password = "FAKEsupersecret123"
        answer = (
            f"Connect with postgresql://user:{password}@host.example.com:5432/db "
            "for the loader."
        )

        result = generate_transcript.redact_secrets(answer)

        assert generate_transcript.REDACTION_PLACEHOLDER in result
        # The embedded credential must not survive.
        assert password not in result
        # Non-secret structure (scheme, user, host) is preserved.
        assert "postgresql://user:" in result
        assert "@host.example.com:5432/db" in result

    def test_clean_answer_is_unchanged(self) -> None:
        # An ordinary answer with no secret-looking values is returned as-is.
        answer = "Entity resolution links records that refer to the same real-world entity."

        result = generate_transcript.redact_secrets(answer)

        assert result == answer
        assert generate_transcript.REDACTION_PLACEHOLDER not in result

    def test_empty_answer_is_handled(self) -> None:
        assert generate_transcript.redact_secrets("") == ""


# ---------------------------------------------------------------------------
# Property 1: Pairing integrity
# ---------------------------------------------------------------------------


@st.composite
def st_paired_qa_events(draw) -> tuple[list[dict], dict[str, str]]:
    """Generate a question/answer event sequence with DISTINCT question ids.

    Builds a set of questions, each with a unique ``question_id``, then emits
    answer events for a subset of those ids. Distinct ids keep Property 1
    unambiguous: every answer maps to exactly one question.

    Returns:
        A tuple ``(events, answered)`` where ``events`` is the ordered list of
        question/answer event dicts and ``answered`` maps each answered
        ``question_id`` to its known answer text. Content is synthetic and
        PII-free.
    """
    # Draw a set of distinct question ids (hex strings of varying length).
    question_ids = draw(
        st.lists(
            st.text(alphabet="0123456789abcdef", min_size=1, max_size=10),
            min_size=0,
            max_size=8,
            unique=True,
        )
    )

    events: list[dict] = []
    answered: dict[str, str] = {}
    # A monotonically increasing counter ensures stable, ordered timestamps so
    # that questions precede their answers in the event sequence.
    clock = 0

    # One question event per distinct id.
    questions: list[dict] = []
    for qid in question_ids:
        module = draw(st.integers(min_value=0, max_value=11))
        q_text = draw(st.text(min_size=1, max_size=50))
        questions.append(
            {
                "event_type": "question",
                "module": module,
                "timestamp": f"2024-01-01T00:00:{clock:02d}+00:00",
                "data": {"text": q_text, "question_id": qid},
            }
        )
        clock += 1

    # Decide which ids get answered (a subset).
    answered_ids = draw(
        st.lists(st.sampled_from(question_ids), unique=True) if question_ids else st.just([])
    )

    answers: list[dict] = []
    for qid in answered_ids:
        a_text = draw(st.text(min_size=1, max_size=50))
        answered[qid] = a_text
        answers.append(
            {
                "event_type": "answer",
                "module": draw(st.integers(min_value=0, max_value=11)),
                "timestamp": f"2024-01-01T00:01:{clock:02d}+00:00",
                "data": {"text": a_text, "question_id": qid},
            }
        )
        clock += 1

    events = questions + answers
    return events, answered


class TestPairingIntegrity:
    """Validates Property 1 (Pairing integrity) for ``build_model``.

    For all sequences of question and answer events, every answered question (a
    question whose ``question_id`` also appears on an answer event) renders with
    exactly its paired answer text, and no answer is attached to a different
    question.

    Validates: Requirements 2.2, 4.5
    """

    @settings(max_examples=20)
    @given(case=st_paired_qa_events())
    def test_answered_questions_pair_with_their_own_answer(
        self, case: tuple[list[dict], dict[str, str]]
    ) -> None:
        events, answered = case

        model = generate_transcript.build_model(events)

        # Index pairs by question_id (ids are distinct in this strategy).
        pairs_by_id = {pair.question_id: pair for pair in model.pairs}

        # Every answered question carries exactly its own paired answer text.
        for qid, expected_text in answered.items():
            assert qid in pairs_by_id
            assert pairs_by_id[qid].answer_text == expected_text

        # No answer is attached to a different (unanswered) question, and no
        # answer_text leaks onto a question that was never answered.
        for pair in model.pairs:
            if pair.question_id in answered:
                assert pair.answer_text == answered[pair.question_id]
            else:
                assert pair.answer_text is None

        # With distinct ids and questions preceding answers, every answer pairs
        # cleanly: there are no orphan answers.
        assert model.orphan_answers == []
        # answered_count equals the number of distinct answered questions.
        assert model.answered_count == len(answered)

        # Optional render-level check (render_markdown is implemented in a later
        # task; guard against NotImplementedError to keep this test robust).
        try:
            rendered = generate_transcript.render_markdown(model, "2024-01-01T00:00:00+00:00")
        except NotImplementedError:
            pass
        else:
            for qid, expected_text in answered.items():
                assert expected_text in rendered


# ---------------------------------------------------------------------------
# Property 2: Order preservation
# ---------------------------------------------------------------------------


# A small pool of timestamps so collisions happen and the stable tie-break is
# exercised. Values are deliberately NOT in sorted-by-string order relative to
# their pool index so that file order and timestamp order can diverge.
_TIMESTAMP_POOL = [
    "2024-01-01T00:00:05+00:00",
    "2024-01-01T00:00:01+00:00",
    "2024-01-01T00:00:05+00:00",
    "2024-01-01T00:00:03+00:00",
    "2024-01-01T00:00:01+00:00",
]


@st.composite
def st_ordered_qa_events(draw) -> list[dict]:
    """Generate an event sequence with distinct question ids and varying ts.

    Produces a list of ``question`` events (each with a unique
    ``question_id``) whose timestamps are drawn from a small pool so that ties
    occur, deliberately including out-of-file-order timestamps. Answer events
    for a subset of those ids may be interspersed; the property under test only
    concerns question ordering. Content is synthetic and PII-free.

    Returns:
        The ordered (file-order) list of question/answer event dicts.
    """
    n = draw(st.integers(min_value=0, max_value=8))

    question_events: list[dict] = []
    for index in range(n):
        # Distinct, file-order-encoding question id keeps tie-break checkable.
        question_id = f"q{index:03d}"
        question_events.append(
            {
                "event_type": "question",
                "module": draw(st.integers(min_value=0, max_value=11)),
                "timestamp": draw(st.sampled_from(_TIMESTAMP_POOL)),
                "data": {
                    "text": draw(st.text(min_size=1, max_size=40)),
                    "question_id": question_id,
                },
            }
        )

    # Optionally intersperse answer events for a subset of question ids. These
    # must not affect question ordering.
    answer_events: list[dict] = []
    if question_events:
        answered_ids = draw(
            st.lists(
                st.sampled_from([q["data"]["question_id"] for q in question_events]),
                unique=True,
                max_size=len(question_events),
            )
        )
        for qid in answered_ids:
            answer_events.append(
                {
                    "event_type": "answer",
                    "module": draw(st.integers(min_value=0, max_value=11)),
                    "timestamp": draw(st.sampled_from(_TIMESTAMP_POOL)),
                    "data": {
                        "text": draw(st.text(min_size=1, max_size=40)),
                        "question_id": qid,
                    },
                }
            )

    # Questions followed by answers; relative file order within each group is
    # preserved so the stable tie-break is observable.
    events = question_events + answer_events
    return events


class TestOrderPreservation:
    """Validates Property 2 (Order preservation) for ``build_model``.

    For all event sequences, the rendered/model question order appears in
    non-decreasing ``timestamp`` order, with file order breaking ties -- i.e.
    the rendered order equals the stable timestamp order of the question
    events.

    Validates: Requirements 4.4, 5.2
    """

    @settings(max_examples=20)
    @given(events=st_ordered_qa_events())
    def test_question_order_equals_stable_timestamp_order(self, events: list[dict]) -> None:
        # Independently compute the expected order: take question events in
        # their original file order, then stable-sort by timestamp. Python's
        # ``sorted`` is stable, so equal timestamps keep file order.
        question_events = [e for e in events if e["event_type"] == "question"]
        expected_ids = [
            e["data"]["question_id"]
            for e in sorted(question_events, key=lambda e: e["timestamp"])
        ]

        model = generate_transcript.build_model(events)
        actual_ids = [pair.question_id for pair in model.pairs]

        # Rendered question order equals the stable timestamp order.
        assert actual_ids == expected_ids

        # Timestamps appear in non-decreasing order across consecutive pairs.
        for i in range(len(model.pairs) - 1):
            assert model.pairs[i].q_timestamp <= model.pairs[i + 1].q_timestamp


# ---------------------------------------------------------------------------
# Property 3: No content dropped / no fabrication
# ---------------------------------------------------------------------------


@st.composite
def st_mixed_qa_events(draw) -> tuple[list[dict], list[str], int, int]:
    """Generate a mixed question/answer sequence exercising matches and orphans.

    Builds questions with DISTINCT hex ``question_id`` values, then emits:
      * matched answers, each referencing a UNIQUE existing question id (so each
        pairs cleanly with its question), and
      * orphan answers, each referencing a fresh id that is guaranteed NOT to be
        among the question ids (so they stay genuinely unmatched).

    Question timestamps precede answer timestamps, so the stable sort in
    ``build_model`` lets every matched answer find its question. Orphan ids use
    a non-hex prefix (``orphan-``) so they can never collide with a hex
    question id. Content is synthetic and PII-free with no secret-like patterns.

    Returns:
        A tuple ``(events, question_ids, matched_count, orphan_count)`` where
        ``events`` is the ordered list of event dicts, ``question_ids`` is the
        list of distinct question ids, ``matched_count`` is the number of
        answers that should pair with a question, and ``orphan_count`` is the
        number of answers that should remain unmatched.
    """
    # Distinct hex question ids -> exactly one question event each.
    question_ids = draw(
        st.lists(
            st.text(alphabet="0123456789abcdef", min_size=1, max_size=10),
            min_size=0,
            max_size=8,
            unique=True,
        )
    )

    clock = 0
    questions: list[dict] = []
    for qid in question_ids:
        questions.append(
            {
                "event_type": "question",
                "module": draw(st.integers(min_value=0, max_value=11)),
                "timestamp": f"2024-01-01T00:00:{clock:02d}+00:00",
                "data": {
                    "text": draw(st.text(min_size=1, max_size=40)),
                    "question_id": qid,
                },
            }
        )
        clock += 1

    # Matched answers reference a UNIQUE subset of existing ids so each pairs
    # cleanly (no second answer for the same id, which would itself orphan).
    matched_ids = draw(
        st.lists(st.sampled_from(question_ids), unique=True) if question_ids else st.just([])
    )

    answers: list[dict] = []
    for qid in matched_ids:
        answers.append(
            {
                "event_type": "answer",
                "module": draw(st.integers(min_value=0, max_value=11)),
                "timestamp": f"2024-01-01T00:01:{clock:02d}+00:00",
                "data": {
                    "text": draw(st.text(min_size=1, max_size=40)),
                    "question_id": qid,
                },
            }
        )
        clock += 1

    # Orphan answers reference fresh ids that cannot match any question id.
    orphan_count = draw(st.integers(min_value=0, max_value=4))
    for index in range(orphan_count):
        answers.append(
            {
                "event_type": "answer",
                "module": draw(st.integers(min_value=0, max_value=11)),
                "timestamp": f"2024-01-01T00:02:{clock:02d}+00:00",
                "data": {
                    "text": draw(st.text(min_size=1, max_size=40)),
                    "question_id": f"orphan-{index}",
                },
            }
        )
        clock += 1

    events = questions + answers
    return events, question_ids, len(matched_ids), orphan_count


class TestNoContentDropped:
    """Validates Property 3 (No content dropped / no fabrication) for ``build_model``.

    For all event sequences, every question event yields a rendered question
    (answered or marked unanswered) and every answer event is rendered either as
    its question's answer or as an orphan -- no question or answer is silently
    discarded, and no ``question_id`` is invented for an unmatched answer.

    Validates: Requirements 2.5, 4.6, 5.4
    """

    @settings(max_examples=20)
    @given(case=st_mixed_qa_events())
    def test_no_question_or_answer_is_dropped_or_fabricated(
        self, case: tuple[list[dict], list[str], int, int]
    ) -> None:
        events, question_ids, matched_count, orphan_count = case

        question_id_set = set(question_ids)
        num_question_events = sum(1 for e in events if e["event_type"] == "question")
        num_answer_events = sum(1 for e in events if e["event_type"] == "answer")

        model = generate_transcript.build_model(events)

        # No question dropped: one pair per question event, and the rendered set
        # of pair ids is exactly the set of question event ids (distinct ids).
        assert len(model.pairs) == num_question_events
        assert {pair.question_id for pair in model.pairs} == question_id_set
        assert model.question_count == num_question_events

        # Answers conserved: matched (pairs with answer_text) + orphans equals
        # the total number of answer events -- nothing silently discarded.
        answered_pairs = sum(1 for pair in model.pairs if pair.answer_text is not None)
        assert answered_pairs + len(model.orphan_answers) == num_answer_events
        assert answered_pairs == matched_count
        assert len(model.orphan_answers) == orphan_count

        # No fabrication: every orphan answer references a question_id that is
        # genuinely absent from the question set (no id was invented to absorb
        # it, and it was not silently attached to an unrelated question).
        for event in model.orphan_answers:
            orphan_id = (event.get("data") or {}).get("question_id", "")
            assert orphan_id not in question_id_set

        # answered_count reflects exactly the paired questions.
        assert model.answered_count == answered_pairs

        # Render-level check: every question text appears verbatim (questions
        # are never redacted), each answer appears in its rendered (redacted)
        # form, unanswered questions are marked rather than omitted, and the
        # orphan section label shows whenever orphans exist.
        rendered = generate_transcript.render_markdown(model, "2024-01-01T00:00:00+00:00")
        for pair in model.pairs:
            assert pair.question_text in rendered
            if pair.answer_text is None:
                # The question is still rendered (marked unanswered, not omitted).
                assert "*(unanswered)*" in rendered
            else:
                assert generate_transcript.redact_secrets(pair.answer_text) in rendered
        if model.orphan_answers:
            assert "## Unmatched answers" in rendered
            for event in model.orphan_answers:
                orphan_text = (event.get("data") or {}).get("text", "")
                assert generate_transcript.redact_secrets(orphan_text) in rendered


# ---------------------------------------------------------------------------
# Example tests: render_markdown output format
# ---------------------------------------------------------------------------


# Fixed generation timestamp used by every example below (no clock dependence).
_GENERATED_AT = "2024-01-01T12:00:00+00:00"


def _question_event(question_id: str, module: int, text: str, timestamp: str) -> dict:
    """Build a synthetic ``question`` event matching the logger schema."""
    return {
        "event_type": "question",
        "module": module,
        "timestamp": timestamp,
        "data": {"text": text, "question_id": question_id},
    }


def _answer_event(question_id: str, module: int, text: str, timestamp: str) -> dict:
    """Build a synthetic ``answer`` event matching the logger schema."""
    return {
        "event_type": "answer",
        "module": module,
        "timestamp": timestamp,
        "data": {"text": text, "question_id": question_id},
    }


class TestRenderExamples:
    """Concrete example tests for ``render_markdown`` output format.

    These are illustrative, hand-built examples (no Hypothesis) that pin the
    exact rendered Markdown for representative sessions: a fully-answered
    two-question session grouped by module, an unanswered question marked with
    the ``*(unanswered)*`` marker, and an orphan answer rendered in the labeled
    ``## Unmatched answers`` section. All content is synthetic, PII-free, and
    contains no secret-like patterns, so it passes through ``redact_secrets``
    unchanged and assertions can match verbatim.

    Validates: Requirements 4.4, 4.5, 4.6, 5.4
    """

    def test_two_question_session_grouped_by_module_with_answers(self) -> None:
        # Two questions in different modules, each with a paired answer.
        q1_text = "What is entity resolution?"
        a1_text = "It links records that refer to the same real-world entity."
        q2_text = "How do you load data into Senzing?"
        a2_text = "Transform records to the generic mapping then add them."

        events = [
            _question_event("q1", 1, q1_text, "2024-01-01T00:00:00+00:00"),
            _answer_event("q1", 1, a1_text, "2024-01-01T00:00:10+00:00"),
            _question_event("q2", 2, q2_text, "2024-01-01T00:01:00+00:00"),
            _answer_event("q2", 2, a2_text, "2024-01-01T00:01:10+00:00"),
        ]

        model = generate_transcript.build_model(events)
        rendered = generate_transcript.render_markdown(model, _GENERATED_AT)

        # Title and metadata header reflect the totals (Req 4.4 header).
        assert "# Bootcamp Q&A Transcript" in rendered
        assert f"- **Generated at:** {_GENERATED_AT}" in rendered
        assert "- **Total questions:** 2" in rendered
        assert "- **Answered questions:** 2" in rendered

        # One heading per module, in first-appearance order (Req 4.4).
        assert "## Module 1" in rendered
        assert "## Module 2" in rendered
        assert rendered.index("## Module 1") < rendered.index("## Module 2")

        # Both questions and both answers render with the Q/A markers (Req 4.5).
        assert f"**Q:** {q1_text}" in rendered
        assert f"**A:** {a1_text}" in rendered
        assert f"**Q:** {q2_text}" in rendered
        assert f"**A:** {a2_text}" in rendered

        # Each answer renders beneath its own question.
        assert rendered.index(f"**Q:** {q1_text}") < rendered.index(f"**A:** {a1_text}")
        assert rendered.index(f"**Q:** {q2_text}") < rendered.index(f"**A:** {a2_text}")
        # Module 1's pair precedes Module 2's pair.
        assert rendered.index(f"**A:** {a1_text}") < rendered.index(f"**Q:** {q2_text}")

        # No orphan section is emitted when every answer pairs cleanly.
        assert "## Unmatched answers" not in rendered

    def test_two_questions_same_module_grouped_together(self) -> None:
        # Two questions in the SAME module render under a single heading.
        q1_text = "What data sources does Senzing support?"
        a1_text = "Any structured records mapped to the generic entity schema."
        q2_text = "Why use stable record ids?"
        a2_text = "They keep updates idempotent across reloads."

        events = [
            _question_event("a1", 1, q1_text, "2024-01-01T00:00:00+00:00"),
            _answer_event("a1", 1, a1_text, "2024-01-01T00:00:05+00:00"),
            _question_event("a2", 1, q2_text, "2024-01-01T00:00:10+00:00"),
            _answer_event("a2", 1, a2_text, "2024-01-01T00:00:15+00:00"),
        ]

        model = generate_transcript.build_model(events)
        rendered = generate_transcript.render_markdown(model, _GENERATED_AT)

        # Exactly one "## Module 1" heading covers both questions (Req 4.4).
        assert rendered.count("## Module 1") == 1
        assert "- **Total questions:** 2" in rendered
        assert "- **Answered questions:** 2" in rendered

        # Both Q/A pairs appear in question order (Req 4.5).
        assert f"**Q:** {q1_text}" in rendered
        assert f"**A:** {a1_text}" in rendered
        assert f"**Q:** {q2_text}" in rendered
        assert f"**A:** {a2_text}" in rendered
        assert rendered.index(f"**Q:** {q1_text}") < rendered.index(f"**Q:** {q2_text}")

    def test_unanswered_question_renders_with_marker(self) -> None:
        # A question with no matching answer is marked, not omitted (Req 4.6).
        q_text = "What is the difference between a record and an entity?"

        events = [
            _question_event("q1", 3, q_text, "2024-01-01T00:00:00+00:00"),
        ]

        model = generate_transcript.build_model(events)
        rendered = generate_transcript.render_markdown(model, _GENERATED_AT)

        # The question text is still rendered under its module heading.
        assert "## Module 3" in rendered
        assert f"**Q:** {q_text}" in rendered
        # And the unanswered marker appears in its answer slot.
        assert "**A:** *(unanswered)*" in rendered

        # Header totals reflect one question, zero answered.
        assert "- **Total questions:** 1" in rendered
        assert "- **Answered questions:** 0" in rendered

    def test_orphan_answer_renders_in_unmatched_section(self) -> None:
        # An answer whose question_id has no matching question is an orphan.
        orphan_text = "This answer references a question that is not in the log."

        events = [
            _answer_event("missing-q", 4, orphan_text, "2024-01-01T00:00:00+00:00"),
        ]

        model = generate_transcript.build_model(events)
        rendered = generate_transcript.render_markdown(model, _GENERATED_AT)

        # The labeled section heading appears (Req 5.4).
        assert "## Unmatched answers" in rendered
        # The orphan answer text renders within that section.
        assert f"**A:** {orphan_text}" in rendered
        assert rendered.index("## Unmatched answers") < rendered.index(
            f"**A:** {orphan_text}"
        )

        # No question events -> zero totals, and no module headings.
        assert "- **Total questions:** 0" in rendered
        assert "- **Answered questions:** 0" in rendered
        assert "## Module" not in rendered


# ---------------------------------------------------------------------------
# Requirement 7.3: Full regeneration overwrites stale content
# ---------------------------------------------------------------------------


class TestMainRegeneration:
    """Example tests for ``main`` full-regeneration behavior (Req 7.3).

    The renderer must regenerate ``docs/bootcamp_transcript.md`` from the
    current session log by full overwrite -- never appending to (or otherwise
    preserving) stale content from a prior run. Content is synthetic and
    PII-free.

    Validates: Requirements 7.3
    """

    def test_existing_transcript_is_overwritten_on_regeneration(self, tmp_path, capsys) -> None:
        # A valid two-event session: one question with its paired answer.
        q_text = "What is entity resolution?"
        a_text = "It links records that refer to the same real-world entity."
        events = [
            _question_event("q1", 1, q_text, "2024-01-01T00:00:00+00:00"),
            _answer_event("q1", 1, a_text, "2024-01-01T00:00:10+00:00"),
        ]

        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
        )

        # Pre-create the output file with stale content that must NOT survive.
        stale = "STALE CONTENT THAT MUST NOT SURVIVE"
        output_path = tmp_path / "bootcamp_transcript.md"
        output_path.write_text(stale + "\n", encoding="utf-8")

        exit_code = generate_transcript.main(
            ["--log", str(log_path), "--output", str(output_path)]
        )

        # Success exit code.
        assert exit_code == 0

        rendered = output_path.read_text(encoding="utf-8")
        # Stale content is gone -- regeneration overwrote, never appended.
        assert stale not in rendered
        # The freshly rendered transcript is present.
        assert "# Bootcamp Q&A Transcript" in rendered
        assert q_text in rendered
        assert a_text in rendered

        # A success message was printed to stdout.
        captured = capsys.readouterr()
        assert "Wrote transcript to" in captured.out


# ---------------------------------------------------------------------------
# Property 5: Empty-input safety
# ---------------------------------------------------------------------------


@st.composite
def st_empty_of_qa_log(draw) -> str:
    """Generate the full text of a log containing ZERO Q&A events.

    Produces either an entirely empty file or an arbitrary interleaving of
    malformed / non-Q&A lines (reusing ``st_malformed_line``). By construction
    none of the lines is a valid Q&A event, so ``read_events`` yields nothing.
    Content is synthetic and PII-free.

    Returns:
        The complete file content (possibly empty) to write to a temp log.
    """
    # Half the time, an entirely empty file; otherwise malformed/non-Q&A lines.
    if draw(st.booleans()):
        return ""
    lines = draw(st.lists(st_malformed_line(), max_size=12))
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


class TestEmptyInputSafety:
    """Validates Property 5 (Empty-input safety) for ``main``.

    For all logs with zero Q&A events (including a missing file), ``main``
    emits a warning to stderr and writes no misleading transcript file,
    returning 0. Content is synthetic and PII-free.

    Validates: Requirements 5.3, 7.3
    """

    @settings(max_examples=20)
    @given(content=st_empty_of_qa_log())
    def test_empty_of_qa_log_warns_and_writes_nothing(self, content: str) -> None:
        # Guard: the generated content must truly contain zero Q&A events.
        for line in content.splitlines():
            assert not _is_qa_event_line(line)

        # Unique temp paths per example; the output path must NOT pre-exist.
        fd, raw_log = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        log_path = Path(raw_log)
        out_dir = Path(tempfile.mkdtemp())
        out_path = out_dir / "bootcamp_transcript.md"

        # Capture stderr so we can assert the warning was emitted.
        captured_err = io.StringIO()
        old_stderr = sys.stderr
        try:
            log_path.write_text(content, encoding="utf-8")
            assert not out_path.exists()

            sys.stderr = captured_err
            try:
                exit_code = generate_transcript.main(
                    ["--log", str(log_path), "--output", str(out_path)]
                )
            finally:
                sys.stderr = old_stderr

            # Returns 0 even with no Q&A events.
            assert exit_code == 0
            # A warning was emitted to stderr.
            assert "no transcript written" in captured_err.getvalue().lower()
            # No misleading transcript file was created.
            assert not out_path.exists()
        finally:
            log_path.unlink(missing_ok=True)
            out_path.unlink(missing_ok=True)
            try:
                out_dir.rmdir()
            except OSError:
                pass

    def test_missing_log_file_warns_and_writes_nothing(self, tmp_path, capsys) -> None:
        # A --log path that does not exist at all.
        missing_log = tmp_path / "does_not_exist.jsonl"
        out_path = tmp_path / "bootcamp_transcript.md"
        assert not missing_log.exists()
        assert not out_path.exists()

        exit_code = generate_transcript.main(
            ["--log", str(missing_log), "--output", str(out_path)]
        )

        # Returns 0, warns to stderr, and creates no output file.
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "no transcript written" in captured.err.lower()
        assert not out_path.exists()
