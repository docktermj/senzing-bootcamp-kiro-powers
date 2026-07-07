"""Property-based test for the fixed four-space indentation invariant.

Feature: recap-qr-formatting

Property 4: Fixed four-space indentation invariant. For any QR_Pair emitted by
``format_qr_section``, the Question_Item line has an Indent_Depth of 0 with no
tab characters, the Response_Item line has an Indent_Depth of exactly 4 with no
tab characters, and the Response_Item Indent_Depth is exactly 4 greater than its
Question_Item Indent_Depth — uniformly across every pair and every section.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import INDENT_UNIT, format_qr_section

_QUESTION_PREFIX = "- **Q:**"
_RESPONSE_PREFIX = "- **R:**"


# ---------------------------------------------------------------------------
# Strategies (self-contained)
# ---------------------------------------------------------------------------

# Latin-1-safe text: printable content the renderer can reproduce verbatim.
# Include spaces and tabs inside the *content* so we exercise that the invariant
# measures leading indentation, not incidental whitespace within the text.
_st_text_char = st.characters(min_codepoint=0x20, max_codepoint=0xFF)

_st_line = st.text(alphabet=_st_text_char, max_size=40)


def st_qr_pair() -> st.SearchStrategy[tuple[str, str]]:
    """A (question, response) pair.

    Questions are constrained to have at least one non-whitespace character so
    the pair is *substantive* and is actually emitted by ``format_qr_section``.
    Responses may be empty, whitespace-only, single-line, or multi-line to
    exercise the placeholder and continuation-line paths.
    """
    substantive_question = _st_line.filter(lambda s: s.strip() != "")
    response = st.one_of(
        st.just(""),
        st.text(alphabet=" \t", max_size=5),  # whitespace-only -> placeholder
        _st_line,
        st.lists(_st_line, min_size=2, max_size=4).map("\n".join),  # multi-line
    )
    return st.tuples(substantive_question, response)


def st_qr_pairs() -> st.SearchStrategy[list[tuple[str, str]]]:
    """An ordered, non-empty list of substantive QR_Pairs."""
    return st.lists(st_qr_pair(), min_size=1, max_size=6)


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


def _leading_spaces(line: str) -> int:
    """Count leading ASCII 0x20 space characters (Indent_Depth)."""
    return len(line) - len(line.lstrip(" "))


class TestQRIndentation:
    """Validates the fixed four-space indentation invariant (Property 4)."""

    # Feature: recap-qr-formatting, Property 4: Fixed four-space indentation
    # invariant — For any QR_Pair emitted by format_qr_section, the Question_Item
    # line has an Indent_Depth of 0 with no tab characters, the Response_Item line
    # has an Indent_Depth of exactly 4 with no tab characters, and the
    # Response_Item Indent_Depth is exactly 4 greater than its Question_Item
    # Indent_Depth — uniformly across every pair and every section.
    @given(pairs=st_qr_pairs())
    def test_fixed_four_space_indentation_invariant(
        self, pairs: list[tuple[str, str]]
    ) -> None:
        """Validates: Requirements 2.1, 2.2, 2.3, 2.4."""
        section = format_qr_section(pairs)
        lines = section.split("\n")

        # Locate every Question_Item line and its following Response_Item line.
        question_depths: list[int] = []
        response_depths: list[int] = []
        for idx, line in enumerate(lines):
            if line.startswith(_QUESTION_PREFIX):
                # No tab characters anywhere on the Question_Item line.
                assert "\t" not in line
                # Question_Item Indent_Depth is exactly 0.
                q_depth = _leading_spaces(line)
                assert q_depth == 0
                question_depths.append(q_depth)

                # The immediately following line is this question's Response_Item.
                assert idx + 1 < len(lines)
                response_line = lines[idx + 1]
                stripped = response_line.lstrip(" ")
                assert stripped.startswith(_RESPONSE_PREFIX)
                # No tab characters anywhere on the Response_Item line.
                assert "\t" not in response_line
                # Response_Item Indent_Depth is exactly 4.
                r_depth = _leading_spaces(response_line)
                assert r_depth == INDENT_UNIT == 4
                response_depths.append(r_depth)

                # Delta is exactly 4 for this pair.
                assert r_depth - q_depth == INDENT_UNIT

        # A substantive section must have emitted at least one pair, and the
        # invariant holds uniformly across every pair.
        assert len(question_depths) == len(pairs)
        assert all(d == 0 for d in question_depths)
        assert all(d == INDENT_UNIT for d in response_depths)
