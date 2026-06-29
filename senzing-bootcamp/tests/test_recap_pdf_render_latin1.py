"""Property-based test for Latin-1 safety in the Shared_Renderer_Module.

Feature: shared-markdown-renderer-refactor

Validates Property 2 from the design (Latin-1 safety never raises an encoding
error) against ``recap_pdf_render.py``. The canonical renderer must accept
arbitrary text — including astral / non-Latin-1 code points — and render it
through PDF core fonts without raising an encoding error.

**Validates: Requirements 1.4**
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import render_markdown_body, safe_text

# Whether the optional fpdf2 dependency is importable. Latin-1 safety of
# ``safe_text`` is exercised regardless; the body-rendering assertion is
# skipped when fpdf2 is absent.
try:
    import fpdf  # noqa: F401

    _FPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - environment without fpdf2
    _FPDF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


def st_arbitrary_text() -> st.SearchStrategy[str]:
    """Generate arbitrary text including astral / non-Latin-1 code points.

    The full Unicode range (max_codepoint covers astral planes) is sampled so
    the strategy regularly produces characters outside the Latin-1 (0..255)
    range — exactly the inputs that would crash a naive core-font renderer.

    Returns:
        A strategy producing arbitrary strings, possibly empty.
    """
    return st.text(
        alphabet=st.characters(min_codepoint=0, max_codepoint=0x10FFFF),
        min_size=0,
        max_size=200,
    )


# ---------------------------------------------------------------------------
# Property 2: Latin-1 safety never raises an encoding error
# ---------------------------------------------------------------------------


class TestLatin1Safety:
    """Latin-1 safety of the Shared_Renderer.

    **Validates: Requirements 1.4**

    For any string — including characters outside the Latin-1 range —
    ``safe_text`` returns a value that encodes cleanly to Latin-1, and rendering
    a body containing that text through the Shared_Renderer completes without
    raising an encoding error.
    """

    # Feature: shared-markdown-renderer-refactor, Property 2: Latin-1 safety
    # never raises an encoding error.
    @given(text=st_arbitrary_text())
    def test_safe_text_encodes_to_latin1(self, text: str) -> None:
        """``safe_text(s).encode("latin-1")`` succeeds for arbitrary input.

        **Validates: Requirements 1.4**
        """
        # Must not raise UnicodeEncodeError for any input, including astral
        # code points outside the Latin-1 range.
        safe_text(text).encode("latin-1")

    # Feature: shared-markdown-renderer-refactor, Property 2: Latin-1 safety
    # never raises an encoding error.
    @pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 not installed")
    @given(text=st_arbitrary_text())
    def test_render_body_raises_no_encoding_error(self, text: str) -> None:
        """Rendering a body containing arbitrary ``text`` raises no encoding error.

        Builds a lightweight FPDF instance and renders a body that embeds the
        arbitrary text through the canonical ``render_markdown_body``. The render
        must complete without a Latin-1 encoding error.

        **Validates: Requirements 1.4**
        """
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        try:
            render_markdown_body(pdf, text)
        except UnicodeEncodeError as exc:  # pragma: no cover - failure path
            pytest.fail(f"render_markdown_body raised an encoding error: {exc!r}")
