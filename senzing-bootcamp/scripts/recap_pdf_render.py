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
import zlib
from pathlib import Path

# Minimum number of distinct body lines that must survive into a rendered recap
# PDF before the generators report success. The round-trip verification
# (verify_rendered_pdf) treats a PDF that carries fewer surviving body lines than
# this floor (when the source has at least this many) as a dropped-content
# failure — the outline-only-PDF defect this bugfix addresses. The floor is
# capped at the number of body lines the source actually has, so a legitimately
# short recap is never rejected for simply having little content.
MIN_BODY_LINES = 3

# Number of leading ASCII space (0x20) characters that make up one Markdown
# nesting level in the Paired_Schema. A Response_Item nests one level (four
# spaces) beneath its Question_Item (Requirements 2.1-2.4).
INDENT_UNIT = 4

# Fixed, positive horizontal offset (in millimetres) applied per nesting level
# when rendering a list item in the PDF. An item at nesting level N starts at
# ``l_margin + N * PER_LEVEL_INDENT_MM``, so deeper items begin further right
# and the response of a QR_Pair nests visibly beneath its question
# (Requirements 3.1, 3.2).
PER_LEVEL_INDENT_MM = 6.0

# ---------------------------------------------------------------------------
# Professional layout constants (recap-pdf-professional-design)
# ---------------------------------------------------------------------------
# A single accent color (Senzing blue) is applied to every heading so the
# document reads as designed rather than plain, while body text uses a distinct
# near-black. Margins and font sizes are centralized here so the RecapPDF
# subclass and the shared rendering primitives share one source of truth.
ACCENT_COLOR = (0, 90, 156)          # Senzing blue — headings
BODY_COLOR = (40, 40, 40)            # Near-black — body text
MARGINS_MM = 20.0                    # All-sides page margin
TITLE_FONT_SIZE = 32                 # Cover page title
SUBTITLE_FONT_SIZE = 16              # Cover page subtitle
BOOTCAMPER_FONT_SIZE = 20            # Cover page bootcamper name
MODULE_HEADING_FONT_SIZE = 18        # Module-level headings
SUBSECTION_HEADING_FONT_SIZE = 14    # Subsection-level headings
BODY_FONT_SIZE = 11                  # Body text
CODE_FONT_SIZE = 10                  # Code blocks / inline code
FOOTER_FONT_SIZE = 9                 # Page footer


def _build_recap_pdf_class() -> type:
    """Build and return the ``RecapPDF`` class, importing ``fpdf`` lazily.

    ``fpdf`` is an optional dependency and MUST NOT be imported at module top
    level, so the ``RecapPDF`` subclass cannot be defined at import time (its
    base class is ``fpdf.FPDF``). This factory imports ``fpdf`` and defines the
    subclass on demand; the module-level :func:`__getattr__` caches the result
    so ``recap_pdf_render.RecapPDF`` resolves lazily on first access while the
    module still imports cleanly when ``fpdf2`` is absent.

    Returns:
        The ``RecapPDF`` class (a subclass of ``fpdf.FPDF``).

    Raises:
        ImportError: If ``fpdf2`` is not installed.
    """
    from fpdf import FPDF  # noqa: PLC0415

    class RecapPDF(FPDF):
        """Professional-layout FPDF subclass with page footers and margins.

        Sets generous all-sides margins and auto page break in ``__init__`` and
        renders a centered ``Page N`` footer on every Content_Page via the
        fpdf2 :meth:`footer` hook. The footer is suppressed on the Cover_Page
        (page 1) so the cover reads as a clean title page.
        """

        def __init__(self) -> None:
            """Initialize the document with professional margins and page break."""
            super().__init__()
            self.set_margins(MARGINS_MM, MARGINS_MM, MARGINS_MM)
            self.set_auto_page_break(auto=True, margin=MARGINS_MM)

        def is_cover_page(self) -> bool:
            """Return ``True`` when the current page is the Cover_Page (page 1).

            Returns:
                ``True`` if ``self.page_no() == 1``, otherwise ``False``.
            """
            return self.page_no() == 1

        def footer(self) -> None:
            """Render the ``Page N`` footer centered at the bottom of the page.

            Called automatically by fpdf2 on every page. On the Cover_Page the
            footer is suppressed so page 1 carries no page number.
            """
            if self.is_cover_page():
                return
            self.set_y(-15)
            self.set_font("Helvetica", "", FOOTER_FONT_SIZE)
            self.set_text_color(*BODY_COLOR)
            self.cell(0, 10, safe_text(f"Page {self.page_no()}"), align="C")

    return RecapPDF


