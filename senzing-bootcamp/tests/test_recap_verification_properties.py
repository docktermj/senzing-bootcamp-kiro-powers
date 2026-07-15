"""Property test for post-generation PDF verification (Property 5).

Feature: professional-recap-pdf

This file is self-contained: it defines its own ``st_*`` strategies and
validates Property 5 by exercising ``verify_rendered_pdf`` in
``recap_pdf_render.py`` — the round-trip check the generators run before
reporting success. ``verify_rendered_pdf`` extracts text from a written PDF via
``extract_pdf_text`` (stdlib zlib, regex-based text-show operator extraction),
asserts every expected ``Module N`` heading is present, and asserts at least
``min_body_lines`` distinctive body tokens survived. It never imports ``fpdf``,
so this test builds minimal, uncompressed PDF byte streams by hand (a
``stream``..``endstream`` block whose text is carried by ``(...) Tj`` operators)
rather than rendering with the optional ``fpdf2`` dependency.

Property 5 (Verification detects missing content): for any set of module
numbers and expected body lines, ``verify_rendered_pdf`` raises
``PdfVerificationError`` when a ``Module N`` heading is missing, and raises when
fewer than ``min_body_lines`` distinctive tokens survive (capped at the number
of available tokens); when all headings and enough body tokens are present it
does not raise.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import (  # noqa: E402
    MIN_BODY_LINES,
    PdfVerificationError,
    verify_rendered_pdf,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Lowercase ASCII letters only: Latin-1-safe, never contain a space or digit, so
# body tokens can never accidentally spell a "Module N" heading (capital M plus
# a space and a digit) and never collide with the heading tokens the verifier
# splits out of the extracted text.
_LOWER = "abcdefghijklmnopqrstuvwxyz"

# One nesting level of the module count keeps materialization cheap while still
# exercising multi-module verification.
_MAX_MODULES = 6


def st_module_numbers() -> st.SearchStrategy[list[int]]:
    """Draw 1-6 distinct single-digit module numbers.

    Restricting values to the single-digit range 1..6 (matching "1-6 modules")
    guarantees no ``Module a`` string is ever a substring of another
    ``Module b`` (single-digit and distinct implies neither decimal is a prefix
    of the other). That keeps the "missing heading" assertion unambiguous: an
    omitted module's heading is genuinely absent from the extracted text rather
    than accidentally matching a longer number's heading.
    """
    return st.lists(
        st.integers(min_value=1, max_value=_MAX_MODULES),
        min_size=1,
        max_size=_MAX_MODULES,
        unique=True,
    )


@st.composite
def st_body_lines(draw) -> tuple[list[str], list[str]]:
    """Draw 3-10 body lines plus each line's known distinctive token.

    Every line carries exactly one "long" token (length 5-12) that is unique
    across all lines and strictly longer than any filler word (length 2-4) on
    the same line. Because ``_distinctive_token`` picks the longest
    whitespace-delimited token of length >= 2, that long token is deterministically
    the line's distinctive token. Returning the tokens alongside the lines lets
    the test embed a precise number of surviving tokens into a hand-built PDF.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(lines, tokens)`` tuple where ``tokens[i]`` is the distinctive token
        of ``lines[i]`` and all tokens are unique.
    """
    tokens = draw(
        st.lists(
            st.text(alphabet=_LOWER, min_size=5, max_size=12),
            min_size=MIN_BODY_LINES,
            max_size=10,
            unique=True,
        )
    )
    lines: list[str] = []
    for token in tokens:
        fillers = draw(
            st.lists(
                st.text(alphabet=_LOWER, min_size=2, max_size=4),
                min_size=0,
                max_size=3,
            )
        )
        position = draw(st.integers(min_value=0, max_value=len(fillers)))
        words = fillers[:position] + [token] + fillers[position:]
        lines.append(" ".join(words))
    return lines, tokens


# ---------------------------------------------------------------------------
# Minimal PDF construction (no fpdf2 — stdlib only)
# ---------------------------------------------------------------------------


def _pdf_string_escape(text: str) -> str:
    """Escape a string for a PDF literal string operand.

    Backslash, open-paren, and close-paren are the characters that must be
    escaped inside a ``(...)`` PDF string. The test alphabets never emit these,
    so this is defensive, but it keeps the builder correct for any input.

    Args:
        text: The raw text to embed in a ``(...)`` operand.

    Returns:
        The escaped text safe to place between literal-string parentheses.
    """
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_minimal_pdf(literals: list[str]) -> bytes:
    """Build minimal PDF bytes whose only text is ``literals`` shown via ``Tj``.

    The bytes contain a single uncompressed ``stream``..``endstream`` block with
    one ``(literal) Tj`` operator per entry, which is exactly what
    ``extract_pdf_text`` reads (it decompresses when possible, falls back to the
    raw stream when not, and collects the parenthesised text-show operands).

    Args:
        literals: The text strings to embed as ``Tj`` operands, in order.

    Returns:
        The raw PDF bytes.
    """
    operators = "\n".join(f"({_pdf_string_escape(text)}) Tj" for text in literals)
    stream_body = operators.encode("latin-1")
    return b"".join(
        [
            b"%PDF-1.4\n",
            b"1 0 obj\n",
            b"<< /Length %d >>\n" % len(stream_body),
            b"stream\n",
            stream_body,
            b"\nendstream\n",
            b"endobj\n",
            b"%%EOF\n",
        ]
    )


# ---------------------------------------------------------------------------
# Property 5: Verification detects missing content
# ---------------------------------------------------------------------------


class TestVerificationDetectsMissingContent:
    """Validates: Requirements 5.1, 5.2."""

    # Feature: professional-recap-pdf, Property 5: Verification detects missing
    # content — For any set of module numbers and expected body lines,
    # verify_rendered_pdf raises PdfVerificationError when the PDF text is
    # missing a "Module N" heading for any expected module, and raises when
    # fewer than min_body_lines distinctive tokens survive (capped at the number
    # of available tokens); when all headings and enough body tokens are present
    # it does not raise.
    #
    # Validates: Requirements 5.1, 5.2

    @given(module_numbers=st_module_numbers(), body=st_body_lines())
    def test_missing_module_heading_raises(
        self, module_numbers: list[int], body: tuple[list[str], list[str]]
    ) -> None:
        # Omit the last module's heading (all body tokens are still present, so
        # the only failing check is the missing per-module section). Requirement
        # 5.1: every expected "Module N" heading must survive into the PDF.
        lines, _tokens = body
        kept = module_numbers[:-1]
        literals = [f"Module {n}" for n in kept] + lines
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "recap.pdf"
            pdf_path.write_bytes(build_minimal_pdf(literals))
            with pytest.raises(PdfVerificationError):
                verify_rendered_pdf(str(pdf_path), module_numbers, lines)

    @given(module_numbers=st_module_numbers(), body=st_body_lines())
    def test_insufficient_body_content_raises(
        self, module_numbers: list[int], body: tuple[list[str], list[str]]
    ) -> None:
        # Every module heading is present so the section check passes, but fewer
        # than the required number of distinctive body tokens survive. Requirement
        # 5.2: enough distinctive body tokens must survive into the PDF.
        lines, tokens = body
        required = min(MIN_BODY_LINES, len(tokens))
        surviving_lines = lines[: required - 1]
        literals = [f"Module {n}" for n in module_numbers] + surviving_lines
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "recap.pdf"
            pdf_path.write_bytes(build_minimal_pdf(literals))
            with pytest.raises(PdfVerificationError):
                verify_rendered_pdf(str(pdf_path), module_numbers, lines)

    @given(module_numbers=st_module_numbers(), body=st_body_lines())
    def test_all_headings_and_body_present_passes(
        self, module_numbers: list[int], body: tuple[list[str], list[str]]
    ) -> None:
        # Both checks are satisfied: every "Module N" heading and every body
        # line's distinctive token survive, so verification must not raise.
        lines, _tokens = body
        literals = [f"Module {n}" for n in module_numbers] + lines
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "recap.pdf"
            pdf_path.write_bytes(build_minimal_pdf(literals))
            # Should not raise.
            verify_rendered_pdf(str(pdf_path), module_numbers, lines)
