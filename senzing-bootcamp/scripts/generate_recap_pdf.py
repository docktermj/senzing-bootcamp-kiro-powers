#!/usr/bin/env python3
"""Generate a PDF from the bootcamp recap markdown document.

Converts docs/bootcamp_recap.md into a formatted PDF suitable for sharing
at bootcamp graduation. Uses stdlib for markdown parsing and fpdf2 for
PDF rendering.

Usage:
    python senzing-bootcamp/scripts/generate_recap_pdf.py
    python senzing-bootcamp/scripts/generate_recap_pdf.py --input recap.md
    python senzing-bootcamp/scripts/generate_recap_pdf.py --output recap.pdf

Recap schema:
    The parser recognizes module sections by a level-2 heading of the form::

        ## Module N: <name> [— <timestamp>]

    where ``N`` is the module number, ``<name>`` is the module title, and the
    optional ``— <timestamp>`` suffix uses an em-dash (U+2014). Headings written
    without the suffix (``## Module N: <name>``) are recognized too, parsing with
    an empty timestamp.

    Within a module, five ``###`` subsections are recognized by name:

        - Information Shared
        - Questions Asked
        - Answers Given
        - Actions Taken
        - Duration

    Any other content under a module — prose paragraphs, code blocks, or other
    headings — is not discarded. It renders generically as "Additional Notes"
    rather than being dropped. When no module sections parse at all, the raw
    Markdown body is rendered as a fallback so that no content is silently lost.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Canonical raw-Markdown → PDF rendering primitives (Shared_Renderer_Module).
# Scripts are not packages, so ensure this script's directory is importable to
# resolve the sibling module whether this file is run directly or imported via
# the documented sys.path pattern.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import (  # noqa: E402
    INDENT_UNIT,
    PdfVerificationError,
    extract_pdf_text,
    format_qr_section,
    render_generic_blocks,
    render_heading,
    render_indented_list_items,
    render_list_items,
    render_markdown_body,
    safe_text,
    split_blocks,
    verify_rendered_pdf,
)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class RecapHeader:
    """Header metadata for the recap document."""

    bootcamper: str = "Bootcamper"
    started: str = ""
    total_duration: str = ""


@dataclass
class QRPair:
    """One question and its corresponding response within a QR_Section.

    Attributes:
        question: Question text after the ``- **Q:** `` prefix, verbatim.
        response: Response text after the ``- **R:** `` prefix, verbatim (or a
            placeholder when the recorded response was absent/whitespace-only).
    """

    question: str = ""
    response: str = ""


@dataclass
class RecapSection:
    """A single module recap section."""

    module_number: int = 0
    module_name: str = ""
    timestamp: str = ""
    information_shared: list[str] = field(default_factory=list)
    # Paired_Schema: interspersed question/response pairs.
    qr_pairs: list[QRPair] = field(default_factory=list)
    # Split_List_Schema (legacy, retained for backward compatibility).
    questions_asked: list[str] = field(default_factory=list)
    answers_given: list[str] = field(default_factory=list)
    # Which schema this section was classified as: "paired" | "split" | "none".
    schema: str = "none"
    actions_taken: list[str] = field(default_factory=list)
    duration: str = ""
    generic_content: list[str] = field(default_factory=list)


@dataclass
class RecapDocument:
    """Complete parsed recap document."""

    header: RecapHeader = field(default_factory=RecapHeader)
    sections: list[RecapSection] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Markdown Parser
# ---------------------------------------------------------------------------

_HEADER_BOOTCAMPER_RE = re.compile(r"^\*\*Bootcamper:\*\*\s*(.+)$", re.MULTILINE)
_HEADER_STARTED_RE = re.compile(r"^\*\*Started:\*\*\s*(.+)$", re.MULTILINE)
_HEADER_DURATION_RE = re.compile(r"^\*\*Total Duration:\*\*\s*(.+)$", re.MULTILINE)

_MODULE_HEADING_RE = re.compile(
    r"^##\s+Module\s+(\d+):\s+(.+?)\s+—\s+(.+)$", re.MULTILINE
)

# Tolerant fallback: a module heading without the " — <timestamp>" suffix,
# e.g. "## Module 1: Business Problem". Used only when the strict pattern
# matches nothing so Strict_Schema recaps keep identical behavior.
_MODULE_HEADING_LOOSE_RE = re.compile(
    r"^##\s+Module\s+(\d+):\s+(.+?)\s*$", re.MULTILINE
)


def _parse_header(content: str) -> RecapHeader:
    """Extract header fields from the recap markdown.

    Args:
        content: Full markdown content.

    Returns:
        Populated RecapHeader.
    """
    header = RecapHeader()

    m = _HEADER_BOOTCAMPER_RE.search(content)
    if m:
        header.bootcamper = m.group(1).strip()

    m = _HEADER_STARTED_RE.search(content)
    if m:
        header.started = m.group(1).strip()

    m = _HEADER_DURATION_RE.search(content)
    if m:
        header.total_duration = m.group(1).strip()

    return header


def _extract_list_items(text: str) -> list[str]:
    """Extract list items (bulleted or numbered) from a subsection block.

    Args:
        text: Text block containing list items.

    Returns:
        List of item strings with leading markers removed.
    """
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        # Match "- item" or "1. item" or "2. item" etc.
        m = re.match(r"^(?:-|\d+\.)\s+(.+)$", stripped)
        if m:
            items.append(m.group(1))
    return items


# Subsection names recognized by the strict schema (lowercased).
_KNOWN_SUBSECTIONS = frozenset(
    {
        "information shared",
        "questions asked",
        "answers given",
        "questions & responses",
        "actions taken",
        "duration",
    }
)

# Paired_Schema list-item prefixes (mirror the literals in recap_pdf_render).
_QR_QUESTION_PREFIX = "- **Q:** "
_QR_RESPONSE_PREFIX = "- **R:** "

# Split_List_Schema placeholder for an unmatched question or answer (a
# question/answer numbered N with no counterpart of the same number). Renders
# in place of the missing counterpart so the item is never dropped
# (Requirement 5.4).
_SPLIT_UNMATCHED_PLACEHOLDER = "(no matching entry)"

# Module-section heading detectors used for per-section schema classification.
_QR_HEADING_RE = re.compile(
    r"^###\s+Questions & Responses\s*$", re.MULTILINE | re.IGNORECASE
)
_QUESTIONS_ASKED_HEADING_RE = re.compile(
    r"^###\s+Questions Asked\s*$", re.MULTILINE | re.IGNORECASE
)
_ANSWERS_GIVEN_HEADING_RE = re.compile(
    r"^###\s+Answers Given\s*$", re.MULTILINE | re.IGNORECASE
)


def classify_section(section_text: str) -> str:
    """Classify a module section as Paired_Schema, Split_List_Schema, or none.

    Classification is per section (never per document) so a recap mixing the
    new and legacy formats renders each section by its own headings
    (Requirement 5.5):

    * ``"paired"`` when the section has a ``### Questions & Responses`` heading.
    * ``"split"`` when it has both ``### Questions Asked`` and
      ``### Answers Given`` headings.
    * ``"none"`` otherwise.

    Args:
        section_text: Text of a single module section (after the ## heading).

    Returns:
        The schema label: ``"paired"``, ``"split"``, or ``"none"``.
    """
    if _QR_HEADING_RE.search(section_text):
        return "paired"
    if _QUESTIONS_ASKED_HEADING_RE.search(
        section_text
    ) and _ANSWERS_GIVEN_HEADING_RE.search(section_text):
        return "split"
    return "none"


def parse_qr_section(text: str) -> list[QRPair]:
    """Parse a ``### Questions & Responses`` body into ordered QR_Pairs.

    Pairs each Question_Item (a line whose leading spaces are followed by the
    ``- **Q:** `` prefix) with the immediately following Response_Item (the
    ``- **R:** `` prefix). The ``- **Q:** `` / ``- **R:** `` prefixes and the
    response indentation are dropped while the remaining text is preserved
    character-for-character. Continuation lines of a multi-line response (the
    indented lines following its Response_Item) fold back into the response with
    their canonical four-space indent removed, so ``parse_qr_section`` is the
    exact inverse of :func:`recap_pdf_render.format_qr_section` over substantive
    pairs. A ``- None`` body yields zero pairs. Responses indented by more than
    four spaces are tolerated (only leading ASCII spaces are stripped).

    Args:
        text: The QR_Section body (the text after the
            ``### Questions & Responses`` heading).

    Returns:
        The QR_Pairs in first-to-last document order.
    """
    pairs: list[QRPair] = []
    question: str | None = None
    response_lines: list[str] | None = None

    def commit() -> None:
        nonlocal question, response_lines
        if question is not None and response_lines is not None:
            pairs.append(
                QRPair(question=question, response="\n".join(response_lines))
            )
        question = None
        response_lines = None

    # Split on "\n" only — the exact line separator `format_qr_section` joins
    # with — so `parse_qr_section` is a true inverse. `str.splitlines()` would
    # over-split on Latin-1 line-boundary control characters (e.g. U+0085 NEL,
    # 0x0B, 0x0C, 0x1C-0x1E) that the formatter treats as ordinary in-line text,
    # injecting a spurious break between a Question_Item and its Response_Item.
    for line in text.split("\n"):
        content = line.lstrip(" ")
        if content.startswith(_QR_QUESTION_PREFIX):
            commit()
            question = content[len(_QR_QUESTION_PREFIX):]
        elif content.startswith(_QR_RESPONSE_PREFIX) and question is not None:
            response_lines = [content[len(_QR_RESPONSE_PREFIX):]]
        elif response_lines is not None and line.startswith(" "):
            # Indented continuation line of the current multi-line response;
            # strip the canonical four-space indent, preserving deeper indents.
            response_lines.append(line[INDENT_UNIT:])
        else:
            # A blank line or unrelated content ends the current pair.
            commit()

    commit()
    return pairs


def _split_subsections(section_text: str) -> tuple[dict[str, str], list[str]]:
    """Split a module section into its ### subsections and leftover content.

    Args:
        section_text: Text of a single module section (after the ## heading).

    Returns:
        Tuple of (subsections, generic_blocks) where ``subsections`` maps the
        subsection name (lowercase) to its body text, and ``generic_blocks`` is
        the renderable leftover content not belonging to a known subsection —
        the preamble before the first ``###`` plus any unrecognized
        ``### `` subsection (heading included), split into blocks.
    """
    subsections: dict[str, str] = {}
    parts = re.split(r"^###\s+(.+)$", section_text, flags=re.MULTILINE)

    # parts[0] is text before the first ###; it is always generic content.
    leftover = parts[0]

    # Then alternating name/body pairs.
    i = 1
    while i < len(parts) - 1:
        raw_name = parts[i].strip()
        name = raw_name.lower()
        body = parts[i + 1]
        if name in _KNOWN_SUBSECTIONS:
            subsections[name] = body
        else:
            # Unrecognized heading — preserve it as generic content.
            leftover += f"\n### {raw_name}\n{body}"
        i += 2

    return subsections, split_blocks(leftover)


def _parse_sections(content: str) -> list[RecapSection]:
    """Parse all module sections from the recap markdown.

    Tries the strict heading pattern first so Strict_Schema recaps parse
    exactly as before. When no strict headings match, falls back to the
    tolerant pattern (headings without the " — <timestamp>" suffix) and
    records an empty ``timestamp``. This function never raises.

    Args:
        content: Full markdown content.

    Returns:
        List of RecapSection objects in document order.
    """
    sections: list[RecapSection] = []

    # Find all module heading positions, preferring the strict pattern.
    headings = list(_MODULE_HEADING_RE.finditer(content))
    loose = False
    if not headings:
        headings = list(_MODULE_HEADING_LOOSE_RE.finditer(content))
        loose = True
    if not headings:
        return sections

    for idx, heading_match in enumerate(headings):
        # The loose pattern has no timestamp group; use an empty timestamp.
        timestamp = "" if loose else heading_match.group(3).strip()
        section = RecapSection(
            module_number=int(heading_match.group(1)),
            module_name=heading_match.group(2).strip(),
            timestamp=timestamp,
        )

        # Determine the text block for this section
        start = heading_match.end()
        if idx + 1 < len(headings):
            end = headings[idx + 1].start()
        else:
            end = len(content)

        section_text = content[start:end]

        # Split into subsections (plus leftover Generic_Content)
        subsections, generic_content = _split_subsections(section_text)
        section.generic_content = generic_content

        # Per-section schema classification (Requirement 5.5).
        section.schema = classify_section(section_text)

        section.information_shared = _extract_list_items(
            subsections.get("information shared", "")
        )
        section.questions_asked = _extract_list_items(
            subsections.get("questions asked", "")
        )
        section.answers_given = _extract_list_items(
            subsections.get("answers given", "")
        )
        section.actions_taken = _extract_list_items(
            subsections.get("actions taken", "")
        )

        # Paired_Schema QR_Pairs (Requirements 4.1, 4.3, 4.4).
        if "questions & responses" in subsections:
            section.qr_pairs = parse_qr_section(
                subsections["questions & responses"]
            )

        # Duration is plain text, not a list
        duration_text = subsections.get("duration", "").strip()
        # Take the first non-empty line as the duration value
        for line in duration_text.splitlines():
            stripped = line.strip()
            if stripped:
                section.duration = stripped
                break

        sections.append(section)

    return sections


def parse_recap_markdown(content: str) -> RecapDocument:
    """Parse a recap markdown document into structured data.

    Args:
        content: Full markdown content of the recap document.

    Returns:
        RecapDocument with header and sections populated.
    """
    return RecapDocument(
        header=_parse_header(content),
        sections=_parse_sections(content),
    )


# ---------------------------------------------------------------------------
# Markdown Formatter
# ---------------------------------------------------------------------------


def format_recap_section(section: RecapSection) -> str:
    """Format a RecapSection as markdown text.

    Args:
        section: The section to format.

    Returns:
        Markdown string for the section including heading and all subsections.
    """
    lines: list[str] = []

    lines.append(
        f"## Module {section.module_number}: {section.module_name}"
        f" \u2014 {section.timestamp}"
    )
    lines.append("")

    # Information Shared
    lines.append("### Information Shared")
    if section.information_shared:
        for item in section.information_shared:
            lines.append(f"- {item}")
    lines.append("")

    # Questions & Responses (Paired_Schema) or the legacy split lists.
    if section.schema == "paired":
        # Re-emit the QR_Section verbatim via the canonical formatter so a
        # normalization round-trip preserves the Paired_Schema intact and is
        # idempotent (Requirements 4.1, 4.3, 4.4, 5.5).
        lines.append(
            format_qr_section(
                [(pair.question, pair.response) for pair in section.qr_pairs]
            )
        )
        lines.append("")
    else:
        # Questions Asked
        lines.append("### Questions Asked")
        if section.questions_asked:
            for i, item in enumerate(section.questions_asked, 1):
                lines.append(f"{i}. {item}")
        lines.append("")

        # Answers Given
        lines.append("### Answers Given")
        if section.answers_given:
            for i, item in enumerate(section.answers_given, 1):
                lines.append(f"{i}. {item}")
        lines.append("")

    # Actions Taken
    lines.append("### Actions Taken")
    if section.actions_taken:
        for item in section.actions_taken:
            lines.append(f"- {item}")
    lines.append("")

    # Duration
    lines.append("### Duration")
    lines.append(section.duration)
    lines.append("")

    return "\n".join(lines)


def format_recap_document(doc: RecapDocument) -> str:
    """Format a complete RecapDocument as markdown text.

    Args:
        doc: The document to format.

    Returns:
        Full markdown string for the recap document.
    """
    lines: list[str] = []

    # Title
    lines.append("# Senzing Bootcamp Recap")
    lines.append("")

    # Header fields
    lines.append(f"**Bootcamper:** {doc.header.bootcamper}")
    lines.append(f"**Started:** {doc.header.started}")
    lines.append(f"**Total Duration:** {doc.header.total_duration}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sections
    for section in doc.sections:
        lines.append(format_recap_section(section))
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF Renderer
# ---------------------------------------------------------------------------


def _render_cover_page(pdf: "FPDF", doc: RecapDocument) -> None:  # noqa: F821
    """Render the cover page with title, bootcamper name, dates, and duration.

    Args:
        pdf: The FPDF instance to render into.
        doc: Parsed recap document.
    """
    pdf.add_page()
    pdf.ln(40)

    # Title
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 14, "Senzing Bootcamp Recap", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)

    # Bootcamper name
    pdf.set_font("Helvetica", "", 18)
    pdf.cell(
        0,
        10,
        safe_text(doc.header.bootcamper),
        new_x="LMARGIN",
        new_y="NEXT",
        align="C",
    )
    pdf.ln(10)

    # Started date
    if doc.header.started:
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(
            0,
            8,
            f"Started: {safe_text(doc.header.started)}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        pdf.ln(4)

    # Total duration
    if doc.header.total_duration:
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(
            0,
            8,
            f"Total Duration: {safe_text(doc.header.total_duration)}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )


def _build_qa_lines(questions: list[str], answers: list[str]) -> list[str]:
    """Build the ordered Q/A line sequence for the merged section.

    Pairs questions and answers by index, emitting ``Q: <question>`` immediately
    followed by ``A: <answer>`` for each index. Iterates over the longer of the
    two lists so unequal lengths never drop content; a missing counterpart emits
    the explicit placeholder ``(no matching entry)`` (Requirement 5.4) rather
    than misaligning later pairs.

    This is a pure helper with no PDF side effects, so the ordering and pairing
    can be unit-tested without rendering binary PDF output.

    Args:
        questions: Question strings in order.
        answers: Answer strings in order (parallel to ``questions`` by index).

    Returns:
        Ordered list of label-prefixed line strings (e.g. ``['Q: ...', 'A: ...']``)
        with the answer for index ``i`` immediately following its question.
    """
    lines: list[str] = []
    for i in range(max(len(questions), len(answers))):
        if i < len(questions):
            lines.append(f"Q: {questions[i]}")
        else:
            lines.append(f"Q: {_SPLIT_UNMATCHED_PLACEHOLDER}")
        if i < len(answers):
            lines.append(f"A: {answers[i]}")
        else:
            lines.append(f"A: {_SPLIT_UNMATCHED_PLACEHOLDER}")
    return lines


def _render_qa_pairs(
    pdf: "FPDF",  # noqa: F821
    questions: list[str],
    answers: list[str],
) -> None:
    """Render questions and answers as inline Q/A pairs under one section.

    Pairs by index: question ``i`` is rendered as ``Q: <question>`` immediately
    followed by ``A: <answer>``. Iterates over the longer of the two lists so
    nothing is dropped; a missing counterpart renders the explicit placeholder
    ``(no matching entry)`` (Requirement 5.4) rather than misaligning later
    pairs. Reuses the inline-code handling used by ``render_list_items`` so
    backtick spans render in the monospace font.

    Args:
        pdf: The FPDF instance.
        questions: Question strings in order.
        answers: Answer strings in order (parallel to ``questions`` by index).
    """
    pdf.set_font("Helvetica", "", 11)
    for line in _build_qa_lines(questions, answers):
        # Handle inline code (backtick content) with monospace font. The
        # "Q: "/"A: " prefixes contain no backticks, so splitting the whole
        # line keeps any inline code inside the content rendering in monospace.
        parts = re.split(r"`([^`]+)`", line)
        pdf.set_x(pdf.l_margin + 6)
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


def _render_qr_pairs(
    pdf: "FPDF",  # noqa: F821
    qr_pairs: list[QRPair],
) -> None:
    """Render Paired_Schema QR_Pairs through the indent-aware renderer.

    Each QR_Pair becomes two ``(level, text)`` render items: the Question_Item
    at level 0 (``- **Q:** <question>``) immediately followed by its
    Response_Item at level 1 (``- **R:** <response>``), so the response nests
    visibly beneath its question in the PDF (Requirements 3.2, 4.4). First-to-
    last order and question/response adjacency are preserved. The ``- **Q:** ``
    / ``- **R:** `` prefix literals mirror the Paired_Schema authored Markdown.

    Args:
        pdf: The FPDF instance.
        qr_pairs: The module's QR_Pairs in first-to-last order.
    """
    items: list[tuple[int, str]] = []
    for pair in qr_pairs:
        items.append((0, f"{_QR_QUESTION_PREFIX}{pair.question}"))
        items.append((1, f"{_QR_RESPONSE_PREFIX}{pair.response}"))
    render_indented_list_items(pdf, items)


def _render_module_page(pdf: "FPDF", section: RecapSection) -> None:  # noqa: F821
    """Render a single module section on a new page.

    Args:
        pdf: The FPDF instance.
        section: The module recap section to render.
    """
    pdf.add_page()

    # Module heading
    heading = f"Module {section.module_number}: {section.module_name}"
    render_heading(pdf, heading, level=2)

    # Timestamp
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(
        0,
        6,
        f"Completed: {safe_text(section.timestamp)}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    # Information Shared
    render_heading(pdf, "Information Shared", level=3)
    if section.information_shared:
        render_list_items(pdf, section.information_shared, numbered=False)
    else:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 6, "None", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Questions and responses — rendered per this section's classified schema.
    if section.schema == "paired":
        # Paired_Schema: interspersed QR_Pairs under a single heading, each
        # response nested one level beneath its question (Requirements 3.2,
        # 3.5, 4.4).
        render_heading(pdf, "Questions & Responses", level=3)
        if section.qr_pairs:
            _render_qr_pairs(pdf, section.qr_pairs)
        else:
            pdf.set_font("Helvetica", "I", 11)
            pdf.cell(0, 6, "None", new_x="LMARGIN", new_y="NEXT")
    else:
        # Split_List_Schema (or none): pair answer N with question N, in
        # ascending numeric order, with the (no matching entry) placeholder for
        # any unmatched counterpart (Requirements 5.1, 5.3, 5.4).
        render_heading(pdf, "Questions and responses", level=3)
        if section.questions_asked or section.answers_given:
            _render_qa_pairs(pdf, section.questions_asked, section.answers_given)
        else:
            pdf.set_font("Helvetica", "I", 11)
            pdf.cell(0, 6, "None", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Actions Taken
    render_heading(pdf, "Actions Taken", level=3)
    if section.actions_taken:
        render_list_items(pdf, section.actions_taken, numbered=False)
    else:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 6, "None", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Duration
    render_heading(pdf, "Duration", level=3)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(
        0,
        6,
        safe_text(section.duration) or "N/A",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    # Generic_Content — prose, code blocks, and other headings the strict
    # parser would otherwise discard. Rendered after the five known subsections.
    if section.generic_content:
        render_heading(pdf, "Additional Notes", level=3)
        render_generic_blocks(pdf, section.generic_content)


def render_pdf(doc: RecapDocument, output_path: str, body_text: str = "") -> None:
    """Render a RecapDocument as a formatted PDF file.

    Imports fpdf2 lazily so the module can be imported for parsing-only use
    without requiring fpdf2 to be installed. When the document has structured
    sections they are rendered per-module exactly as before. When no sections
    were parsed but ``body_text`` is non-empty, the raw Markdown body is rendered
    after the cover page (Raw_Body_Fallback) so no content is silently dropped.

    Args:
        doc: Parsed recap document to render.
        output_path: File path for the generated PDF.
        body_text: Raw recap Markdown used for the fallback when no structured
            sections are present. Ignored when ``doc.sections`` is non-empty.

    Raises:
        ImportError: If fpdf2 is not installed.
        OSError: If the PDF cannot be written to the output path.
    """
    from fpdf import FPDF  # noqa: PLC0415

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover page
    _render_cover_page(pdf, doc)

    if doc.sections:
        # Structured path — unchanged when sections are present.
        for section in doc.sections:
            _render_module_page(pdf, section)
    elif body_text.strip():
        # Raw_Body_Fallback — render the raw Markdown so nothing is dropped.
        pdf.add_page()
        render_markdown_body(pdf, body_text)

    pdf.output(output_path)


def collect_verification_targets(
    doc: RecapDocument, body_text: str = ""
) -> tuple[list[int], list[str]]:
    """Collect the per-module numbers and body lines a rendered PDF must contain.

    Mirrors what :func:`render_pdf` emits: when the document has structured
    sections, every section contributes its module number plus its body lines
    (Information Shared, Questions/Answers, Actions Taken, Duration, and any
    captured Generic_Content). When no sections parsed, the raw Markdown body is
    rendered via the fallback, so the renderable blocks of ``body_text`` are the
    expected body lines and there are no per-module sections to assert.

    Args:
        doc: Parsed recap document to render.
        body_text: Raw recap Markdown used for the Raw_Body_Fallback. Ignored
            when ``doc.sections`` is non-empty.

    Returns:
        A ``(module_numbers, expected_body_lines)`` tuple for
        :func:`recap_pdf_render.verify_rendered_pdf`.
    """
    if doc.sections:
        module_numbers = [section.module_number for section in doc.sections]
        body_lines: list[str] = []
        for section in doc.sections:
            body_lines.extend(section.information_shared)
            # Paired_Schema QR_Pairs contribute their question and response text
            # so a dropped pair fails verification; Split_List_Schema sections
            # contribute their two numbered lists.
            for pair in section.qr_pairs:
                body_lines.append(pair.question)
                body_lines.append(pair.response)
            body_lines.extend(section.questions_asked)
            body_lines.extend(section.answers_given)
            body_lines.extend(section.actions_taken)
            if section.duration:
                body_lines.append(section.duration)
            body_lines.extend(section.generic_content)
        return module_numbers, body_lines

    return [], split_blocks(body_text)


def _distinctive_token(line: str) -> str | None:
    """Return the longest Latin-1-safe token (length >= 2) of a body line.

    Mirrors :func:`recap_pdf_render._distinctive_token` so the offending-content
    identifier below uses the same wrap-robust marker the verifier relies on.

    Args:
        line: A source body line (question, response, or numbered item).

    Returns:
        The longest whitespace-delimited token of length >= 2, or ``None`` when
        the line has no such token.
    """
    tokens = [tok for tok in safe_text(line).split() if len(tok) >= 2]
    if not tokens:
        return None
    return max(tokens, key=len)


def identify_unrendered_content(pdf_path: str, doc: RecapDocument) -> str | None:
    """Best-effort: name the first QR_Pair / numbered item missing from a PDF.

    Re-opens the rendered (temporary) PDF, extracts its text, and returns a
    human-readable description of the first QR_Pair (Paired_Schema) or numbered
    question/answer (Split_List_Schema) whose distinctive token did not survive
    into the rendered text. Used to enrich the stderr error on a verification
    failure (Requirements 4.2, 5.2). Returns ``None`` when nothing specific can
    be pinpointed (e.g. the PDF text cannot be read back).

    Args:
        pdf_path: Path to the rendered PDF to inspect.
        doc: The parsed recap document whose content was rendered.

    Returns:
        A description of the offending content, or ``None`` when none can be
        identified.
    """
    try:
        text = extract_pdf_text(Path(pdf_path).read_bytes())
    except (OSError, ValueError):
        return None
    text_tokens = set(text.split())

    def missing(line: str) -> bool:
        token = _distinctive_token(line)
        return token is not None and token not in text_tokens

    for section in doc.sections:
        mod = section.module_number
        for idx, pair in enumerate(section.qr_pairs, 1):
            if missing(pair.question):
                return (
                    f"Module {mod}, QR_Pair #{idx} question: "
                    f"{pair.question!r}"
                )
            if missing(pair.response):
                return (
                    f"Module {mod}, QR_Pair #{idx} response: "
                    f"{pair.response!r}"
                )
        for idx, question in enumerate(section.questions_asked, 1):
            if missing(question):
                return f"Module {mod}, question #{idx}: {question!r}"
        for idx, answer in enumerate(section.answers_given, 1):
            if missing(answer):
                return f"Module {mod}, answer #{idx}: {answer!r}"
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with input and output paths.
    """
    parser = argparse.ArgumentParser(
        description="Generate a PDF from the bootcamp recap markdown document.",
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
    """Entry point for recap PDF generation.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    args = parse_args(argv)
    input_path = Path(args.input)

    # Check if input file exists
    if not input_path.exists():
        print(f"Recap file not found: {args.input}", file=sys.stderr)
        return 1

    # Read input file and check if empty
    content = input_path.read_text(encoding="utf-8")
    if not content.strip():
        print(f"Recap file is empty: {args.input}", file=sys.stderr)
        return 1

    # Parse markdown content
    doc = parse_recap_markdown(content)

    # Detect under-population: compare the module headings present in the source
    # (counted with the tolerant pattern, which also matches strict headings) to
    # the number of sections the parser actually produced. A shortfall — or zero
    # sections for a non-empty body — means content was rendered via the
    # Raw_Body_Fallback or some modules were dropped, so warn (Req 2.4).
    detected_headings = len(_MODULE_HEADING_LOOSE_RE.findall(content))
    parsed_sections = len(doc.sections)

    # Render + verify + publish atomically. Render into a temporary file in the
    # same directory as the output, run round-trip verification against that
    # temp file, and only move it into place on success (os.replace is atomic on
    # the same filesystem). On verification failure the temp file is removed so
    # NO recap PDF is written or overwritten, an error identifying the offending
    # QR_Pair / numbered item is printed to stderr, and we return 1
    # (Requirements 4.1, 4.2, 5.1, 5.2). Degrade gracefully when fpdf2 is absent
    # (leave the Markdown intact) and report genuine write/move failures.
    module_numbers, expected_body_lines = collect_verification_targets(doc, content)
    output_path = Path(args.output)
    directory = output_path.parent if str(output_path.parent) else Path(".")

    tmp_path: str | None = None
    try:
        # mkstemp raises OSError (e.g. the target directory is missing), matching
        # the previous direct-write OSError contract.
        fd, tmp_path = tempfile.mkstemp(
            dir=str(directory), prefix=f"{output_path.name}.", suffix=".tmp"
        )
        os.close(fd)
        render_pdf(doc, tmp_path, body_text=content)
        verify_rendered_pdf(tmp_path, module_numbers, expected_body_lines)
        os.replace(tmp_path, str(output_path))
        tmp_path = None  # Published — nothing left to clean up.
    except ImportError:
        print(
            "fpdf2 is required. Install with: pip install fpdf2",
            file=sys.stderr,
        )
        return 1
    except PdfVerificationError as exc:
        offending = (
            identify_unrendered_content(tmp_path, doc) if tmp_path else None
        )
        detail = f" Offending content: {offending}" if offending else ""
        print(f"PDF verification failed: {exc}{detail}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to write PDF: {exc}", file=sys.stderr)
        return 1
    finally:
        # Always clean up the temp file on any failure path so a rejected render
        # never lingers beside the recap.
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # Emit the under-population warning to stderr only, preserving the stdout
    # `PDF generated:` contract and the exit-code-0 success path (Req 2.4, 3.1).
    if parsed_sections == 0:
        print(
            f"Warning: no module sections were parsed from {args.input}; "
            "the recap body was rendered as raw Markdown. Check that module "
            "headings use the form '## Module N: <name> [\u2014 <timestamp>]'.",
            file=sys.stderr,
        )
    elif parsed_sections < detected_headings:
        print(
            f"Warning: parsed only {parsed_sections} of {detected_headings} "
            f"module heading(s) in {args.input}; some content may not be fully "
            "structured in the PDF.",
            file=sys.stderr,
        )

    print(f"PDF generated: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
