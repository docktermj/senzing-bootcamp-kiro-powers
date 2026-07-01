"""Property test for Split_List unmatched-item retention (Property 9).

Feature: recap-qr-formatting

This file is self-contained: it defines its own ``st_*`` strategies and
validates Property 9 against the pure helper ``_build_qa_lines`` in
``generate_recap_pdf.py``. That helper pairs questions with answers by index,
iterating over the LONGER of the two lists so an asymmetric length never drops
content; a missing counterpart is emitted as the literal placeholder
``(no matching entry)`` (Requirement 5.4) rather than dropping the item.

Emitted lines look like ``Q: <question>`` / ``A: <answer>``; a missing
counterpart is exactly ``Q: (no matching entry)`` or ``A: (no matching entry)``.
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

from generate_recap_pdf import _build_qa_lines, _SPLIT_UNMATCHED_PLACEHOLDER  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Single-line, Latin-1-safe characters. The range 0x20..0xFF excludes newline
# (0x0A), carriage return (0x0D), and tab (0x09), so item text never spans
# multiple lines.
_SINGLE_LINE = st.characters(min_codepoint=0x20, max_codepoint=0xFF)


def st_item() -> st.SearchStrategy[str]:
    """A single-line, Latin-1-safe question or answer item.

    Items are non-empty and never equal to the placeholder text, so a real
    item's text can be told apart from a rendered ``(no matching entry)``
    placeholder in the assertions.
    """
    return st.text(_SINGLE_LINE, min_size=1, max_size=60).filter(
        lambda text: text != _SPLIT_UNMATCHED_PLACEHOLDER
    )


def st_asymmetric_lists() -> st.SearchStrategy[tuple[list[str], list[str]]]:
    """Produce ``(questions, answers)`` where one list is strictly longer.

    Guarantees at least one unmatched item: either a trailing question with no
    answer of the same index, or a trailing answer with no question. The shorter
    list may be empty. Both orderings (more questions, more answers) are covered.
    """
    lengths = st.tuples(
        st.integers(min_value=0, max_value=6), st.integers(min_value=0, max_value=6)
    ).filter(lambda pair: pair[0] != pair[1])

    def build(pair: tuple[int, int]) -> st.SearchStrategy[tuple[list[str], list[str]]]:
        q_len, a_len = pair
        return st.tuples(
            st.lists(st_item(), min_size=q_len, max_size=q_len),
            st.lists(st_item(), min_size=a_len, max_size=a_len),
        )

    return lengths.flatmap(build)


# ---------------------------------------------------------------------------
# Property 9: Split_List unmatched items are retained with a placeholder
# ---------------------------------------------------------------------------


class TestSplitUnmatched:
    """Validates: Requirements 5.4."""

    # Feature: recap-qr-formatting, Property 9: Split_List unmatched items are
    # retained with a placeholder — For any Split_List_Schema section containing
    # a question with no answer of the same number or an answer with no question
    # of the same number, the unmatched item is rendered with its text preserved
    # and its missing counterpart rendered as the literal placeholder
    # `(no matching entry)` — the item is never dropped.
    #
    # Validates: Requirements 5.4
    @given(lists=st_asymmetric_lists())
    def test_unmatched_items_retained_with_placeholder(
        self, lists: tuple[list[str], list[str]]
    ) -> None:
        questions, answers = lists
        lines = _build_qa_lines(questions, answers)

        placeholder = _SPLIT_UNMATCHED_PLACEHOLDER

        # The helper emits one Q line and one A line per index over the longer
        # list, so the line count is exactly 2 * max(len(q), len(a)).
        assert len(lines) == 2 * max(len(questions), len(answers))
        q_lines = lines[0::2]
        a_lines = lines[1::2]

        if len(questions) > len(answers):
            # Indices >= len(answers): the answer line is exactly the placeholder
            # and the question at that index is still present (not dropped).
            for i in range(len(answers), len(questions)):
                assert a_lines[i] == f"A: {placeholder}"
                assert q_lines[i] == f"Q: {questions[i]}"
        else:
            # len(answers) > len(questions): indices >= len(questions): the
            # question line is exactly the placeholder and the answer is present.
            for i in range(len(questions), len(answers)):
                assert q_lines[i] == f"Q: {placeholder}"
                assert a_lines[i] == f"A: {answers[i]}"

        # Every real item's text is preserved somewhere in the output; nothing
        # is dropped (Requirement 5.4).
        for i, question in enumerate(questions):
            assert q_lines[i] == f"Q: {question}"
        for i, answer in enumerate(answers):
            assert a_lines[i] == f"A: {answer}"
