"""Edge-case unit test for ``- None`` parse-back in the Paired_Schema.

Feature: recap-qr-formatting

These are example-based unit tests (not property tests) covering Requirement
1.5 from the parsing side: a QR_Section whose body is the single ``- None`` list
item parses back to zero QR_Pairs.

- ``parse_qr_section`` in ``generate_recap_pdf.py`` consumes the QR_Section body
  (the text after the ``### Questions & Responses`` heading), so the heading line
  produced by ``format_qr_section`` is stripped before parsing.
- ``format_qr_section([])`` (an empty pair list) emits the heading followed by
  exactly ``- None``; its body must round-trip to zero pairs.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import parse_qr_section
from recap_pdf_render import format_qr_section

_QR_SECTION_HEADING = "### Questions & Responses"


def _section_body(section: str) -> str:
    """Strip the ``### Questions & Responses`` heading line from a section.

    ``parse_qr_section`` expects only the body (the text after the heading),
    while ``format_qr_section`` returns the heading plus the body.

    Args:
        section: The full section text produced by ``format_qr_section``.

    Returns:
        The section body with the leading heading line removed.
    """
    lines = section.split("\n")
    assert lines[0] == _QR_SECTION_HEADING
    return "\n".join(lines[1:])


class TestQRNoneParse:
    """``- None`` bodies parse back to zero QR_Pairs (Requirement 1.5)."""

    def test_bare_none_body_parses_to_zero_pairs(self) -> None:
        """Validates: Requirement 1.5.

        A QR_Section body consisting of the literal ``- None`` list item yields
        no QR_Pairs.
        """
        assert parse_qr_section("- None") == []

    def test_empty_format_roundtrips_to_zero_pairs(self) -> None:
        """Validates: Requirement 1.5.

        The section produced by ``format_qr_section([])`` (an empty pair list)
        has a ``- None`` body that parses back to zero QR_Pairs.
        """
        section = format_qr_section([])
        body = _section_body(section)
        assert parse_qr_section(body) == []

    def test_all_whitespace_questions_roundtrip_to_zero_pairs(self) -> None:
        """Validates: Requirement 1.5.

        A pair list whose questions are all whitespace-only has zero substantive
        questions, so ``format_qr_section`` emits a ``- None`` body that parses
        back to zero QR_Pairs.
        """
        section = format_qr_section([("   ", "resp"), ("\t", "x")])
        body = _section_body(section)
        assert parse_qr_section(body) == []
