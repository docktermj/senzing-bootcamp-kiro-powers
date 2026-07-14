"""Property and example tests for the 👉 leading-question counting rule.

These tests exercise the deterministic counting rule in
``count_leading_questions.py`` — the single source of truth the Stop-boundary
Leading-Question Count Audit builds on — over *synthetic rendered turns* and
assert the four correctness properties from the design:

* **P1 (soundness):** for any rendered Yielding_Turn, the audit flags it iff the
  👉 leading-question count is not exactly one (with the design's exclusions:
  code fences, inline code, quoted prior-turn examples, and the internal 🛑/⛔
  markers).
* **P2 (non-yielding safety):** for any non-yielding / pass-through / period
  turn, the audit produces no output — the excluded contexts contribute zero
  leading questions.
* **P3 (no self-worsening):** the self-correction output contains at most one 👉
  and is not itself a compound question / new leading-question line.
* **P4 (non-blocking):** for any input or internal error, the counting rule and
  the ``config/.question_pending`` reader degrade gracefully (never raise,
  never block).

The Yielding_Turn detection and self-correction *phase* live as prose in the
``ask-bootcamper`` hook prompt; their determinism comes from this importable
counting rule, so these tests target the rule that makes the phase deterministic.

Feature: conversational-self-audit-hook
Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4

Conventions: Python 3.11+, stdlib-only helpers, type hints, Google-style
docstrings, pytest + Hypothesis, class-based, ``sys.path``-import,
``st_``-prefixed strategies.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from count_leading_questions import (  # noqa: E402
    HARD_GATE_MARKER,
    POINTER_INDICATOR,
    STOP_MARKER,
    CrossCheckResult,
    classify_leading_question_count,
    count_leading_questions,
    crosscheck_pending_question,
    is_leading_question_line,
    pending_question_present,
    read_pending_question,
)

P = POINTER_INDICATOR


# ---------------------------------------------------------------------------
# Shared vocabulary
# ---------------------------------------------------------------------------

# Question bodies (no trailing punctuation) reused to build both real leading
# questions and the various excluded (non-counting) contexts.
_QUESTION_BODIES: tuple[str, ...] = (
    "Ready to move on to the next module",
    "Which data source should we map first",
    "Should I generate config/data_sources.yaml",
    "Want to load the truth set now",
    "Do you want to run entity resolution",
)

# Prose lines that never begin with 👉, a blockquote marker, or a code fence, so
# they never contribute to the leading-question count.
_PROSE_LINES: tuple[str, ...] = (
    "Here is a recap of the work we completed.",
    "The transformation step finished successfully.",
    "All 42 records loaded into the SQLite database.",
    "I updated the mapping and re-ran the load.",
    "Nothing else changed in this turn.",
)

# Leading indentation variants that must not prevent counting.
_INDENTS: tuple[str, ...] = ("", " ", "   ", "\t")

# Alphabet for fence-content and free-text lines that can never open/close a
# code fence (no backtick, no tilde).
_SAFE_ALPHABET = "abcdefghijklmnopqrstuvwxyz ?.,-"


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


@st.composite
def st_leading_question_line(draw: st.DrawFn) -> str:
    """Draw a single line that IS a 👉 leading question (contributes one).

    Covers optional leading whitespace and the ``**👉 …**`` bold wrapper — both
    of which the counting rule must see through.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A rendered line whose first non-whitespace, non-bold content is 👉.
    """
    indent = draw(st.sampled_from(_INDENTS))
    body = draw(st.sampled_from(_QUESTION_BODIES))
    if draw(st.booleans()):
        return f"{indent}**{P} {body}?**"
    return f"{indent}{P} {body}?"


@st.composite
def st_non_counting_line(draw: st.DrawFn) -> str:
    """Draw a single line that must NOT count as a leading question.

    Covers plain prose, a mid-line 👉 (not the first content), a blockquoted
    (quoted prior-turn) 👉, an inline-code 👉, and the internal 🛑/⛔ markers.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A rendered line that contributes zero to the leading-question count.
    """
    body = draw(st.sampled_from(_QUESTION_BODIES))
    kind = draw(
        st.sampled_from(
            ("prose", "midline", "blockquote", "inline_code", "stop", "gate")
        )
    )
    if kind == "prose":
        return draw(st.sampled_from(_PROSE_LINES))
    if kind == "midline":
        # 👉 is not the first content, so the line is not a leading question.
        return f"See the note {P} for details on {body.lower()}."
    if kind == "blockquote":
        return f"> {P} {body}?"
    if kind == "inline_code":
        return f"`{P} {body}?`"
    if kind == "stop":
        return f"{STOP_MARKER} **STOP — waiting for your answer**"
    return f"{HARD_GATE_MARKER} **MANDATORY GATE**"


@st.composite
def st_fence_block(draw: st.DrawFn) -> list[str]:
    """Draw a complete fenced code block (open + body + close), contributing zero.

    The body may include lines beginning with 👉; because they are inside the
    fence they never count. The fence marker alternates between ``` and ~~~.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        The list of lines making up the fenced block.
    """
    fence = draw(st.sampled_from(("```", "~~~")))
    body = draw(st.lists(st_fence_content_line(), min_size=0, max_size=4))
    return [fence, *body, fence]


