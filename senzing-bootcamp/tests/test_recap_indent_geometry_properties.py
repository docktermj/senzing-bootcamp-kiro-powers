"""Property-based test for the per-level horizontal offset geometry.

Feature: recap-qr-formatting

Property 6: Per-level horizontal offset geometry. For any nesting level N from 0
up to the maximum level produced by the Paired_Schema, the rendered horizontal
start position equals the left margin plus N times a fixed positive per-level
offset; the spacing between consecutive levels is constant; the start position
stays at or right of the left margin and strictly left of the right margin; and
a Response_Item (level 1) always starts at a greater horizontal position than its
Question_Item (level 0).

These are exercised against the pure geometry helpers (``start_x`` /
``nesting_level`` and the ``PER_LEVEL_INDENT_MM`` / ``INDENT_UNIT`` constants) so
no ``fpdf`` dependency or binary PDF parsing is required.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import (  # noqa: E402
    INDENT_UNIT,
    PER_LEVEL_INDENT_MM,
    nesting_level,
    start_x,
)


# ---------------------------------------------------------------------------
# Strategies (self-contained)
# ---------------------------------------------------------------------------

# A generous but bounded maximum nesting level: the Paired_Schema only produces
# levels 0 (Question_Item) and 1 (Response_Item), but the geometry helper is
# general, so we test a range of levels up to a small maximum.
_MAX_LEVEL = 8


def st_level() -> st.SearchStrategy[int]:
    """A nesting level from 0 up to a small maximum."""
    return st.integers(min_value=0, max_value=_MAX_LEVEL)


def st_l_margin() -> st.SearchStrategy[float]:
    """A plausible page left-margin position in millimetres."""
    return st.floats(min_value=0.0, max_value=40.0, allow_nan=False, allow_infinity=False)


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestRecapIndentGeometry:
    """Validates the per-level horizontal offset geometry (Property 6)."""

    # Feature: recap-qr-formatting, Property 6: Per-level horizontal offset
    # geometry — For any nesting level N from 0 up to the maximum level produced
    # by the Paired_Schema, the rendered horizontal start position equals the
    # left margin plus N times a fixed positive per-level offset; the spacing
    # between consecutive levels is constant; the start position stays at or
    # right of the left margin and strictly left of the right margin; and a
    # Response_Item (level 1) always starts at a greater horizontal position than
    # its Question_Item (level 0).
    @given(level=st_level(), l_margin=st_l_margin())
    def test_per_level_horizontal_offset_geometry(
        self, level: int, l_margin: float
    ) -> None:
        """Validates: Requirements 3.1, 3.2, 3.3."""
        # The per-level offset is fixed and strictly positive.
        assert PER_LEVEL_INDENT_MM > 0

        # start_x == left margin + N * fixed positive per-level offset.
        assert start_x(level, l_margin) == l_margin + level * PER_LEVEL_INDENT_MM

        # Spacing between consecutive levels is constant and equal to the offset
        # (compared approximately: subtracting two floats introduces rounding).
        assert math.isclose(
            start_x(level + 1, l_margin) - start_x(level, l_margin),
            PER_LEVEL_INDENT_MM,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )

        # The start position stays at or right of the left margin.
        assert start_x(level, l_margin) >= l_margin

        # Choose a right margin large enough that every tested level fits, then
        # assert the start position is strictly left of the right margin.
        right_margin = l_margin + (_MAX_LEVEL + 1) * PER_LEVEL_INDENT_MM
        assert start_x(level, l_margin) < right_margin

        # A Response_Item (level 1) always starts to the right of its
        # Question_Item (level 0).
        assert start_x(1, l_margin) > start_x(0, l_margin)

    # Feature: recap-qr-formatting, Property 6: the nesting_level helper maps the
    # canonical four-space indentation to the levels the geometry consumes, so a
    # Response_Item indented one INDENT_UNIT sits one level right of its question.
    @given(level=st_level(), l_margin=st_l_margin())
    def test_nesting_level_feeds_start_x_consistently(
        self, level: int, l_margin: float
    ) -> None:
        """Validates: Requirements 3.1, 3.2, 3.3."""
        depth = level * INDENT_UNIT
        assert nesting_level(depth) == level
        assert start_x(nesting_level(depth), l_margin) == start_x(level, l_margin)
