"""Unit tests for the 👉 leading-question counting rule.

Verifies the deterministic counting rule and the config/.question_pending
cross-check that underpin the Stop-boundary Leading-Question Count Audit.

Feature: conversational-self-audit-hook
Validates: Requirements 1.1, 1.5
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    classify_leading_question_count,
    count_leading_questions,
    crosscheck_pending_question,
    is_leading_question_line,
    pending_question_present,
    read_pending_question,
)

P = POINTER_INDICATOR


# ---------------------------------------------------------------------------
# Tests: the counting rule
# ---------------------------------------------------------------------------


class TestCountLeadingQuestions:
    """Unit tests for count_leading_questions().

    Validates: Requirements 1.1
    """

    def test_zero_questions(self) -> None:
        """A turn with no 👉 counts zero."""
        assert count_leading_questions("Here is a recap of the work.\nAll done.") == 0

    def test_exactly_one_question(self) -> None:
        """A single closing 👉 counts one."""
        text = f"Recap of what we did.\n\n{P} Ready to move on to Module 3?"
        assert count_leading_questions(text) == 1

    def test_two_questions(self) -> None:
        """Two 👉 lines count two."""
        text = f"{P} Which data source first?\n{P} Ready to load records?"
        assert count_leading_questions(text) == 2

    def test_bold_wrapped_question_counts(self) -> None:
        """A 👉 behind a leading bold marker still counts."""
        assert count_leading_questions(f"**{P} What language would you like?**") == 1

    def test_leading_whitespace_counts(self) -> None:
        """Leading whitespace before 👉 does not prevent counting."""
        assert count_leading_questions(f"   {P} Ready?") == 1

    def test_fenced_code_block_excluded(self) -> None:
        """A 👉 inside a fenced code block is not counted."""
        text = f"```\n{P} Example question inside a fence\n```\n{P} Real question?"
        assert count_leading_questions(text) == 1

    def test_tilde_fence_excluded(self) -> None:
        """A 👉 inside a ~~~ fenced block is not counted."""
        text = f"~~~\n{P} inside tilde fence\n~~~"
        assert count_leading_questions(text) == 0

    def test_inline_code_excluded(self) -> None:
        """A 👉 inside inline code is not counted."""
        assert count_leading_questions(f"`{P} inline example`") == 0

    def test_blockquoted_question_excluded(self) -> None:
        """A blockquoted 👉 (quoted prior-turn example) is not counted."""
        assert count_leading_questions(f"> {P} A quoted example from a prior turn") == 0

    def test_stop_and_gate_markers_not_counted(self) -> None:
        """Internal 🛑/⛔ markers are never counted as leading questions."""
        text = f"{STOP_MARKER} **STOP**\n{HARD_GATE_MARKER} **MANDATORY GATE**"
        assert count_leading_questions(text) == 0

    def test_one_question_with_trailing_stop_marker(self) -> None:
        """A well-formed turn (one 👉 then a 🛑 line) counts exactly one."""
        text = f"{P} Ready to continue?\n{STOP_MARKER} **STOP — waiting for your answer**"
        assert count_leading_questions(text) == 1


class TestIsLeadingQuestionLine:
    """Unit tests for is_leading_question_line().

    Validates: Requirements 1.1
    """

    def test_plain_pointer_line(self) -> None:
        assert is_leading_question_line(f"{P} Ready?") is True

    def test_blank_line(self) -> None:
        assert is_leading_question_line("   ") is False

    def test_prose_line(self) -> None:
        assert is_leading_question_line("This is just prose.") is False

    def test_pointer_mid_line_not_leading(self) -> None:
        """A 👉 that is not the first content is not a leading-question line."""
        assert is_leading_question_line(f"See the note {P} here") is False


class TestClassifyLeadingQuestionCount:
    """Unit tests for classify_leading_question_count().

    Validates: Requirements 1.1
    """

    def test_pass(self) -> None:
        assert classify_leading_question_count(1) == "pass"

    def test_missing(self) -> None:
        assert classify_leading_question_count(0) == "missing"

    def test_multiple(self) -> None:
        assert classify_leading_question_count(2) == "multiple"
        assert classify_leading_question_count(5) == "multiple"


# ---------------------------------------------------------------------------
# Tests: the config/.question_pending cross-check
# ---------------------------------------------------------------------------


class TestPendingQuestionReader:
    """Unit tests for read_pending_question()/pending_question_present().

    Validates: Requirements 1.5
    """

    def test_absent_file(self, tmp_path: Path) -> None:
        missing = tmp_path / ".question_pending"
        assert read_pending_question(missing) is None
        assert pending_question_present(missing) is False

    def test_type_and_body(self, tmp_path: Path) -> None:
        sentinel = tmp_path / ".question_pending"
        sentinel.write_text("step_question\nWhich data source first?\n", encoding="utf-8")
        assert read_pending_question(sentinel) == "Which data source first?"
        assert pending_question_present(sentinel) is True

    def test_type_only_no_body(self, tmp_path: Path) -> None:
        """A sentinel with only a type line (no body) is treated as no question."""
        sentinel = tmp_path / ".question_pending"
        sentinel.write_text("confirmation\n", encoding="utf-8")
        assert read_pending_question(sentinel) is None
        assert pending_question_present(sentinel) is False


class TestCrossCheck:
    """Unit tests for crosscheck_pending_question().

    Validates: Requirements 1.5
    """

    def test_consistent_one_and_pending(self) -> None:
        result = crosscheck_pending_question(1, True)
        assert result.consistent is True
        assert result.signal is None

    def test_consistent_zero_and_no_pending(self) -> None:
        result = crosscheck_pending_question(0, False)
        assert result.consistent is True
        assert result.signal is None

    def test_zero_but_pending_is_dead_end(self) -> None:
        result = crosscheck_pending_question(0, True)
        assert result.consistent is False
        assert result.signal is not None

    def test_two_but_single_pending(self) -> None:
        result = crosscheck_pending_question(2, True)
        assert result.consistent is False
        assert "2" in result.signal

    def test_one_but_no_pending(self) -> None:
        result = crosscheck_pending_question(1, False)
        assert result.consistent is False
        assert result.signal is not None
