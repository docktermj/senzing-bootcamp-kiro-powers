"""Property test for choice-question lead/option bold separation.

Feature: onboarding-session-ux

Exercises the choice-question formatting helper in :mod:`helpers.bold_format`
(co-located in this tests directory, not shipped as a power script). It covers
**Property 2 — Choice question formatting separates lead from options**: for any
lead question text and any non-empty list of option strings,
:func:`helpers.bold_format.format_choice_question` renders the lead in bold
(``👉 **...**``) and every numbered option line in plain text (no ``**``).

Validates: Requirements 3.3, 3.4
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# The formatting helpers live in ``senzing-bootcamp/tests/helpers/``. Ensure the
# tests directory is importable so ``helpers.bold_format`` resolves regardless of
# the pytest import mode / invocation cwd.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from helpers.bold_format import (  # noqa: E402
    BOLD_MARKER,
    POINTER,
    format_bold_question,
    format_choice_question,
)


def st_lead() -> st.SearchStrategy[str]:
    """Strategy for arbitrary lead question text (may be empty or multi-line).

    Returns:
        A Hypothesis strategy producing arbitrary strings for the lead question.
    """
    return st.text()


def st_options() -> st.SearchStrategy[list[str]]:
    """Strategy for a non-empty list of arbitrary option strings.

    Returns:
        A Hypothesis strategy producing lists of at least one arbitrary string.
    """
    return st.lists(st.text(), min_size=1)


class TestChoiceQuestionFormatting:
    """Feature: onboarding-session-ux, Property 2: Choice question formatting \
separates lead from options

    For any lead question text and any non-empty list of option strings,
    :func:`helpers.bold_format.format_choice_question` renders the lead in bold
    (``👉 **...**``, pointer outside the bold span) and renders every numbered
    option line in plain text with no ``**`` markers.

    Validates: Requirements 3.3, 3.4
    """

    @given(lead=st_lead(), options=st_options())
    def test_lead_bold_options_plain(self, lead: str, options: list[str]) -> None:
        """Lead is rendered in bold and no option line contains ``**``.

        The lead is rendered by :func:`format_bold_question`, which may span more
        than one line when ``lead`` itself contains newlines. The lead block is
        therefore isolated by its own line count before inspecting the remaining
        (option) lines, so a newline embedded in the lead is never mistaken for
        an option line.

        Args:
            lead: Arbitrary lead question text.
            options: Non-empty list of arbitrary option strings.
        """
        result = format_choice_question(lead, options)
        lead_block = format_bold_question(lead)

        # The formatted output begins with the bold lead block, with the 👉
        # pointer at the very start and outside the bold span.
        assert result.startswith(lead_block)
        assert result.startswith(f"{POINTER} {BOLD_MARKER}")

        # The lead is rendered in bold.
        assert BOLD_MARKER in lead_block

        # Separate the lead block from the option lines by the lead's line count
        # so a multi-line lead is attributed to the lead, not to an option line.
        all_lines = result.split("\n")
        lead_line_count = lead_block.count("\n") + 1
        option_lines = all_lines[lead_line_count:]

        # Every numbered option line is plain text — no bold markers.
        for line in option_lines:
            assert BOLD_MARKER not in line, (
                f"option line unexpectedly contains bold markers: {line!r}"
            )
