#!/usr/bin/env python3
"""Stdlib-only PDF writer for the bootcamp recap (Stdlib_PDF_Writer, Tier 3).

Emits a structurally valid PDF 1.4 from the parsed recap model using ONLY the
Python standard library -- no ``fpdf2`` and no other third-party packages. This
is the guaranteed fallback: when ``fpdf2`` is neither installed nor installable,
this writer still produces a valid, if visually plain, ``docs/bootcamp_recap.pdf``
so a real PDF is always available at graduation.

The document is built by hand: a fixed catalog/pages tree, two standard Type1
fonts (Helvetica and Helvetica-Bold), one uncompressed content stream per page
whose text is drawn with the ``BT``/``Tf``/``Td``/``Tj``/``ET`` operators, a
cross-reference table, and a ``trailer``/``startxref``/``%%EOF`` epilogue. Text
literals are escaped so the same round-trip verification used elsewhere
(:func:`recap_pdf_render.extract_pdf_text` / :func:`verify_rendered_pdf`)
recovers the drawn text.

It reuses the existing recap parser/model (``RecapDocument`` / ``RecapSection`` /
``QRPair`` from ``generate_recap_pdf``) so content selection matches the rich
renderer and no recap content is dropped. Neither this module nor the modules it
imports pull in ``fpdf`` at import time, so ``fpdf2`` never becomes a hard
dependency.

Usage:
    python senzing-bootcamp/scripts/recap_pdf_minimal.py
    python senzing-bootcamp/scripts/recap_pdf_minimal.py --input recap.md
    python senzing-bootcamp/scripts/recap_pdf_minimal.py --output recap.pdf
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

# Scripts are not packages, so make this file's directory importable to resolve
# the sibling modules whether run directly or imported via the documented
# sys.path pattern. Both sibling modules are stdlib-only at import time (fpdf is
# imported lazily inside their render functions, never at module top level), so
# importing them here keeps this writer independent of fpdf2 (Requirement 4.3).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import (  # noqa: E402
    RecapDocument,
    RecapSection,
    _build_qa_lines,
    collect_verification_targets,
    parse_recap_markdown,
)
from recap_pdf_render import (  # noqa: E402
    PdfVerificationError,
    safe_text,
    split_blocks,
    verify_rendered_pdf,
    wrap_text,
)

# ---------------------------------------------------------------------------
# Page geometry and typography (US Letter, 1 inch margins, in PDF points)
# ---------------------------------------------------------------------------

PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0
MARGIN = 72.0
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN  # 468 pt usable text width
TOP_Y = PAGE_HEIGHT - MARGIN             # first baseline anchor (from the top)
BOTTOM_Y = MARGIN                        # new page once the cursor drops below

# Resource names for the two fonts referenced by every page (see _build_pdf).
FONT_REGULAR = "F1"  # Helvetica
FONT_BOLD = "F2"     # Helvetica-Bold

# Font sizes (points) for each text role.
TITLE_SIZE = 24
MODULE_HEADING_SIZE = 16
SUBSECTION_SIZE = 12
BODY_SIZE = 11

# Vertical advance per rendered line, as a multiple of the font size.
LINE_HEIGHT_FACTOR = 1.35

# Conservative average glyph width (as a fraction of the font size) used to
# estimate how many characters fit on a line for word wrapping. Helvetica's
# average is nearer 0.5; 0.55 leaves headroom so wrapped lines stay inside the
# right margin for typical text.
CHAR_WIDTH_FACTOR = 0.55

# Hanging indent (points) applied to wrapped continuation lines of a bullet so
# they align past the "- " marker rather than under it.
BULLET_HANG_MM = 10.0

# Canonical labeled subsection headings emitted for every module section. The
# "Questions & Responses" label is used regardless of the section's parsed
# schema so the heading is stable across recap formats.
LABEL_INFORMATION_SHARED = "Information Shared"
LABEL_QUESTIONS_RESPONSES = "Questions & Responses"
LABEL_ACTIONS_TAKEN = "Actions Taken"
LABEL_DURATION = "Duration"
LABEL_JOURNAL = "Journal"

_EMPTY_PLACEHOLDER = "None"


# ---------------------------------------------------------------------------
# PDF string escaping
# ---------------------------------------------------------------------------


def _escape_pdf_text(text: str) -> str:
    """Escape a string for use inside a PDF literal-string ``( ... )`` operand.

    Backslash, open-paren, and close-paren are escaped so the literal parses
    unambiguously and round-trips through :func:`recap_pdf_render.extract_pdf_text`,
    which reverses exactly these escapes. Carriage returns, newlines, and tabs
    are folded to spaces so a literal never spans lines (text is wrapped before
    it reaches this function, so no intended line breaks are lost).

    Args:
        text: Latin-1-safe text to escape.

    Returns:
        The escaped string, safe to place between ``(`` and ``)``.
    """
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
    )


# ---------------------------------------------------------------------------
# Page layout engine
# ---------------------------------------------------------------------------


class _PdfCanvas:
    """Accumulate text-drawing operators across one or more paginated pages.

    Maintains a vertical cursor that descends from the top margin; when the next
    line would fall below the bottom margin the current page's content is flushed
    and a fresh page is started, giving automatic multi-page overflow. Each
    rendered line becomes a ``BT ... Tj ET`` operator sequence in the current
    page's content stream.
    """

    def __init__(self) -> None:
        """Initialize an empty canvas with a single active (empty) page."""
        self.pages: list[str] = []
        self._current: list[str] = []
        self._y: float = TOP_Y

    def _new_page(self) -> None:
        """Flush the current page (when it has content) and reset the cursor."""
        if self._current:
            self.pages.append("\n".join(self._current))
            self._current = []
        self._y = TOP_Y

    def finish(self) -> list[str]:
        """Flush the final page and return every page's content stream text.

        Guarantees at least one page even for an empty document, so the built
        PDF always has a renderable page tree.

        Returns:
            The per-page content-stream strings in document order.
        """
        if self._current or not self.pages:
            self.pages.append("\n".join(self._current))
            self._current = []
        return self.pages

    def _emit_line(self, text: str, size: float, font: str, indent: float) -> None:
        """Draw one physical line at the current cursor, advancing downward.

        Starts a new page first when the line would cross the bottom margin.

        Args:
            text: The (already-wrapped) line text.
            size: Font size in points.
            font: Resource font name (``FONT_REGULAR`` or ``FONT_BOLD``).
            indent: Horizontal offset in points added to the left margin.
        """
        line_height = size * LINE_HEIGHT_FACTOR
        if self._y - line_height < BOTTOM_Y:
            self._new_page()
        self._y -= line_height
        x = MARGIN + indent
        escaped = _escape_pdf_text(safe_text(text))
        self._current.append(
            f"BT /{font} {size:g} Tf {x:.2f} {self._y:.2f} Td ({escaped}) Tj ET"
        )

    def paragraph(
        self,
        text: str,
        size: float,
        font: str,
        *,
        indent: float = 0.0,
        hang: float = 0.0,
        space_before: float = 0.0,
    ) -> None:
        """Word-wrap ``text`` to the content width and draw it line by line.

        Args:
            text: The text to render.
            size: Font size in points.
            font: Resource font name.
            indent: Left indent in points for every line.
            hang: Extra indent in points for wrapped continuation lines.
            space_before: Vertical gap in points inserted before the paragraph.
        """
        if space_before:
            self._y -= space_before
        width = max(40.0, CONTENT_WIDTH - indent)
        char_width = size * CHAR_WIDTH_FACTOR
        for i, line in enumerate(wrap_text(text, width, char_width)):
            self._emit_line(line, size, font, indent + (hang if i else 0.0))

    # -- role-specific convenience wrappers ---------------------------------

    def title(self, text: str) -> None:
        """Render the document title, bold and prominent."""
        self.paragraph(text, TITLE_SIZE, FONT_BOLD, space_before=4)

    def module_heading(self, text: str) -> None:
        """Render a per-module heading, bold, with generous space above."""
        self.paragraph(text, MODULE_HEADING_SIZE, FONT_BOLD, space_before=14)

    def subheading(self, text: str) -> None:
        """Render a labeled subsection heading, bold, with space above."""
        self.paragraph(text, SUBSECTION_SIZE, FONT_BOLD, space_before=8)

    def body(self, text: str, *, indent: float = 0.0) -> None:
        """Render a body paragraph in the regular font."""
        self.paragraph(text, BODY_SIZE, FONT_REGULAR, indent=indent)

    def bullet(self, text: str, *, indent: float = 0.0) -> None:
        """Render a hanging-indent bullet item in the regular font."""
        self.paragraph(
            f"- {text}",
            BODY_SIZE,
            FONT_REGULAR,
            indent=indent,
            hang=BULLET_HANG_MM,
        )


# ---------------------------------------------------------------------------
# Content rendering from the recap model
# ---------------------------------------------------------------------------


def _render_items_or_none(canvas: _PdfCanvas, items: list[str]) -> None:
    """Render ``items`` as bullets, or a single ``None`` line when empty.

    Args:
        canvas: The canvas to draw into.
        items: The list items to render (verbatim).
    """
    if items:
        for item in items:
            canvas.bullet(item)
    else:
        canvas.body(_EMPTY_PLACEHOLDER)


def _render_questions_responses(canvas: _PdfCanvas, section: RecapSection) -> None:
    """Render a module's questions/responses under one canonical heading.

    Renders Paired_Schema QR_Pairs as a ``Q:`` line followed by an indented
    ``R:`` line, or the legacy Split_List_Schema questions/answers paired by
    index (via :func:`generate_recap_pdf._build_qa_lines`, which supplies the
    ``(no matching entry)`` placeholder for an unmatched counterpart). When the
    section carries neither, a single ``None`` line is drawn. Question and
    response text is emitted verbatim so no content is dropped.

    Args:
        canvas: The canvas to draw into.
        section: The parsed module section.
    """
    canvas.subheading(LABEL_QUESTIONS_RESPONSES)
    if section.schema == "paired" and section.qr_pairs:
        for pair in section.qr_pairs:
            canvas.bullet(f"Q: {pair.question}")
            canvas.body(f"R: {pair.response}", indent=BULLET_HANG_MM + 6.0)
    elif section.questions_asked or section.answers_given:
        for line in _build_qa_lines(section.questions_asked, section.answers_given):
            canvas.bullet(line)
    else:
        canvas.body(_EMPTY_PLACEHOLDER)


def _render_section(canvas: _PdfCanvas, section: RecapSection) -> None:
    """Render a single module section with its labeled subsections.

    Emits the module heading, an optional completion timestamp, and the labeled
    subsections in a fixed order: Information Shared, Questions & Responses,
    Actions Taken, Duration, and Journal. Journal carries the section's
    Generic_Content (prose/notes the strict parser did not map to a known
    subsection) so nothing authored under a module is dropped.

    Args:
        canvas: The canvas to draw into.
        section: The parsed module section.
    """
    canvas.module_heading(f"Module {section.module_number}: {section.module_name}")
    if section.timestamp:
        canvas.body(f"Completed: {section.timestamp}")

    canvas.subheading(LABEL_INFORMATION_SHARED)
    _render_items_or_none(canvas, section.information_shared)

    _render_questions_responses(canvas, section)

    canvas.subheading(LABEL_ACTIONS_TAKEN)
    _render_items_or_none(canvas, section.actions_taken)

    canvas.subheading(LABEL_DURATION)
    canvas.body(section.duration or "N/A")

    canvas.subheading(LABEL_JOURNAL)
    if section.generic_content:
        for block in section.generic_content:
            for line in block.splitlines():
                if line.strip():
                    canvas.body(line)
    else:
        canvas.body(_EMPTY_PLACEHOLDER)


def _render_raw_body(canvas: _PdfCanvas, body_text: str) -> None:
    """Render raw recap Markdown blocks when no module sections were parsed.

    Mirrors the tolerant Raw_Body_Fallback of the rich renderer so a recap that
    does not match the module-heading schema still contributes its content to
    the PDF rather than being dropped. Content is rendered verbatim (bullets for
    list markers, otherwise wrapped prose) to keep every token intact for
    round-trip verification.

    Args:
        canvas: The canvas to draw into.
        body_text: The raw recap Markdown body.
    """
    for block in split_blocks(body_text):
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped[:2] in ("- ", "* ") or (
                stripped[:1].isdigit() and ". " in stripped[:4]
            ):
                # Drop only the leading list marker; render the item text.
                marker_end = stripped.find(" ") + 1
                canvas.bullet(stripped[marker_end:])
            else:
                canvas.body(line)


def render_minimal_pdf(
    doc: RecapDocument, out_path: str | Path, *, body_text: str = ""
) -> None:
    """Render a :class:`RecapDocument` to a valid PDF 1.4 using stdlib only.

    Draws a title and header, then one labeled section per module (Information
    Shared, Questions & Responses, Actions Taken, Duration, Journal) with word
    wrapping and automatic multi-page overflow. When the document has no parsed
    sections but ``body_text`` is supplied, the raw Markdown body is rendered
    instead so no content is dropped. The output is written atomically to
    ``out_path`` as a structurally valid PDF (header, object tree, cross-
    reference table, and ``%%EOF`` trailer).

    Args:
        doc: The parsed recap document to render.
        out_path: Destination path for the generated PDF.
        body_text: Raw recap Markdown for the fallback when ``doc`` has no
            sections. Ignored when ``doc.sections`` is non-empty.

    Raises:
        OSError: If the PDF cannot be written to ``out_path``.
    """
    canvas = _PdfCanvas()

    canvas.title("Senzing Bootcamp Recap")
    if doc.header.bootcamper and doc.header.bootcamper.strip():
        canvas.body(f"Bootcamper: {doc.header.bootcamper}")
    if doc.header.started and doc.header.started.strip():
        canvas.body(f"Started: {doc.header.started}")
    if doc.header.total_duration and doc.header.total_duration.strip():
        canvas.body(f"Total Duration: {doc.header.total_duration}")
    canvas.body(f"Modules completed: {len(doc.sections)}")

    if doc.sections:
        for section in doc.sections:
            _render_section(canvas, section)
    elif body_text.strip():
        _render_raw_body(canvas, body_text)

    pdf_bytes = _build_pdf(canvas.finish())
    Path(out_path).write_bytes(pdf_bytes)


# ---------------------------------------------------------------------------
# PDF assembly (objects, xref, trailer)
# ---------------------------------------------------------------------------

# Fixed object numbers for the shared, non-page objects.
_OBJ_CATALOG = 1
_OBJ_PAGES = 2
_OBJ_FONT_REGULAR = 3
_OBJ_FONT_BOLD = 4
_FIRST_PAGE_OBJ = 5  # page/content objects are numbered from here, two per page


def _build_pdf(pages: list[str]) -> bytes:
    """Assemble a complete PDF 1.4 byte string from per-page content streams.

    Builds the catalog, page tree, two Type1 font objects, and, for each page, a
    page object plus its (uncompressed) content-stream object. Records each
    object's byte offset to emit a correct cross-reference table, then writes the
    ``trailer``, ``startxref``, and ``%%EOF``.

    Args:
        pages: Per-page content-stream strings (drawing operators), in order.

    Returns:
        The full PDF file as bytes.
    """
    objects: list[tuple[int, bytes]] = []

    objects.append(
        (_OBJ_CATALOG, b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    )

    kids = " ".join(
        f"{_FIRST_PAGE_OBJ + 2 * i} 0 R" for i in range(len(pages))
    )
    objects.append(
        (
            _OBJ_PAGES,
            (
                f"2 0 obj\n<< /Type /Pages /Kids [{kids}] "
                f"/Count {len(pages)} >>\nendobj\n"
            ).encode("latin-1"),
        )
    )
    objects.append(
        (
            _OBJ_FONT_REGULAR,
            b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            b"/Encoding /WinAnsiEncoding >>\nendobj\n",
        )
    )
    objects.append(
        (
            _OBJ_FONT_BOLD,
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont "
            b"/Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n",
        )
    )

    for i, content in enumerate(pages):
        page_num = _FIRST_PAGE_OBJ + 2 * i
        content_num = page_num + 1
        page_obj = (
            f"{page_num} 0 obj\n"
            "<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH:g} {PAGE_HEIGHT:g}] "
            f"/Resources << /Font << /{FONT_REGULAR} 3 0 R "
            f"/{FONT_BOLD} 4 0 R >> >> "
            f"/Contents {content_num} 0 R >>\nendobj\n"
        ).encode("latin-1")
        data = content.encode("latin-1")
        stream_obj = (
            f"{content_num} 0 obj\n<< /Length {len(data)} >>\nstream\n".encode(
                "latin-1"
            )
            + data
            + b"\nendstream\nendobj\n"
        )
        objects.append((page_num, page_obj))
        objects.append((content_num, stream_obj))

    objects.sort(key=lambda item: item[0])
    object_count = objects[-1][0] + 1  # include the free object 0

    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"  # binary marker comment

    offsets: dict[int, int] = {}
    for number, payload in objects:
        offsets[number] = len(out)
        out += payload

    xref_offset = len(out)
    out += b"xref\n"
    out += f"0 {object_count}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for number in range(1, object_count):
        out += f"{offsets.get(number, 0):010d} 00000 n \n".encode("latin-1")

    out += b"trailer\n"
    out += f"<< /Size {object_count} /Root 1 0 R >>\n".encode("latin-1")
    out += b"startxref\n"
    out += f"{xref_offset}\n".encode("latin-1")
    out += b"%%EOF\n"

    return bytes(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Mirrors ``generate_recap_pdf.py`` so the scripts are interchangeable.

    Args:
        argv: Argument list to parse. Defaults to ``sys.argv[1:]``.

    Returns:
        Parsed namespace with ``input`` and ``output`` paths.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Render a valid PDF from the bootcamp recap markdown using only the "
            "Python standard library (no fpdf2)."
        ),
    )
    parser.add_argument(
        "--input",
        default="docs/bootcamp_recap.md",
        help="Path to recap markdown (default: docs/bootcamp_recap.md)",
    )
    parser.add_argument(
        "--output",
        default="docs/bootcamp_recap.pdf",
        help="Path for output PDF (default: docs/bootcamp_recap.pdf)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the stdlib-only recap PDF writer.

    Reads and parses the recap Markdown, renders it into a temporary PDF via
    :func:`render_minimal_pdf`, verifies the written PDF round-trips its module
    sections and body content, and only then publishes it atomically to the
    output path. On verification or write failure the temporary file is removed
    and no output is overwritten.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    args = parse_args(argv)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Recap file not found: {args.input}", file=sys.stderr)
        return 1
    content = input_path.read_text(encoding="utf-8")
    if not content.strip():
        print(f"Recap file is empty: {args.input}", file=sys.stderr)
        return 1

    doc = parse_recap_markdown(content)
    module_numbers, expected_body_lines = collect_verification_targets(doc, content)

    output_path = Path(args.output)
    directory = output_path.parent if str(output_path.parent) else Path(".")

    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(directory), prefix=f"{output_path.name}.", suffix=".tmp"
        )
        os.close(fd)
        render_minimal_pdf(doc, tmp_path, body_text=content)
        verify_rendered_pdf(tmp_path, module_numbers, expected_body_lines)
        os.replace(tmp_path, str(output_path))
        tmp_path = None
    except PdfVerificationError as exc:
        print(f"PDF verification failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to write PDF: {exc}", file=sys.stderr)
        return 1
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    print(f"PDF generated: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
