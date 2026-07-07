"""Property-based tests for QR_Section structure (Paired_Schema).

Feature: recap-qr-formatting

Validates that ``format_qr_section`` emits exactly one
``### Questions & Responses`` heading and never emits the legacy
``### Questions Asked`` / ``### Answers Given`` headings, for any list of
QR_Pairs containing at least one substantive pair.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import format_qr_section  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Latin-1-safe text so the renderer's safe_text contract holds. Include
# whitespace and multi-line content to exercise the formatter broadly.
_LATIN1_TEXT = st.text(
    alphabet=st.characters(min_codepoint=0x20, max_codepoint=0xFF),
    min_size=0,
    max_size=40,
)
_MULTILINE_TEXT = st.lists(_LATIN1_TEXT, min_size=1, max_size=3).map("\n".join)

# Whitespace-only text (spaces, tabs, newlines) to exercise non-substantive
# and empty-response cases.
_WHITESPACE_TEXT = st.text(alphabet=" \t\n", min_size=0, max_size=5)


def st_text() -> st.SearchStrategy[str]:
    """Question/response text: Latin-1-safe, multi-line, or whitespace-only."""
    return st.one_of(_LATIN1_TEXT, _MULTILINE_TEXT, _WHITESPACE_TEXT)


def st_substantive_text() -> st.SearchStrategy[str]:
    """Text guaranteed to be substantive (>= 1 non-whitespace char)."""
    return st.text(
        alphabet=st.characters(min_codepoint=0x21, max_codepoint=0xFF),
        min_size=1,
        max_size=40,
    )


def st_qr_pair() -> st.SearchStrategy[tuple[str, str]]:
    """One (question, response) QR_Pair with arbitrary Latin-1-safe text."""
    return st.tuples(st_text(), st_text())


def st_qr_pairs() -> st.SearchStrategy[list[tuple[str, str]]]:
    """An ordered list of QR_Pairs guaranteed to contain a substantive pair.

    A substantive pair (question has a non-whitespace char after strip) is
    prepended so the section always renders at least one QR_Pair.
    """
    substantive = st.tuples(st_substantive_text(), st_text())
    return st.tuples(substantive, st.lists(st_qr_pair(), max_size=5)).map(
        lambda t: [t[0], *t[1]]
    )


# ---------------------------------------------------------------------------
# Property 1: QR_Section has exactly one heading and no legacy headings
# ---------------------------------------------------------------------------


class TestQRSectionStructure:
    """Validates: Requirements 1.1, 1.4."""

    # Feature: recap-qr-formatting, Property 1: QR_Section has exactly one
    # heading and no legacy headings.
    @given(pairs=st_qr_pairs())
    def test_exactly_one_heading_and_no_legacy_headings(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        """For any list of QR_Pairs with at least one substantive pair, the
        section has exactly one ``### Questions & Responses`` heading and no
        ``### Questions Asked`` / ``### Answers Given`` headings."""
        section = format_qr_section(pairs)
        # Classify structure by heading LINES at column 0, not by arbitrary
        # substrings. The formatter emits real headings unindented, while
        # question/response content and multi-line response continuation lines
        # are indented (>= 4 spaces) — so legitimate content that literally
        # reads "### Questions Asked" is never mistaken for a heading line.
        column0_lines = [
            line for line in section.splitlines() if not line.startswith(" ")
        ]
        qr_heading_lines = [
            line for line in column0_lines if line == "### Questions & Responses"
        ]
        legacy_heading_lines = [
            line
            for line in column0_lines
            if line == "### Questions Asked" or line == "### Answers Given"
        ]

        assert len(qr_heading_lines) == 1
        assert legacy_heading_lines == []
