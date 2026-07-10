"""Property-based test for bold `👉` question formatting idempotence.

Exercises :func:`format_bold_question` from the ``bold_format`` test helper,
which codifies the bold-question convention the bootcamp agent follows (enforced
at runtime by steering, not by code). The single property here validates that
formatting a question:

- wraps the question wording in exactly one CommonMark bold span (``**...**``);
- keeps the leading ``👉`` pointer at the start of the line, outside the bold
  span, separated from the bold text by a single space; and
- is idempotent — re-applying the formatter to already-formatted output yields
  an identical string (no nested ``**`` markers, no duplicated pointer).

Feature: onboarding-session-ux, Property 1: Question formatting idempotence

Validates: Requirements 3.1, 3.2, 3.6
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# The bold-format helper lives in the ``helpers`` package co-located in this
# tests directory. Ensure the tests directory is importable so ``helpers``
# resolves regardless of the pytest import mode / invocation cwd, mirroring the
# established sibling-import pattern in this suite.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from helpers.bold_format import (  # noqa: E402
    BOLD_MARKER,
    POINTER,
    format_bold_question,
)

# Prefix a formatted bold question always opens with: pointer, one space, then
# the opening bold marker (Requirements 3.1, 3.2).
_BOLD_PREFIX = f"{POINTER} {BOLD_MARKER}"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_plain_question_text() -> st.SearchStrategy[str]:
    """Draw non-empty question text with no bold markers or leading pointer.

    This constrains :func:`st.text` to the "raw question wording" input space:
    text whose trimmed form is non-empty, carries no ``**`` bold markers, and
    does not already begin with the ``👉`` pointer. For such input the formatter
    leaves the wording untouched apart from wrapping, so the bold span content
    must equal the trimmed source — which lets the structural test assert the
    text really does land inside the ``**...**`` span.

    Returns:
        A strategy producing raw, unformatted question strings.
    """
    return st.text().filter(
        lambda s: (
            s.strip() != ""
            and BOLD_MARKER not in s
            and not s.strip().startswith(POINTER)
        )
    )


def st_question_text() -> st.SearchStrategy[str]:
    """Draw any non-empty question text (may contain ``**`` and/or ``👉``).

    Used for the idempotence check, where already-formatted output (which always
    contains bold markers and a leading pointer) must be a fixed point of the
    formatter.

    Returns:
        A strategy producing non-empty question strings.
    """
    return st.text().filter(lambda s: s.strip() != "")


class TestQuestionFormattingIdempotence:
    """Property 1: Question formatting idempotence.

    Feature: onboarding-session-ux, Property 1: Question formatting idempotence

    Validates: Requirements 3.1, 3.2, 3.6
    """

    @given(text=st_plain_question_text())
    def test_format_wraps_text_in_single_bold_span_pointer_outside(
        self, text: str
    ) -> None:
        """Formatting yields ``👉 **{text}**``: one bold span, pointer outside it.

        Verifies (a) the trimmed question wording sits inside a single ``**...**``
        span and (b) the ``👉`` pointer is at the start of the line, outside the
        bold span, separated from the bold text by a single space.

        Validates: Requirements 3.1, 3.2
        """
        result = format_bold_question(text)

        # (b) Pointer leads the line, outside the bold span, single-space gap.
        assert result.startswith(_BOLD_PREFIX)
        assert result.index(POINTER) == 0
        assert result.index(POINTER) < result.index(BOLD_MARKER)

        # (a) Exactly one balanced bold span wraps the wording.
        assert result.endswith(BOLD_MARKER)
        assert result.count(BOLD_MARKER) == 2

        # The bold span contains the trimmed source wording and no ``**`` marker.
        inner = result[len(_BOLD_PREFIX):-len(BOLD_MARKER)]
        assert BOLD_MARKER not in inner
        assert inner == text.strip()

    @given(text=st_question_text())
    def test_format_bold_question_is_idempotent(self, text: str) -> None:
        """Re-applying the formatter yields an identical string (idempotence).

        The second application must be a fixed point: no nested ``**`` markers
        and no duplicated ``👉`` pointer accumulate.

        Validates: Requirements 3.1, 3.2, 3.6
        """
        once = format_bold_question(text)
        twice = format_bold_question(once)

        assert twice == once

        # A fixed point still holds the invariants: one bold span, pointer first.
        assert twice.startswith(_BOLD_PREFIX)
        assert twice.endswith(BOLD_MARKER)
        assert twice.count(BOLD_MARKER) == 2
