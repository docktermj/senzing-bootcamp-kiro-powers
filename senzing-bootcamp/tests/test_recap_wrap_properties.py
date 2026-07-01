"""Property test for indent-aware text wrapping within margins (Property 7).

Feature: recap-qr-formatting

This file is self-contained: it defines its own ``st_wrap_text()`` /
``st_width()`` strategies and validates Property 7 against the pure ``wrap_text``
helper in ``recap_pdf_render.py`` (the Shared_Renderer_Module). ``wrap_text`` is a
pure, greedy, whitespace-token word-wrapper with no ``fpdf`` dependency, so it can
be tested directly.
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

from recap_pdf_render import wrap_text  # noqa: E402

# Latin-1-safe printable characters (codepoints 0x20..0xFF). Mixing this class
# with explicit whitespace produces text with a natural spread of words and gaps.
_LATIN1_CHARS = st.characters(min_codepoint=0x20, max_codepoint=0xFF)


def st_wrap_text() -> st.SearchStrategy[str]:
    """Latin-1-safe text mixing words and whitespace, including tokenless cases."""
    words = st.text(_LATIN1_CHARS, max_size=15)
    whitespace = st.sampled_from([" ", "  ", "\t", " \t ", "\n", "   "])
    # Interleave word-ish and whitespace fragments into a single string.
    fragments = st.lists(st.one_of(words, whitespace), max_size=12)
    return fragments.map("".join)


def st_width() -> st.SearchStrategy[float]:
    """Available horizontal width for the text (strictly positive)."""
    return st.floats(min_value=1.0, max_value=400.0, allow_nan=False, allow_infinity=False)


def st_char_width() -> st.SearchStrategy[float]:
    """Rendered width of a single character (strictly positive)."""
    return st.floats(min_value=1.0, max_value=15.0, allow_nan=False, allow_infinity=False)


class TestRecapWrap:
    """Property 7: text wraps within the available width without dropping content."""

    # Feature: recap-qr-formatting, Property 7: Text wraps within margins without
    # dropping content — For any item text and any available line width greater
    # than one character, wrapping the text produces lines that each fit within
    # the available width, and rejoining the wrapped lines reproduces every token
    # of the original text with no word truncated or dropped.
    #
    # Validates: Requirements 3.4
    @given(text=st_wrap_text(), width=st_width(), char_width=st_char_width())
    def test_wrap_preserves_tokens_and_fits_width(
        self, text: str, width: float, char_width: float
    ) -> None:
        lines = wrap_text(text, width, char_width)

        # No content dropped or truncated: rejoining the wrapped lines with single
        # spaces and splitting on whitespace reproduces exactly the original token
        # sequence. Tokenless text yields [""], whose rejoin splits back to [].
        assert " ".join(lines).split() == text.split(), (
            f"token sequence not preserved: {lines!r} vs {text.split()!r}"
        )

        # Each returned line fits within the width. The maximum characters per
        # line mirrors wrap_text's own contract: floor(width / char_width), at
        # least one. A line holding a single token may exceed max_chars because
        # wrap_text never splits a token; every multi-token line must fit.
        max_chars = max(1, int(width // char_width))
        for line in lines:
            assert len(line) <= max_chars or len(line.split()) <= 1, (
                f"multi-token line exceeds max_chars={max_chars}: {line!r}"
            )
