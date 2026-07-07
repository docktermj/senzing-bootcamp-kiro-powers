"""Edge-case unit tests for the Paired_Schema formatting helpers.

Feature: recap-qr-formatting

These are example-based unit tests (not property tests) covering two edge cases
of ``format_qr_section`` / ``format_qr_pair`` in ``recap_pdf_render.py``:

- Requirement 1.5: a module with zero substantive questions (an empty pair list
  or a list whose questions are all whitespace-only) yields the
  ``### Questions & Responses`` heading followed by exactly one ``- None`` list
  item, with no QR_Pairs.
- Requirement 2.5: a multi-line response has every continuation line prefixed
  with at least four leading space characters so it stays nested beneath its
  Question_Item.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import INDENT_UNIT, format_qr_pair, format_qr_section

_QR_SECTION_HEADING = "### Questions & Responses"
_QUESTION_PREFIX = "- **Q:**"
_RESPONSE_PREFIX = "- **R:**"
_EMPTY_SECTION_ITEM = "- None"


def _leading_spaces(line: str) -> int:
    """Count leading ASCII 0x20 space characters (Indent_Depth)."""
    return len(line) - len(line.lstrip(" "))


class TestQRFormatEdge:
    """Edge cases for empty/whitespace-only and multi-line QR formatting."""

    def test_empty_pair_list_emits_heading_then_none(self) -> None:
        """Validates: Requirement 1.5.

        An empty pair list yields exactly the heading and a single ``- None``
        item, with no Question_Item or Response_Item lines.
        """
        section = format_qr_section([])
        lines = section.split("\n")

        # Exactly one heading.
        assert lines.count(_QR_SECTION_HEADING) == 1
        assert lines[0] == _QR_SECTION_HEADING

        # Exactly one `- None` item and no QR_Pairs.
        assert lines.count(_EMPTY_SECTION_ITEM) == 1
        assert not any(ln.startswith(_QUESTION_PREFIX) for ln in lines)
        assert not any(ln.lstrip(" ").startswith(_RESPONSE_PREFIX) for ln in lines)

    def test_all_whitespace_questions_emit_heading_then_none(self) -> None:
        """Validates: Requirement 1.5.

        A list whose questions are all whitespace-only has zero substantive
        questions, so the section is the heading followed by exactly ``- None``.
        """
        section = format_qr_section([("   ", "resp"), ("\t", "x")])
        lines = section.split("\n")

        assert lines.count(_QR_SECTION_HEADING) == 1
        assert lines[0] == _QR_SECTION_HEADING
        assert lines.count(_EMPTY_SECTION_ITEM) == 1
        # No pairs emitted for whitespace-only questions.
        assert not any(ln.startswith(_QUESTION_PREFIX) for ln in lines)
        assert not any(ln.lstrip(" ").startswith(_RESPONSE_PREFIX) for ln in lines)

    def test_multiline_response_continuation_lines_are_indented(self) -> None:
        """Validates: Requirement 2.5.

        A multi-line response places the Question_Item at Indent_Depth 0 and
        prefixes every response line (including continuation lines) with at
        least four leading spaces so they stay nested.
        """
        lines = format_qr_pair("Q", "line1\nline2\nline3")

        # Question_Item at Indent_Depth 0.
        assert lines[0].startswith(_QUESTION_PREFIX)
        assert _leading_spaces(lines[0]) == 0
        assert "\t" not in lines[0]

        # First Response_Item line carries the prefix at Indent_Depth 4.
        assert lines[1].lstrip(" ").startswith(_RESPONSE_PREFIX)
        assert _leading_spaces(lines[1]) == INDENT_UNIT

        # Every response line (the R-prefixed line plus continuation lines) has
        # at least four leading spaces and no tab characters.
        for continuation in lines[1:]:
            assert _leading_spaces(continuation) >= INDENT_UNIT
            assert "\t" not in continuation

        # The three source lines each survive as their own rendered line.
        assert lines[1].endswith("line1")
        assert lines[2].strip() == "line2"
        assert lines[3].strip() == "line3"