@st.composite
def st_fence_content_line(draw: st.DrawFn) -> str:
    """Draw a line safe to place inside a fenced block (never a fence marker).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A line that contains no backtick or tilde run, optionally 👉-prefixed.
    """
    text = draw(st.text(alphabet=_SAFE_ALPHABET, max_size=40))
    prefix = draw(st.sampled_from(("", f"{P} ", "> ", "**")))
    return f"{prefix}{text}"


@st.composite
def st_turn_with_known_count(draw: st.DrawFn) -> tuple[str, int]:
    """Draw a synthetic rendered turn with a known expected leading-question count.

    Interleaves real leading-question lines (each contributing one) with
    non-counting lines and complete fenced blocks (each contributing zero), then
    shuffles the pieces so the leading questions can appear anywhere in the turn.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(text, expected_count)`` pair where ``expected_count`` is the number
        of real 👉 leading-question lines the rule should find.
    """
    n_questions = draw(st.integers(min_value=0, max_value=4))
    pieces: list[list[str]] = [[draw(st_leading_question_line())] for _ in range(n_questions)]

    n_noise = draw(st.integers(min_value=0, max_value=4))
    pieces.extend([draw(st_non_counting_line())] for _ in range(n_noise))

    n_fences = draw(st.integers(min_value=0, max_value=2))
    pieces.extend(draw(st_fence_block()) for _ in range(n_fences))

    pieces = draw(st.permutations(pieces))
    lines: list[str] = [line for block in pieces for line in block]
    return "\n".join(lines), n_questions


# ---------------------------------------------------------------------------
# P1 — Soundness of the count / classification
# ---------------------------------------------------------------------------


