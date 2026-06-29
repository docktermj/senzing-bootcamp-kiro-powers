"""Property-based test for content survival through the Shared_Renderer.

Feature: shared-markdown-renderer-refactor

Covers Property 1 from the design: rendering a non-empty Raw_Markdown_Body
through the canonical ``recap_pdf_render`` Shared_Renderer produces a non-empty
renderable body in which every distinctive content token from the input
survives (no recap content is dropped to a cover-only PDF). Token survival is
checked through the renderer's block seam (``split_blocks``) — the same content
the renderer emits — which is robust against lossy PDF text extraction. When
``fpdf2`` is installed, the test additionally asserts that a valid ``%PDF`` file
is written by ``render_markdown_pdf`` (the direct Req 8.1 check).

Validates: Requirements 1.3, 2.4, 3.2, 7.1, 8.1
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import render_markdown_pdf, split_blocks

# Whether the optional fpdf2 dependency is installed. The token-survival
# property is exercised regardless; the actual PDF write is guarded by this.
try:
    import fpdf  # noqa: F401

    _FPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    _FPDF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# ASCII alphabet for marker tokens — distinctive content the renderer must not
# drop. Uppercase + digits keeps tokens easy to spot and free of Markdown-active
# characters so they survive the block seam verbatim.
_TOKEN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


@st.composite
def st_marker_token(draw: st.DrawFn) -> str:
    """Draw a distinctive ASCII marker token.

    Tokens are prefixed with ``MARK`` so they are visually distinct and cannot
    collapse to an empty string.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty uppercase-alphanumeric marker token.
    """
    suffix = draw(st.text(alphabet=_TOKEN_ALPHABET, min_size=4, max_size=10))
    return f"MARK{suffix}"


@st.composite
def st_recap_markdown(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Draw non-empty free-form recap Markdown with injected marker tokens.

    Builds a document of loose headings, prose, fenced-code, and list blocks,
    embedding exactly one unique marker token per block so each token is a
    distinctive piece of recap content the renderer must preserve.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(body_text, tokens)`` tuple: the Markdown body and the list of
        marker tokens injected into it.
    """
    tokens = draw(
        st.lists(st_marker_token(), min_size=1, max_size=6, unique=True)
    )
    kinds = draw(
        st.lists(
            st.sampled_from(["heading", "prose", "code", "list"]),
            min_size=len(tokens),
            max_size=len(tokens),
        )
    )

    blocks: list[str] = []
    for token, kind in zip(tokens, kinds):
        if kind == "heading":
            level = draw(st.integers(min_value=1, max_value=6))
            blocks.append(f"{'#' * level} Section {token}")
        elif kind == "code":
            blocks.append(f"```\ncode line {token}\n```")
        elif kind == "list":
            marker = draw(st.sampled_from(["- ", "* ", "1. "]))
            blocks.append(f"{marker}item {token}")
        else:  # prose
            blocks.append(f"recap prose mentioning {token} inline")

    body = "\n\n".join(blocks)
    return body, tokens


# ---------------------------------------------------------------------------
# Property 1: Raw body content survives rendering
# ---------------------------------------------------------------------------


class TestContentSurvival:
    """Property 1 — raw body content survives the Shared_Renderer.

    Validates: Requirements 1.3, 2.4, 3.2, 7.1, 8.1
    """

    # Feature: shared-markdown-renderer-refactor, Property 1: For any non-empty
    # Raw_Markdown_Body, rendering it through the Shared_Renderer produces a
    # non-empty renderable body in which every distinctive content token from
    # the input survives (no recap content is dropped to a cover-only PDF).
    @given(data=st_recap_markdown())
    def test_content_survives_rendering(self, data: tuple[str, list[str]]) -> None:
        """Every injected token survives the split_blocks seam, and a valid
        ``%PDF`` file is written when ``fpdf2`` is installed."""
        body, tokens = data

        # The renderable body (the block seam the renderer emits) is non-empty.
        blocks = split_blocks(body)
        assert blocks, "Shared_Renderer produced an empty body for non-empty input"

        # Every distinctive content token survives into the rendered body.
        rendered = "\n".join(blocks)
        for token in tokens:
            assert token in rendered, f"token {token!r} was dropped during rendering"

        # Direct Req 8.1 check: a valid PDF file is written when fpdf2 is present.
        if _FPDF_AVAILABLE:
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_path = os.path.join(tmp_dir, "recap.pdf")
                render_markdown_pdf(body, output_path)
                assert os.path.exists(output_path), "no PDF file was written"
                with open(output_path, "rb") as handle:
                    header = handle.read(5)
                assert header.startswith(b"%PDF"), "output is not a valid PDF file"
