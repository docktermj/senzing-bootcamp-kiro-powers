"""Property test for Paired_Schema QR_Pair prefixes (Property 2).

Feature: recap-qr-formatting

This file is self-contained: it defines its own ``st_qr_pair()`` /
``st_qr_pairs()`` strategies and validates Property 2 against the output of
``format_qr_section`` in ``recap_pdf_render.py`` (the Shared_Renderer_Module).
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

from recap_pdf_render import format_qr_section  # noqa: E402

# Prefixes under test — kept as local literals so the test is self-contained and
# does not depend on the module's private constants.
_QUESTION_PREFIX = "- **Q:**"
_RESPONSE_PREFIX = "- **R:**"

# Latin-1-safe printable characters (codepoints 0x20..0xFF). This range excludes
# newline (0x0A), carriage return (0x0D), and tab (0x09), so a question drawn
# from it is guaranteed to be a single line.
_LATIN1_SINGLE_LINE = st.characters(min_codepoint=0x20, max_codepoint=0xFF)


def st_question() -> st.SearchStrategy[str]:
    """Single-line, Latin-1-safe question text, including whitespace-only cases."""
    return st.one_of(
        st.text(_LATIN1_SINGLE_LINE, max_size=80),
        st.sampled_from(["", " ", "   ", "\t ", "\t"]),
    )


def st_response() -> st.SearchStrategy[str]:
    """Response text: single-line, multi-line, and whitespace-only, Latin-1-safe."""
    single = st.text(_LATIN1_SINGLE_LINE, max_size=80)
    multi = st.lists(
        st.text(_LATIN1_SINGLE_LINE, max_size=40), min_size=2, max_size=4
    ).map("\n".join)
    whitespace_only = st.sampled_from(["", " ", "   ", "\t", "\n", "  \n  "])
    return st.one_of(single, multi, whitespace_only)


def st_qr_pair() -> st.SearchStrategy[tuple[str, str]]:
    """One ``(question, response)`` QR_Pair."""
    return st.tuples(st_question(), st_response())


def st_qr_pairs() -> st.SearchStrategy[list[tuple[str, str]]]:
    """An ordered list of QR_Pairs, including the empty list."""
    return st.lists(st_qr_pair(), max_size=8)


class TestQRPrefixes:
    """Property 2: every emitted QR_Pair line carries the correct prefix."""

    # Feature: recap-qr-formatting, Property 2: Every QR_Pair carries the correct
    # prefixes — For any list of QR_Pairs, every emitted question line begins
    # with the literal `- **Q:**` and every emitted response line, after its
    # leading indentation, begins with the literal `- **R:**`.
    #
    # Validates: Requirements 1.3
    @given(pairs=st_qr_pairs())
    def test_every_pair_carries_correct_prefixes(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        section = format_qr_section(pairs)
        # Parse on "\n" only — the same line separator `format_qr_section`
        # joins with. `str.splitlines()` would over-split on exotic Latin-1
        # line-break characters (e.g. 0x85) that the formatter treats as
        # ordinary in-line text.
        lines = section.split("\n")

        # Skip the heading and its following blank line; the remainder is either
        # a single `- None` item (no substantive pairs) or the QR_Pair lines.
        body = lines[2:]

        for index, line in enumerate(body):
            depth = len(line) - len(line.lstrip(" "))
            # A Question_Item is an Indent_Depth-0 list item that is not the
            # empty-section sentinel. Its response is the very next emitted line.
            if depth == 0 and line.startswith("- ") and line != "- None":
                assert line.startswith(_QUESTION_PREFIX), (
                    f"question line does not begin with {_QUESTION_PREFIX!r}: {line!r}"
                )
                assert index + 1 < len(body), (
                    f"question line has no following response line: {line!r}"
                )
                response_line = body[index + 1]
                assert response_line.lstrip(" ").startswith(_RESPONSE_PREFIX), (
                    "response line, after leading indentation, does not begin with "
                    f"{_RESPONSE_PREFIX!r}: {response_line!r}"
                )