def __getattr__(name: str):
    """Resolve ``RecapPDF`` lazily so the module imports without ``fpdf2``.

    PEP 562 module ``__getattr__`` hook: when ``RecapPDF`` is first accessed the
    subclass is built (importing ``fpdf``) and cached in the module namespace so
    subsequent accesses are direct attribute lookups.

    Args:
        name: The attribute name being resolved.

    Returns:
        The built ``RecapPDF`` class when ``name == "RecapPDF"``.

    Raises:
        AttributeError: For any other attribute name.
        ImportError: If ``name == "RecapPDF"`` but ``fpdf2`` is not installed.
    """
    if name == "RecapPDF":
        cls = _build_recap_pdf_class()
        globals()["RecapPDF"] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Paired_Schema literals — the single machine-verifiable source of truth for the
# `### Questions & Responses` section the module-recap-append hook emits.
_QR_SECTION_HEADING = "### Questions & Responses"
_QUESTION_PREFIX = "- **Q:** "
_RESPONSE_PREFIX = "- **R:** "
_NO_RESPONSE_PLACEHOLDER = "(no response recorded)"
_EMPTY_SECTION_ITEM = "- None"


def format_qr_pair(question: str, response: str) -> list[str]:
    """Return the Markdown lines for one QR_Pair (Question_Item + Response_Item).

    The first line is the Question_Item at Indent_Depth 0, prefixed
    ``- **Q:** ``. The following line(s) form the Response_Item at Indent_Depth
    :data:`INDENT_UNIT` (four spaces), prefixed ``- **R:** ``. A response that is
    absent (empty/``None``) or whitespace-only is replaced with the literal
    ``(no response recorded)`` placeholder. When the response spans multiple
    lines, every continuation line is prefixed with at least :data:`INDENT_UNIT`
    leading spaces so it stays nested beneath the Question_Item (Requirement 2.5).

    Args:
        question: The question text, rendered verbatim on the Question_Item line.
        response: The response text; when absent or whitespace-only the
            placeholder is substituted.

    Returns:
        A list of Markdown lines: the Question_Item line followed by one or more
        Response_Item lines.
    """
    indent = " " * INDENT_UNIT

    response_text = response if response is not None else ""
    if not response_text.strip():
        response_text = _NO_RESPONSE_PLACEHOLDER

    response_lines = response_text.split("\n")
    lines = [f"{_QUESTION_PREFIX}{question}"]
    lines.append(f"{indent}{_RESPONSE_PREFIX}{response_lines[0]}")
    for continuation in response_lines[1:]:
        lines.append(f"{indent}{continuation}")
    return lines


