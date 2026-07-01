"""Property test for the Paired_Schema round-trip (Property 5).

Feature: recap-qr-formatting

This file is self-contained: it defines its own ``st_*`` strategies and
validates Property 5 by formatting a list of substantive QR_Pairs with
``format_qr_section`` (in ``recap_pdf_render.py``, the authoring source of
truth) and parsing the emitted section body back with ``parse_qr_section``
(in ``generate_recap_pdf.py``). The two functions must be exact inverses over
substantive, Latin-1-safe input: same pairs, same order, each response
immediately following its question, and question/response text reproduced
character-for-character (excluding the ``- **Q:**`` / ``- **R:**`` prefixes and
the response indentation).
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
from generate_recap_pdf import parse_qr_section, QRPair  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Single-line, Latin-1-safe characters. The range 0x20..0xFF excludes newline
# (0x0A), carriage return (0x0D), and tab (0x09), so text drawn from it never
# spans multiple lines. Questions are kept on a single line because
# `format_qr_pair` writes the question on one line — a multi-line question could
# not round-trip.
_SINGLE_LINE = st.characters(min_codepoint=0x20, max_codepoint=0xFF)

# Response line characters exclude the asterisk (0x2A) so a response line can
# never form the literal `**` of a `- **Q:**` / `- **R:**` marker. Without this,
# an indented continuation line that de-indented to exactly a Q/R marker would
# be re-parsed as a new pair — an inherent ambiguity of the Markdown schema,
# not a defect in the round-trip. Every other Latin-1 single-line character is
# fair game.
_RESPONSE_LINE = st.characters(
    min_codepoint=0x20, max_codepoint=0xFF, blacklist_characters="*"
)


def st_question() -> st.SearchStrategy[str]:
    """A substantive, single-line, Latin-1-safe question.

    Substantive means it has at least one non-whitespace character after
    ``strip`` so `format_qr_section` keeps the pair (it drops pairs whose
    question is blank/whitespace-only).
    """
    return st.text(_SINGLE_LINE, min_size=1, max_size=80).filter(
        lambda text: bool(text.strip())
    )


def st_response() -> st.SearchStrategy[str]:
    """A substantive response: single-line or multi-line, Latin-1-safe.

    Substantive (non-whitespace after ``strip``) so `format_qr_pair` reproduces
    the text verbatim instead of substituting the ``(no response recorded)``
    placeholder. Multi-line responses exercise the continuation-line fold-back.
    """
    single = st.text(_RESPONSE_LINE, min_size=1, max_size=80)
    multi = st.lists(
        st.text(_RESPONSE_LINE, max_size=40), min_size=2, max_size=4
    ).map("\n".join)
    return st.one_of(single, multi).filter(lambda text: bool(text.strip()))


def st_qr_pair() -> st.SearchStrategy[tuple[str, str]]:
    """One substantive ``(question, response)`` QR_Pair."""
    return st.tuples(st_question(), st_response())


def st_qr_pairs() -> st.SearchStrategy[list[tuple[str, str]]]:
    """A non-empty ordered list of substantive QR_Pairs."""
    return st.lists(st_qr_pair(), min_size=1, max_size=8)


# ---------------------------------------------------------------------------
# Property 5: Paired round-trip preserves text, order, adjacency, and count
# ---------------------------------------------------------------------------


class TestQRRoundtrip:
    """Validates: Requirements 1.2, 4.1, 4.3, 4.4."""

    # Feature: recap-qr-formatting, Property 5: Paired round-trip preserves text,
    # order, adjacency, and count — For any list of substantive QR_Pairs,
    # formatting the pairs into a QR_Section (format_qr_section) and then parsing
    # that section back (parse_qr_section) yields exactly the same pairs, in the
    # same first-to-last order, with each response immediately following its
    # question, and with question and response text reproduced
    # character-for-character (excluding the `- **Q:**` / `- **R:**` prefixes and
    # the response indentation), over Latin-1-safe input.
    #
    # Validates: Requirements 1.2, 4.1, 4.3, 4.4
    @given(pairs=st_qr_pairs())
    def test_paired_round_trip_is_identity(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        section = format_qr_section(pairs)

        # `format_qr_section` emits the `### Questions & Responses` heading on
        # the first line; `parse_qr_section` expects the section BODY (the text
        # after the heading). Drop the heading line before parsing.
        heading, _, body = section.partition("\n")
        assert heading == "### Questions & Responses"

        parsed = parse_qr_section(body)

        # Count: one QR_Pair parsed for every substantive input pair, none
        # dropped or duplicated (Requirement 4.1).
        assert len(parsed) == len(pairs)

        # Order + text: each parsed pair equals its input verbatim in the same
        # first-to-last order; adjacency (the response follows its question) is
        # inherent to the QRPair structure (Requirements 1.2, 4.3, 4.4).
        for parsed_pair, (question, response) in zip(parsed, pairs):
            assert isinstance(parsed_pair, QRPair)
            assert parsed_pair.question == question
            assert parsed_pair.response == response
