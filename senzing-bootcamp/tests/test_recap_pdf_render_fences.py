"""Property-based test for fenced-code delimiter stripping.

Feature: shared-markdown-renderer-refactor

Validates Property 3 from the design document against the canonical
Shared_Renderer_Module (``recap_pdf_render.py``): for any fenced-code block
(inner code wrapped in ``` delimiter lines), ``render_generic_blocks`` renders
the inner code content with the opening and closing fence delimiter lines
removed.

**Validates: Requirements 1.5**

``render_generic_blocks`` does not import ``fpdf`` and operates on a
caller-provided ``pdf`` object, so this test drives it with a lightweight stub
that records the text passed to ``multi_cell``. The recorded text is inspected
to confirm the ``` fence lines are dropped while the inner code lines survive.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import render_generic_blocks

# ---------------------------------------------------------------------------
# Fake FPDF stub
# ---------------------------------------------------------------------------


class _FakeFPDF:
    """Minimal FPDF-like recorder capturing text passed to ``multi_cell``.

    ``render_generic_blocks`` only calls ``set_font``, ``multi_cell``, and
    ``ln`` on its ``pdf`` argument. This stub records every ``multi_cell`` text
    payload so the test can assert what the renderer emitted.
    """

    def __init__(self) -> None:
        self.cells: list[str] = []

    def set_font(self, *args: object, **kwargs: object) -> None:
        """Accept and ignore font selection."""

    def ln(self, *args: object, **kwargs: object) -> None:
        """Accept and ignore vertical spacing."""

    def multi_cell(self, _w: float, _h: float, txt: str = "", *args: object,
                   **kwargs: object) -> None:
        """Record the rendered text payload."""
        self.cells.append(txt)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# Latin-1-safe, backtick-free, newline-free characters so ``safe_text`` is an
# identity transform on the inner content and no inner line can be mistaken for
# a ``` fence delimiter line.
_CODE_ALPHABET = st.characters(
    min_codepoint=0x20,
    max_codepoint=0x7E,
    blacklist_characters="`",
)


@st.composite
def st_code_line(draw: st.DrawFn) -> str:
    """Draw a single line of inner code (no backticks, no newlines)."""
    return draw(st.text(alphabet=_CODE_ALPHABET, min_size=0, max_size=40))


@st.composite
def st_fence_info_string(draw: st.DrawFn) -> str:
    """Draw an optional fence info string (e.g. a language tag like ``python``)."""
    return draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                max_codepoint=0x7E,
            ),
            min_size=0,
            max_size=12,
        )
    )


@st.composite
def st_fenced_code_block(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Draw a fenced-code block string plus its inner code lines.

    Returns:
        A ``(block, inner_lines)`` tuple where ``block`` is the full fenced
        block (opening ``` info line, inner lines, closing ``` line) and
        ``inner_lines`` is the list of inner code lines that should survive
        rendering with the fences removed.
    """
    info = draw(st_fence_info_string())
    inner_lines = draw(st.lists(st_code_line(), min_size=1, max_size=8))
    block = "\n".join([f"```{info}", *inner_lines, "```"])
    return block, inner_lines


# ---------------------------------------------------------------------------
# Property 3: Fenced-code rendering strips the fence delimiters
# ---------------------------------------------------------------------------


class TestFenceStripping:
    """Fenced-code rendering drops the ``` delimiter lines, keeps inner code.

    **Validates: Requirements 1.5**

    For any fenced-code block with arbitrary inner content, the canonical
    ``render_generic_blocks`` renderer emits the inner code lines while removing
    the opening and closing ``` fence delimiter lines.
    """

    # Feature: shared-markdown-renderer-refactor, Property 3: For any
    # fenced-code block (inner code wrapped in ``` delimiter lines), the
    # Shared_Renderer renders the inner code content with the opening and
    # closing fence delimiter lines removed.
    @given(case=st_fenced_code_block())
    def test_fence_delimiters_stripped(self, case: tuple[str, list[str]]) -> None:
        """The rendered output retains inner code lines and drops ``` fences.

        **Validates: Requirements 1.5**
        """
        block, inner_lines = case

        pdf = _FakeFPDF()
        render_generic_blocks(pdf, [block])

        rendered = "\n".join(pdf.cells)

        # The fence delimiter lines must be absent: no rendered line is a ```
        # fence delimiter line.
        for line in rendered.split("\n"):
            assert not line.lstrip().startswith("```"), (
                f"Fence delimiter line survived rendering: {line!r}"
            )

        # The inner code content survives exactly (inner lines are ASCII, so
        # safe_text is an identity transform here).
        assert rendered == "\n".join(inner_lines), (
            "Inner code lines were not rendered verbatim with fences removed"
        )