class TestP1Soundness:
    """P1 — the audit flags a turn iff the 👉 count is not exactly one.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

    For any synthetic rendered turn assembled from real leading-question lines,
    non-counting noise (prose, mid-line/blockquoted/inline-code 👉, internal
    markers), and fenced blocks, the counting rule returns exactly the number of
    real leading-question lines, and the classification passes iff that count is
    exactly one.
    """

    @given(turn=st_turn_with_known_count())
    def test_count_matches_expected(self, turn: tuple[str, int]) -> None:
        """The rule counts exactly the real leading-question lines."""
        text, expected = turn
        assert count_leading_questions(text) == expected, (
            f"Expected {expected} leading questions in the rendered turn, but the "
            f"rule counted {count_leading_questions(text)}.\n---\n{text}\n---"
        )

    @given(turn=st_turn_with_known_count())
    def test_flag_iff_count_not_one(self, turn: tuple[str, int]) -> None:
        """The audit flags (classification != pass) iff the count is not one."""
        text, expected = turn
        count = count_leading_questions(text)
        flagged = classify_leading_question_count(count) != "pass"
        assert flagged == (count != 1), (
            "The audit must flag a turn iff its leading-question count is not "
            f"exactly one (count={count}, expected={expected})."
        )

    @given(
        pre=st.lists(st_non_counting_line(), min_size=0, max_size=4),
        question=st_leading_question_line(),
        fence=st_fence_block(),
    )
    def test_fencing_content_preserves_single_count(
        self, pre: list[str], question: str, fence: list[str]
    ) -> None:
        """Wrapping arbitrary content in a code fence never changes a valid count.

        A turn with exactly one real leading question keeps a count of one no
        matter what (including extra 👉 lines) is placed inside a fenced block.
        """
        lines = [*pre, question, *fence]
        text = "\n".join(lines)
        assert count_leading_questions(text) == 1, (
            "A single valid leading question must remain a count of one even when "
            f"arbitrary code-fenced content is added.\n---\n{text}\n---"
        )

    def test_classification_thresholds(self) -> None:
        """Zero → missing, one → pass, two-plus → multiple (concrete examples)."""
        assert classify_leading_question_count(0) == "missing"
        assert classify_leading_question_count(1) == "pass"
        assert classify_leading_question_count(2) == "multiple"
        assert classify_leading_question_count(7) == "multiple"


# ---------------------------------------------------------------------------
# P2 — Non-yielding safety (excluded contexts contribute nothing)
# ---------------------------------------------------------------------------


class TestP2NonYieldingSafety:
    """P2 — non-yielding / pass-through / excluded turns yield no leading question.

    **Validates: Requirements 1.5, 2.x**

    Content that is not a live yielding question — the DEFAULT-OUTPUT single
    period, internal 🛑/⛔ markers, blockquoted prior-turn examples, and fenced
    code (even when it embeds 👉) — never contributes to the count, so the audit
    has nothing to flag on such turns.
    """

    @given(lines=st.lists(st_non_counting_line(), min_size=0, max_size=8))
    def test_only_excluded_lines_count_zero(self, lines: list[str]) -> None:
        """A turn built solely from non-counting lines has a count of zero."""
        text = "\n".join(lines)
        assert count_leading_questions(text) == 0, (
            f"Excluded content must contribute zero leading questions:\n{text}"
        )

    @given(fence=st_fence_block())
    def test_fenced_content_counts_zero(self, fence: list[str]) -> None:
        """A turn that is only a fenced block (even with 👉 inside) counts zero."""
        assert count_leading_questions("\n".join(fence)) == 0

    def test_default_output_period_counts_zero(self) -> None:
        """The DEFAULT-OUTPUT single period is not a leading question."""
        assert count_leading_questions(".") == 0

    def test_empty_and_whitespace_turns_count_zero(self) -> None:
        """Empty and whitespace-only turns produce no leading question."""
        assert count_leading_questions("") == 0
        assert count_leading_questions("   \n\t\n  ") == 0

    def test_internal_markers_only_count_zero(self) -> None:
        """A turn of only 🛑/⛔ internal markers produces no leading question."""
        text = f"{STOP_MARKER} **STOP**\n{HARD_GATE_MARKER} **MANDATORY GATE**"
        assert count_leading_questions(text) == 0


# ---------------------------------------------------------------------------
# P3 — No self-worsening (self-correction output stays clean)
# ---------------------------------------------------------------------------


