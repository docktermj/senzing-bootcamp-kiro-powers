#!/usr/bin/env python3
"""Canonical raw-Markdown → PDF rendering helpers (Shared_Renderer_Module).

This module owns the single canonical raw-Markdown → PDF rendering logic shared
by the recap PDF generator scripts in ``senzing-bootcamp/scripts/`` — block
splitting, Latin-1-safe text handling, and per-block rendering of headings,
prose, lists, and fenced-code blocks. It is imported by both
``generate_recap_pdf.py`` (the Bundled_Generator) and
``generate_recap_pdf_inline.py`` (the Inline_Generator), eliminating the
previously duplicated raw renderer.

The module is stdlib-only at top level. ``fpdf`` is imported lazily inside the
rendering function that constructs a document (never at module top level), so the
module imports cleanly without the optional ``fpdf2`` dependency and the
generators can degrade gracefully when it is absent. The module does not depend
on the structured parser/model, keeping the Inline_Generator independent of the
Bundled_Generator.
"""

from __future__ import annotations

import re


def safe_text(text: str) -> str:
    """Ensure text is safe for PDF core fonts (Latin-1 encoding).

    Characters outside the Latin-1 range are replaced with '?' to prevent
    encoding errors with Helvetica/Courier core fonts.

    Args:
        text: Input text that may contain non-Latin-1 characters.

    Returns:
        Text safe for rendering with PDF core fonts.
    """
    return text.encode("latin-1", errors="replace").decode("latin-1")


def split_blocks(text: str) -> list[str]:
    """Split arbitrary Markdown text into renderable blocks.

    Groups consecutive non-blank lines into paragraph blocks and keeps fenced
    code blocks (delimited by ```) intact as single blocks, even when they
    contain blank lines.

    Args:
        text: Raw Markdown text.

    Returns:
        List of non-empty block strings in document order.
    """
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        if current:
            block = "\n".join(current).strip("\n")
            if block.strip():
                blocks.append(block)
            current.clear()

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if in_fence:
                current.append(line)
                in_fence = False
                flush()
            else:
                flush()
                in_fence = True
                current.append(line)
            continue

        if in_fence:
            current.append(line)
            continue

        if not line.strip():
            flush()
        else:
            current.append(line)

    flush()
    return blocks


def render_heading(pdf: "FPDF", text: str, level: int) -> None:  # noqa: F821
    """Render a heading at the given level.

    Args:
        pdf: The FPDF instance.
        text: Heading text.
        level: Heading level (2 for module heading, 3 for subsection).
    """
    if level == 2:
        pdf.set_font("Helvetica", "B", 16)
        pdf.ln(6)
    else:
        pdf.set_font("Helvetica", "B", 13)
        pdf.ln(4)
    pdf.multi_cell(0, 7, safe_text(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def render_list_items(pdf: "FPDF", items: list[str], numbered: bool = False) -> None:  # noqa: F821, E501
    """Render a list of items as bulleted or numbered entries.

    Args:
        pdf: The FPDF instance.
        items: List of text items.
        numbered: If True, use numbered list; otherwise use bullet points.
    """
    pdf.set_font("Helvetica", "", 11)
    for idx, item in enumerate(items, 1):
        prefix = f"{idx}. " if numbered else "- "
        # Handle inline code (backtick content) with monospace font
        parts = re.split(r"`([^`]+)`", item)
        pdf.set_x(pdf.l_margin + 6)
        pdf.write(6, prefix)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Normal text
                pdf.set_font("Helvetica", "", 11)
                pdf.write(6, safe_text(part))
            else:
                # Code span — monospace
                pdf.set_font("Courier", "", 10)
                pdf.write(6, safe_text(part))
        pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)


def render_generic_blocks(pdf: "FPDF", blocks: list[str]) -> None:  # noqa: F821
    """Render Generic_Content blocks (prose, code, other headings) as PDF text.

    Fenced code blocks (delimited by ```) render in a monospace font with the
    fences stripped; everything else renders as wrapped paragraph text.

    Args:
        pdf: The FPDF instance.
        blocks: Generic_Content block strings in document order.
    """
    for block in blocks:
        lines = block.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            # Fenced code block — drop the opening/closing fence lines.
            code_lines = lines[1:]
            if code_lines and code_lines[-1].lstrip().startswith("```"):
                code_lines = code_lines[:-1]
            pdf.set_font("Courier", "", 10)
            pdf.multi_cell(
                0, 5, safe_text("\n".join(code_lines)), new_x="LMARGIN", new_y="NEXT"
            )
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(
                0, 6, safe_text(block), new_x="LMARGIN", new_y="NEXT"
            )
        pdf.ln(2)


def render_markdown_body(pdf: "FPDF", body_text: str) -> None:  # noqa: F821
    """Render arbitrary Markdown body text as PDF blocks (canonical renderer).

    Splits ``body_text`` into blocks and dispatches each to the appropriate
    primitive: ATX headings (``#``..``######``), fenced code blocks,
    bulleted/numbered lists, and prose paragraphs. The caller owns page and
    cover management — this function neither creates pages nor renders a cover,
    and it does not import ``fpdf``.

    Args:
        pdf: The FPDF instance to render into.
        body_text: Raw Markdown body text.
    """
    for block in split_blocks(body_text):
        lines = block.splitlines()
        first = lines[0].lstrip() if lines else ""

        # Fenced code block — defer to the generic-block renderer.
        if first.startswith("```"):
            render_generic_blocks(pdf, [block])
            continue

        # ATX heading (single-line block beginning with one to six '#').
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", first)
        if heading_match and len(lines) == 1:
            level = len(heading_match.group(1))
            render_heading(pdf, heading_match.group(2).strip(), level=2 if level <= 2 else 3)
            continue

        # List block — every non-blank line is a bullet or numbered item.
        item_lines = [ln.strip() for ln in lines if ln.strip()]
        if item_lines and all(re.match(r"^(?:-|\*|\d+\.)\s+", ln) for ln in item_lines):
            numbered = bool(re.match(r"^\d+\.\s+", item_lines[0]))
            items = [re.sub(r"^(?:-|\*|\d+\.)\s+", "", ln) for ln in item_lines]
            render_list_items(pdf, items, numbered=numbered)
            continue

        # Prose paragraph.
        render_generic_blocks(pdf, [block])


def render_markdown_pdf(
    body_text: str,
    output_path: str,
    *,
    title: str = "Senzing Bootcamp Recap",
) -> None:
    """Render raw recap Markdown to a PDF file (Inline_Generator convenience).

    Lazily imports ``fpdf`` (never at module top level), creates the document,
    emits a single bold cover line, renders the body via
    :func:`render_markdown_body`, and writes the PDF to ``output_path``. This is
    the only function in the module that imports ``fpdf``, so an absent
    ``fpdf2`` surfaces as an ``ImportError`` the caller already handles.

    Args:
        body_text: Raw recap Markdown body.
        output_path: File path for the generated PDF.
        title: Cover-line text rendered in bold at the top of the document.

    Raises:
        ImportError: If ``fpdf2`` is not installed.
        OSError: If the PDF cannot be written to ``output_path``.
    """
    from fpdf import FPDF  # noqa: PLC0415

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Cover line.
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 10, safe_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Body.
    render_markdown_body(pdf, body_text)

    pdf.output(output_path)