def format_qr_section(pairs: list[tuple[str, str]]) -> str:
    """Return the full ``### Questions & Responses`` section text (Paired_Schema).

    Emits exactly one ``### Questions & Responses`` heading, then each
    substantive pair as a Question_Item immediately followed by its
    Response_Item, in the given order. A pair is substantive when its question
    has at least one non-whitespace character after leading/trailing whitespace
    is stripped. When there are no substantive pairs, the heading is followed by
    exactly one ``- None`` list item and no QR_Pairs (Requirement 1.5). The
    returned text never contains a ``### Questions Asked`` or ``### Answers
    Given`` heading (Requirement 1.4).

    Args:
        pairs: Ordered ``(question, response)`` pairs in the sequence the
            questions were recorded.

    Returns:
        The complete section text, without a trailing newline.
    """
    lines = [_QR_SECTION_HEADING, ""]

    substantive = [
        (question, response)
        for question, response in pairs
        if question is not None and question.strip()
    ]

    if not substantive:
        lines.append(_EMPTY_SECTION_ITEM)
    else:
        for question, response in substantive:
            lines.extend(format_qr_pair(question, response))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Indentation and wrapping primitives (Requirements 3.1-3.4)
# ---------------------------------------------------------------------------

_LIST_MARKER_RE = re.compile(r"^(\s*)(?:-|\*|\d+\.)\s+(.*)$")
_NUMBERED_MARKER_RE = re.compile(r"^\s*\d+\.\s+")

# A Markdown pipe-table alignment/separator row is composed solely of pipes,
# whitespace, colons, and dashes (e.g. ``| :--- | ---: |``). It carries no cell
# content and must be skipped so it is never rendered as a data row
# (Requirement 6.4).
_TABLE_SEPARATOR_RE = re.compile(r"^[|\s:\-]+$")


def indent_depth(line: str) -> int:
    """Count the leading ASCII space (0x20) characters of a list-item line.

    Only literal space characters are counted as indentation. Tab characters
    are not treated as indentation units and terminate the count (Paired_Schema
    forbids tabs, so a tab marks the end of the space run).

    Args:
        line: A raw list-item (or continuation) line, indentation preserved.

    Returns:
        The number of leading ``0x20`` characters, ``0`` when the line has none.
    """
    count = 0
    for char in line:
        if char == " ":
            count += 1
        else:
            break
    return count


def nesting_level(depth: int, unit: int = INDENT_UNIT) -> int:
    """Map an Indent_Depth to a nesting level.

    The level is ``depth // unit`` (floor division), clamped to be non-negative.
    A depth that is not an exact multiple of ``unit`` (a hand-edited recap
    indented by more than the canonical amount) floors down to the enclosing
    level rather than raising.

    Args:
        depth: The Indent_Depth (leading-space count) of a list-item line.
        unit: Spaces per nesting level. Defaults to :data:`INDENT_UNIT`.

    Returns:
        The non-negative nesting level.
    """
    if unit <= 0:
        return 0
    return max(depth, 0) // unit


def start_x(level: int, l_margin: float, per_level: float = PER_LEVEL_INDENT_MM) -> float:
    """Compute the horizontal start position for a list item at ``level``.

    Pure geometry helper (no ``fpdf`` dependency): the start position is the
    left margin plus ``level`` times a fixed, positive per-level offset that is
    identical for every level, so consecutive levels are evenly spaced and a
    deeper item always starts strictly to the right of a shallower one
    (Requirements 3.1, 3.2).

    Args:
        level: The nesting level (``0`` for a top-level item); negative values
            are clamped to ``0``.
        l_margin: The page's left margin position.
        per_level: The per-level horizontal offset. Defaults to
            :data:`PER_LEVEL_INDENT_MM`.

    Returns:
        The horizontal start position for the item.
    """
    return l_margin + max(level, 0) * per_level


