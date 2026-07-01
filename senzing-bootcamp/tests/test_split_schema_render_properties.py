"""Property test for Split_List rendering (Property 8).

Feature: recap-qr-formatting

This file is self-contained: it defines its own ``st_*`` strategies and
validates Property 8 by exercising ``_build_qa_lines`` in
``generate_recap_pdf.py`` — the pure helper that determines Split_List_Schema
rendering. ``_build_qa_lines`` pairs questions and answers by index position
(``questions[i]`` with ``answers[i]``), emitting ``Q: <question>`` immediately
followed by ``A: <answer>`` for each index, iterating over the longer of the
two lists and substituting the ``(no matching entry)`` placeholder for a
missing counterpart.

By the time rendering happens the parser (``_extract_list_items``) has already
stripped the explicit ``N.`` numbers and returned items in document order, so
"number N" == index/position N. For well-formed sequential lists this
pairing-by-position realizes ascending numeric order. The strategy therefore
produces two independent lists (possibly of different lengths) and the
assertions check position-based pairing, completeness, and ascending order.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import (  # noqa: E402
    _build_qa_lines,
    _SPLIT_UNMATCHED_PLACEHOLDER,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Single-line, Latin-1-safe characters. The range 0x20..0xFF excludes newline
# (0x0A), carriage return (0x0D), and tab (0x09), so text drawn from it never
# spans multiple lines.
_SINGLE_LINE = st.characters(min_codepoint=0x20, max_codepoint=0xFF)


def st_item() -> st.SearchStrategy[str]:
    """A single-line, Latin-1-safe list item (question or answer text).

    Text is filtered so it never starts with the literal ``Q: `` or ``A: ``
    markers, keeping the emitted line unambiguous with respect to the
    label-prefixed output of ``_build_qa_lines``.
    """
    return st.text(_SINGLE_LINE, min_size=1, max_size=60).filter(
        lambda text: not text.startswith("Q: ") and not text.startswith("A: ")
    )


def st_split_section() -> st.SearchStrategy[tuple[list[str], list[str]]]:
    """Two lists (questions, answers), possibly of different lengths.

    The independent lengths exercise asymmetric numbering gaps (a question with
    no answer of the same number, or vice versa), which drive the placeholder
    path in ``_build_qa_lines``.
    """
    return st.tuples(
        st.lists(st_item(), max_size=8),
        st.lists(st_item(), max_size=8),
    )


# ---------------------------------------------------------------------------
# Property 8: Split_List rendering is complete, number-paired, and ordered
# ---------------------------------------------------------------------------


class TestSplitSchemaRender:
    """Validates: Requirements 5.1, 5.3."""

    # Feature: recap-qr-formatting, Property 8: Split_List rendering is complete,
    # number-paired, and ordered — For any Split_List_Schema section, rendering
    # pairs the answer numbered N with the question numbered N, emits every
    # question and every answer with its text and number preserved (none omitted
    # or duplicated), and orders the resulting pairs in ascending numeric order —
    # regardless of the order in which the questions and answers appear in the
    # source lists.
    #
    # Validates: Requirements 5.1, 5.3
    @given(section=st_split_section())
    def test_split_render_is_complete_paired_and_ordered(
        self, section: tuple[list[str], list[str]]
    ) -> None:
        questions, answers = section
        lines = _build_qa_lines(questions, answers)

        expected_pairs = max(len(questions), len(answers))

        # Count: exactly one Q line and one A line per index over the longer
        # list — nothing dropped, nothing duplicated (Requirement 5.1).
        assert len(lines) == 2 * expected_pairs

        for i in range(expected_pairs):
            # Number-pairing by position: the answer numbered N (index i)
            # immediately follows the question numbered N (Requirement 5.3).
            question_line = lines[2 * i]
            answer_line = lines[2 * i + 1]

            expected_question = (
                questions[i] if i < len(questions) else _SPLIT_UNMATCHED_PLACEHOLDER
            )
            expected_answer = (
                answers[i] if i < len(answers) else _SPLIT_UNMATCHED_PLACEHOLDER
            )

            # Completeness + text preserved: every real question/answer appears
            # at its own numbered position with its text intact (Requirement 5.1).
            assert question_line == f"Q: {expected_question}"
            assert answer_line == f"A: {expected_answer}"

        # Ascending numeric order: reading the emitted Q lines back yields the
        # questions in index order (0, 1, 2, ...), and likewise the A lines yield
        # the answers in index order (Requirement 5.3).
        emitted_questions = [lines[2 * i][len("Q: ") :] for i in range(expected_pairs)]
        emitted_answers = [
            lines[2 * i + 1][len("A: ") :] for i in range(expected_pairs)
        ]
        assert emitted_questions[: len(questions)] == questions
        assert emitted_answers[: len(answers)] == answers