def render_self_correction(count: int) -> str:
    """Render the audit's self-correction instruction for a violating count.

    Mirrors the two self-correction messages defined in ``design.md``
    ("Self-correction output"): a dead-end (zero 👉) message and a
    multiple-leading-questions (two-plus 👉) message. Reproduced here so the
    tests can assert the output never worsens the turn (P3).

    Args:
        count: The violating leading-question count (0, or 2+).

    Returns:
        The self-correction instruction text.
    """
    if count == 0:
        return (
            "This turn ended without a leading question — re-render it to end "
            f"with exactly one {P} question the bootcamper can answer."
        )
    return (
        f"This turn ended with {count} leading questions — re-render ending with "
        "exactly one; if these are alternatives, present a single lead question "
        "with a numbered list."
    )


class TestP3NoSelfWorsening:
    """P3 — the self-correction output carries at most one 👉 and no compound question.

    **Validates: Requirements 2.1, 2.3**

    The instruction the audit emits on a violation must not itself introduce a
    second 👉, a new leading-question line, or a compound question.
    """

    @given(count=st.integers(min_value=2, max_value=9))
    def test_multiple_message_introduces_no_leading_question(self, count: int) -> None:
        """The multiple-questions message renders no new 👉 leading-question line."""
        output = render_self_correction(count)
        assert count_leading_questions(output) == 0, (
            "The self-correction output must not itself be a leading question."
        )
        assert output.count(P) <= 1, "The output must contain at most one 👉."
        assert output.count("?") <= 1, "The output must not be a compound question."

    def test_dead_end_message_introduces_no_leading_question(self) -> None:
        """The zero-👉 (dead-end) message renders no new 👉 leading-question line."""
        output = render_self_correction(0)
        assert count_leading_questions(output) == 0
        assert output.count(P) <= 1
        assert output.count("?") <= 1

    @given(count=st.integers(min_value=2, max_value=9))
    def test_self_correction_never_yields_a_pass_turn(self, count: int) -> None:
        """The self-correction text alone never classifies as a passing turn.

        The instruction is advisory prose, not a replacement question, so on its
        own it must not read as the single-question 'pass' turn.
        """
        output = render_self_correction(count)
        assert classify_leading_question_count(count_leading_questions(output)) != "pass"


# ---------------------------------------------------------------------------
# P4 — Non-blocking (graceful degradation, never raises)
# ---------------------------------------------------------------------------


class TestP4NonBlocking:
    """P4 — the counting rule and cross-check never raise / never block.

    **Validates: Requirements 2.2, 2.4, 3.x**

    For any input — including arbitrary text and a missing sentinel file — the
    rule returns a well-formed result instead of raising, so the audit can
    degrade to a silent no-op and never block the turn.
    """

    @given(text=st.text(max_size=500))
    def test_count_never_raises_and_is_non_negative(self, text: str) -> None:
        """Counting arbitrary text always returns a non-negative integer."""
        result = count_leading_questions(text)
        assert isinstance(result, int)
        assert result >= 0

    @given(line=st.text(max_size=200))
    def test_is_leading_question_line_never_raises(self, line: str) -> None:
        """Classifying a single arbitrary line always returns a bool."""
        assert isinstance(is_leading_question_line(line), bool)

    @given(
        count=st.integers(min_value=0, max_value=9),
        present=st.booleans(),
    )
    def test_crosscheck_never_raises(self, count: int, present: bool) -> None:
        """The cross-check always returns a well-formed result for any inputs."""
        result = crosscheck_pending_question(count, present)
        assert isinstance(result, CrossCheckResult)
        assert result.rendered_count == count
        assert result.pending_present is present
        # Consistency holds exactly for (1, pending) and (0, no-pending).
        expected_consistent = (count == 1 and present) or (count == 0 and not present)
        assert result.consistent is expected_consistent
        assert (result.signal is None) is result.consistent

    def test_missing_sentinel_degrades_to_no_op(self, tmp_path: Path) -> None:
        """A missing config/.question_pending reads as 'no question pending'."""
        missing = tmp_path / "does_not_exist" / ".question_pending"
        assert read_pending_question(missing) is None
        assert pending_question_present(missing) is False