def wrap_text(text: str, width: float, char_width: float) -> list[str]:
    """Wrap ``text`` into lines that fit within ``width`` (pure helper).

    Greedy word-wrap that never splits inside a whitespace-delimited token, so
    rejoining the returned lines with single spaces reproduces every token of
    the original text with none truncated or dropped (Requirement 3.4). The
    maximum characters per line is ``floor(width / char_width)`` (at least one),
    so each returned line fits within ``width`` provided no single token is
    longer than that maximum. No ``fpdf`` dependency, so the wrapping property
    can test it directly.

    Args:
        text: The item text to wrap.
        width: The available horizontal width for the text.
        char_width: The rendered width of a single character.

    Returns:
        The wrapped lines; a single empty string when ``text`` has no tokens.
    """
    words = text.split()
    if not words:
        return [""]
    if char_width <= 0 or width <= 0:
        return [" ".join(words)]

    max_chars = max(1, int(width // char_width))
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def parse_list_block(block: str) -> list[tuple[int, bool, str]]:
    """Parse a Markdown list block into ``(level, numbered, text)`` triples.

    Leading indentation is preserved and translated to a nesting level via
    :func:`indent_depth` / :func:`nesting_level`. Each list-marker line
    (``-``, ``*``, or ``N.``) becomes one triple whose ``text`` is the content
    after the marker. A non-marker line folds into the preceding item's text
    (space-joined) so multi-line responses and wrapped continuation lines stay
    part of their item; a leading non-marker line with no preceding item is
    ignored.

    Args:
        block: A list block (consecutive lines), indentation preserved.

    Returns:
        ``(level, numbered, text)`` triples in document order.
    """
    items: list[tuple[int, bool, str]] = []
    for raw_line in block.splitlines():
        if not raw_line.strip():
            continue
        match = _LIST_MARKER_RE.match(raw_line)
        if match:
            level = nesting_level(indent_depth(raw_line))
            numbered = bool(_NUMBERED_MARKER_RE.match(raw_line))
            items.append((level, numbered, match.group(2)))
        elif items:
            level, numbered, text = items[-1]
            items[-1] = (level, numbered, f"{text} {raw_line.strip()}")
    return items


def render_indented_list_items(
    pdf: "FPDF", items: list[tuple[int, str]]  # noqa: F821
) -> None:
    """Render ``(level, text)`` items honoring their nesting level.

    Each item's horizontal start is ``start_x(level, pdf.l_margin)`` so deeper
    items begin further right (Requirements 3.1, 3.2). Text is rendered with
    ``multi_cell`` using width ``(right margin - start_x)`` so it wraps within
    the page margins instead of being dropped or truncated (Requirements 3.3,
    3.4). Text is emitted verbatim (Latin-1-safe) so characters are reproduced
    exactly (Requirement 4.3).

    Args:
        pdf: The FPDF instance to render into.
        items: ``(level, text)`` pairs in render order.
    """
    pdf.set_font("Helvetica", "", 11)
    right_margin_x = pdf.w - pdf.r_margin
    for level, text in items:
        x = start_x(level, pdf.l_margin)
        width = right_margin_x - x
        if width <= 0:
            width = pdf.epw
        pdf.set_x(x)
        pdf.multi_cell(width, 6, safe_text(text), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_x(pdf.l_margin)


class PdfVerificationError(Exception):
    """Raised when a written PDF fails round-trip text verification.

    Signals that the rendered PDF is missing an expected per-module section or
    dropped body content, so the caller must fail loudly rather than reporting
    success for an incomplete artifact (Req 2.6, 2.7).
    """


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
    """Render a heading at the given level in the accent color.

    Module-level headings (level 2) render at :data:`MODULE_HEADING_FONT_SIZE`
    and subsection-level headings (level 3) at :data:`SUBSECTION_HEADING_FONT_SIZE`,
    both bold and in :data:`ACCENT_COLOR` so headings read as designed and share
    one font size per level (Requirements 3.1-3.3, 5.1-5.3). The text color is
    reset to :data:`BODY_COLOR` afterward so following body text is distinct from
    the accent. Vertical spacing is preserved: ``ln(6)`` before a module heading,
    ``ln(4)`` before a subsection heading, and ``ln(2)`` after.

    Args:
        pdf: The FPDF instance.
        text: Heading text.
        level: Heading level (2 for module heading, 3 for subsection).
    """
    if level == 2:
        pdf.set_font("Helvetica", "B", MODULE_HEADING_FONT_SIZE)
        pdf.ln(6)
    else:
        pdf.set_font("Helvetica", "B", SUBSECTION_HEADING_FONT_SIZE)
        pdf.ln(4)
    pdf.set_text_color(*ACCENT_COLOR)
    # Render at full width from the left margin so wrapping always has the full
    # effective page width (a prior cell may have advanced x toward the right
    # margin; multi_cell(0, ...) would otherwise derive too little width and
    # raise FPDFException for content that should fit).
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 7, safe_text(text), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*BODY_COLOR)
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
    # Reset x to the left margin so the write-based indentation cannot leave x
    # advanced toward the right margin for the next cell's wrapping.
    pdf.set_x(pdf.l_margin)


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
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(
                pdf.epw, 5, safe_text("\n".join(code_lines)), new_x="LMARGIN", new_y="NEXT"
            )
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(
                pdf.epw, 6, safe_text(block), new_x="LMARGIN", new_y="NEXT"
            )
        pdf.ln(2)


def _split_table_row(line: str) -> list[str]:
    """Split one Markdown pipe-table row into its cell texts.

    The optional leading and trailing pipe delimiters are dropped, the row is
    split on unescaped ``|`` separators, escaped pipes (``\\|``) are unescaped
    back to a literal pipe, and each cell is stripped of surrounding
    whitespace. A row with no interior pipes yields a single-cell list.

    Args:
        line: A raw pipe-table row line (indentation and delimiters preserved).

    Returns:
        The cell texts in left-to-right order.
    """
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    cells = re.split(r"(?<!\\)\|", stripped)
    return [cell.replace("\\|", "|").strip() for cell in cells]


def render_table(pdf: "FPDF", block: str) -> None:  # noqa: F821
    """Render a Markdown pipe table as a bordered PDF grid.

    Parses the pipe-delimited ``block`` into rows and cells, skips the
    alignment/separator row (``| --- | :--: |``), and lays the remaining rows
    out in a uniform grid. Column widths are allocated proportionally to each
    column's widest cell across the available page width, so text-heavy columns
    get more room while the grid always spans the full content width. The first
    row is rendered in bold as the header and the remaining rows in normal
    weight; every cell's text is emitted through :func:`safe_text` and
    ``multi_cell`` so no cell is omitted and long cell text wraps within its
    column rather than being truncated (Requirement 6.4).

    Page breaks are managed manually while the table renders so a tall,
    multi-line row is moved to a new page as a unit rather than overprinting the
    Page_Footer; the document's auto page-break setting, draw color, font, and
    text color are restored afterward.

    Args:
        pdf: The FPDF instance to render into.
        block: The raw pipe-table block (one row per line).
    """
    line_height = 6.0

    rows: list[list[str]] = []
    for raw_line in block.splitlines():
        if not raw_line.strip():
            continue
        # Skip the alignment/separator row — it carries no cell content.
        if "-" in raw_line and _TABLE_SEPARATOR_RE.match(raw_line.strip()):
            continue
        rows.append(_split_table_row(raw_line))

    if not rows:
        return

    num_cols = max(len(row) for row in rows)
    # Pad short rows so every logical column has a cell and none is dropped.
    rows = [row + [""] * (num_cols - len(row)) for row in rows]

    # Column widths are derived from the rendered string widths of the cells,
    # measured at the weight each row uses (bold for the header row). For every
    # column we track two figures: ``ideal`` (the width that fits the widest
    # whole cell on one line) and ``floor`` (the width of the widest single word,
    # measured so a word is never broken mid-token when it can fit on the page).
    available = pdf.epw
    cell_padding = 2.0

    def _string_width(text: str, *, bold: bool) -> float:
        pdf.set_font("Helvetica", "B" if bold else "", BODY_FONT_SIZE)
        return pdf.get_string_width(safe_text(text))

    col_ideal = [0.0] * num_cols
    col_floor = [0.0] * num_cols
    for row_index, row in enumerate(rows):
        bold = row_index == 0
        for col in range(num_cols):
            cell = row[col]
            col_ideal[col] = max(col_ideal[col], _string_width(cell, bold=bold) + cell_padding)
            widest_word = max(
                (_string_width(word, bold=bold) for word in safe_text(cell).split()),
                default=0.0,
            )
            col_floor[col] = max(col_floor[col], widest_word + cell_padding)

    total_ideal = sum(col_ideal)
    if total_ideal <= 0:
        # Every cell is empty — fall back to equal columns spanning the width.
        col_widths = [available / num_cols] * num_cols
    elif total_ideal <= available:
        # Everything fits on one line per cell — scale up to fill the page width.
        scale = available / total_ideal
        col_widths = [width * scale for width in col_ideal]
    else:
        total_floor = sum(col_floor)
        if total_floor <= available:
            # Give each column its no-break floor, then distribute the leftover
            # width in proportion to how much more each column ideally wants.
            leftover = available - total_floor
            wants = [max(col_ideal[c] - col_floor[c], 0.0) for c in range(num_cols)]
            wants_total = sum(wants)
            if wants_total > 0:
                col_widths = [
                    col_floor[c] + leftover * wants[c] / wants_total for c in range(num_cols)
                ]
            else:
                col_widths = [col_floor[c] + leftover / num_cols for c in range(num_cols)]
        else:
            # Even the widest words cannot all fit; scale the floors to the page
            # width (a single word wider than its fair share may still wrap).
            scale = available / total_floor
            col_widths = [width * scale for width in col_floor]

    # Take manual control of page breaks so a wrapped row never overprints the
    # footer, and remember state to restore once the table is rendered.
    auto_page_break = pdf.auto_page_break
    bottom_margin = pdf.b_margin
    bottom_limit = pdf.h - bottom_margin
    pdf.set_auto_page_break(False)
    pdf.set_draw_color(200, 200, 200)
    try:
        for row_index, row in enumerate(rows):
            is_header = row_index == 0
            pdf.set_font("Helvetica", "B" if is_header else "", BODY_FONT_SIZE)
            pdf.set_text_color(*BODY_COLOR)

            # Row height is the tallest cell: wrapped-line count x line height.
            line_counts = []
            for col in range(num_cols):
                wrapped = pdf.multi_cell(
                    col_widths[col],
                    line_height,
                    safe_text(row[col]),
                    align="L",
                    dry_run=True,
                    output="LINES",
                )
                line_counts.append(max(1, len(wrapped)))
            row_height = max(line_counts) * line_height

            # Move a whole row to a new page rather than splitting it or
            # overprinting the footer (Requirement 4.4 spirit for tables).
            if pdf.get_y() + row_height > bottom_limit:
                pdf.add_page()

            row_top = pdf.get_y()
            cell_x = pdf.l_margin
            for col in range(num_cols):
                pdf.rect(cell_x, row_top, col_widths[col], row_height)
                pdf.set_xy(cell_x, row_top)
                pdf.multi_cell(
                    col_widths[col],
                    line_height,
                    safe_text(row[col]),
                    border=0,
                    align="L",
                    new_x="RIGHT",
                    new_y="TOP",
                    max_line_height=line_height,
                )
                cell_x += col_widths[col]
            pdf.set_xy(pdf.l_margin, row_top + row_height)
    finally:
        pdf.set_auto_page_break(auto_page_break, bottom_margin)
        pdf.set_draw_color(0, 0, 0)
        pdf.set_font("Helvetica", "", BODY_FONT_SIZE)
        pdf.set_text_color(*BODY_COLOR)
        pdf.set_x(pdf.l_margin)
    pdf.ln(2)


def _is_pipe_table(lines: list[str]) -> bool:
    """Return ``True`` when ``lines`` form a Markdown pipe table.

    A pipe table's first line is a header row carrying at least one ``|`` cell
    delimiter, and its second line is an alignment/separator row composed solely
    of pipes, whitespace, colons, and dashes (matching :data:`_TABLE_SEPARATOR_RE`)
    that contains at least one dash. Requiring the dash keeps a whitespace-only or
    pipe-only second line from being mistaken for a separator. A block failing
    either condition — a lone header row, a paragraph that merely contains a
    pipe, or a separator row without dashes — is not a table and falls through to
    prose rendering (Requirement 6.4; Tolerant_Parser principle: no crash).

    Args:
        lines: The lines of a candidate block, in document order.

    Returns:
        ``True`` if the block is a pipe table, otherwise ``False``.
    """
    if len(lines) < 2:
        return False
    if "|" not in lines[0]:
        return False
    separator = lines[1].strip()
    return "-" in separator and bool(_TABLE_SEPARATOR_RE.match(separator))


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

        # List block — the first non-blank line begins with a list marker.
        # Leading spaces are preserved (not stripped) so each item's nesting
        # level can be derived from its Indent_Depth and routed through the
        # indent-aware renderer (Requirements 3.1-3.4).
        non_blank = [ln for ln in lines if ln.strip()]
        if non_blank and re.match(r"^\s*(?:-|\*|\d+\.)\s+", non_blank[0]):
            triples = parse_list_block(block)
            if triples:
                items: list[tuple[int, str]] = []
                number = 0
                for level, numbered, text in triples:
                    if numbered:
                        number += 1
                        marker = f"{number}. "
                    else:
                        marker = "- "
                    items.append((level, f"{marker}{text}"))
                render_indented_list_items(pdf, items)
                continue

        # Pipe table — the first line carries a '|' delimiter and the second is
        # an alignment/separator row. A malformed pipe table fails this check and
        # falls through to the prose fallback below (no crash).
        if _is_pipe_table(lines):
            render_table(pdf, block)
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

    Builds a :class:`RecapPDF` document via :func:`_build_recap_pdf_class` (which
    imports ``fpdf`` lazily, never at module top level), emits a single bold
    cover line, renders the body via :func:`render_markdown_body`, and writes the
    PDF to ``output_path``. The ``RecapPDF`` subclass applies the professional
    margins and auto page break in its ``__init__``, so no manual margin setup is
    needed here. An absent ``fpdf2`` surfaces as an ``ImportError`` (raised while
    building the subclass) that the caller already handles.

    Args:
        body_text: Raw recap Markdown body.
        output_path: File path for the generated PDF.
        title: Cover-line text rendered in bold at the top of the document.

    Raises:
        ImportError: If ``fpdf2`` is not installed.
        OSError: If the PDF cannot be written to ``output_path``.
    """
    recap_pdf_cls = _build_recap_pdf_class()

    pdf = recap_pdf_cls()
    pdf.add_page()

    # Cover line.
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 10, safe_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Body.
    render_markdown_body(pdf, body_text)

    pdf.output(output_path)


# ---------------------------------------------------------------------------
# Round-trip verification (Req 2.6, 2.7)
# ---------------------------------------------------------------------------


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract visible text from a simple fpdf2-generated PDF using stdlib only.

    Decompresses each content stream (FlateDecode / zlib) when possible and
    collects the literal strings passed to the text-showing operators (the
    parenthesised operands of ``Tj``/``TJ``/``'``). The literals are joined with
    newlines so each text-show operator becomes its own line, which is enough to
    assert the presence of distinctive section headings and body-line tokens. It
    is not a general-purpose PDF parser and never imports ``fpdf``.

    Args:
        pdf_bytes: Raw bytes of a written PDF file.

    Returns:
        The newline-joined literal text content found in the PDF's streams.
    """
    chunks: list[str] = []
    # Capture the stream body up to ``endstream`` rather than requiring an
    # explicit ``\r?\n`` immediately before it. A binary FlateDecode stream can
    # legitimately end with a ``0x0D`` (\r) byte; the old ``\r?\nendstream``
    # boundary let ``\r?`` steal that trailing data byte, truncating the zlib
    # stream so ``zlib.decompress`` raised and the whole stream's text was lost
    # (a false negative on valid PDFs). ``decompressobj().decompress`` decodes
    # the zlib data and tolerates the trailing EOL bytes we now retain, whereas
    # ``zlib.decompress`` would reject that trailing data.
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL):
        raw = match.group(1)
        try:
            data = zlib.decompressobj().decompress(raw)
        except zlib.error:
            data = raw
        for token in re.finditer(rb"\((?:\\.|[^\\)])*\)", data):
            literal = (
                token.group(0)[1:-1]
                .replace(b"\\(", b"(")
                .replace(b"\\)", b")")
                .replace(b"\\\\", b"\\")
            )
            chunks.append(literal.decode("latin-1", "replace"))
    return "\n".join(chunks)


def _distinctive_token(line: str) -> str | None:
    """Return the longest whitespace-delimited token of a body line, or ``None``.

    Wrapping only ever splits a rendered line at whitespace, so an individual
    word token survives intact into the extracted PDF text even when the line
    wraps. Picking the longest token (length >= 2, Latin-1-safe to mirror what
    the renderer emits) gives a wrap-robust, low-false-positive marker for
    asserting that a source body line actually rendered.

    Args:
        line: A source body line (list item, Q/A line, duration, or block).

    Returns:
        The longest token of length >= 2, or ``None`` when the line has none.
    """
    tokens = [tok for tok in safe_text(line).split() if len(tok) >= 2]
    if not tokens:
        return None
    return max(tokens, key=len)


def verify_rendered_pdf(
    pdf_path: str,
    module_numbers: list[int],
    expected_body_lines: list[str],
    *,
    min_body_lines: int = MIN_BODY_LINES,
) -> None:
    """Verify a written PDF by round-tripping its text before reporting success.

    Re-opens the PDF at ``pdf_path``, extracts its text, and asserts that it
    contains a ``Module N`` section for every completed module and that at least
    ``min_body_lines`` distinct source body lines survived into the PDF (capped
    at the number of body lines the source actually has, so a short-but-complete
    recap is never rejected). A failure means content was dropped during
    rendering while the file was still written, so the caller must fail loudly
    rather than report success (Req 2.6, 2.7).

    Args:
        pdf_path: Path to the written PDF to verify.
        module_numbers: Module numbers that must each have a ``Module N`` section.
        expected_body_lines: Source body lines that should have rendered.
        min_body_lines: Minimum surviving body-line floor. Defaults to
            :data:`MIN_BODY_LINES`.

    Raises:
        PdfVerificationError: If a per-module section is missing or too few body
            lines survived into the rendered PDF.
        OSError: If the PDF cannot be read back from ``pdf_path``.
    """
    text = extract_pdf_text(Path(pdf_path).read_bytes())

    missing = [n for n in module_numbers if f"Module {n}" not in text]
    if missing:
        raise PdfVerificationError(
            "rendered PDF is missing per-module section(s) for module(s) "
            f"{missing}: round-trip text extraction found no 'Module N' heading."
        )

    text_tokens = set(text.split())
    candidate_tokens = [
        token for line in expected_body_lines if (token := _distinctive_token(line))
    ]
    present = sum(1 for token in candidate_tokens if token in text_tokens)
    required = min(min_body_lines, len(candidate_tokens))
    if required and present < required:
        raise PdfVerificationError(
            f"rendered PDF body verification failed: only {present} of "
            f"{len(candidate_tokens)} expected body line(s) survived into the PDF "
            f"text (require at least {required}). Body content was dropped during "
            "rendering."
        )
