"""Journal-subsection fidelity tests for the recap PDF pipeline.

Feature: guaranteed-recap-pdf.

The bootcamp requires each module's recap to carry a first-class **Journal**
section (What we did / What was produced / Why it matters / Bootcamper's
takeaway). Before this work the ``### Journal`` subsection was not a recognized
subsection: it fell into generic content, was rendered inconsistently between
the two renderers (buried under "Additional Notes" in the rich renderer), and —
most seriously — was DROPPED entirely by ``format_recap_document`` (the recap
normalization consumer), so it could vanish before the PDF was rendered.

These tests pin the fixed behavior:

    parse            ``### Journal`` becomes ``RecapSection.journal`` (the four
                     narrative lines), excluding the ``---`` section separator.
    normalize        ``format_recap_section`` re-emits ``### Journal`` verbatim,
                     so a parse -> format round-trip preserves it (idempotent).
    verify targets   the journal lines are part of the round-trip verification
                     targets so a dropped journal fails verification.
    render (stdlib)  the stdlib writer renders a first-class "Journal" heading
                     and the journal content survives into the PDF text.
    render (rich)    the fpdf2 renderer renders a first-class "Journal" heading
                     (when fpdf2 is importable).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf as grp  # noqa: E402
import recap_pdf_minimal as rpm  # noqa: E402
import recap_pdf_render as rpr  # noqa: E402

_RECAP = """# Senzing Bootcamp Recap

**Bootcamper:** Ada
**Started:** 2026-05-14T10:30:00-05:00
**Total Duration:** 3h

---

## Module 1: Business Problem — 2026-05-14T11:00:00-05:00

### Information Shared
- Entity resolution basics

### Questions & Responses
- **Q:** What data sources?
    - **R:** Customers and vendors

### Actions Taken
- Created config/data_sources.yaml

### Duration
45 minutes

### Journal
**What we did:** Defined the business problem and data sources.
**What was produced:** config/data_sources.yaml
**Why it matters:** Focuses the rest of the bootcamp.
**Bootcamper's takeaway:** N/A

---
"""


def _fpdf2_available() -> bool:
    try:
        import fpdf  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


class TestJournalParsing:
    """``### Journal`` parses into ``RecapSection.journal``."""

    def test_journal_lines_captured(self) -> None:
        section = grp.parse_recap_markdown(_RECAP).sections[0]
        assert section.journal, "journal was not parsed into RecapSection.journal"
        joined = "\n".join(section.journal)
        assert "**What we did:**" in joined
        assert "**What was produced:**" in joined
        assert "**Why it matters:**" in joined
        assert "**Bootcamper's takeaway:**" in joined

    def test_thematic_break_excluded_from_journal(self) -> None:
        """The trailing ``---`` section separator never leaks into the journal."""
        section = grp.parse_recap_markdown(_RECAP).sections[0]
        assert all(line.strip() != "---" for line in section.journal), (
            f"journal captured a thematic break: {section.journal!r}"
        )


class TestJournalNormalizationRoundTrip:
    """``format_recap_section`` preserves the journal (normalization no longer drops it)."""

    def test_format_section_emits_journal(self) -> None:
        section = grp.parse_recap_markdown(_RECAP).sections[0]
        formatted = grp.format_recap_section(section)
        assert "### Journal" in formatted
        assert "**Bootcamper's takeaway:** N/A" in formatted

    def test_document_round_trip_is_idempotent(self) -> None:
        doc = grp.parse_recap_markdown(_RECAP)
        once = grp.format_recap_document(doc)
        twice = grp.format_recap_document(grp.parse_recap_markdown(once))
        # The journal survives a full normalization round-trip unchanged.
        assert grp.parse_recap_markdown(once).sections[0].journal == (
            doc.sections[0].journal
        )
        assert "### Journal" in once
        # Re-normalizing is stable (no journal growth / duplication).
        assert once == twice


class TestJournalVerificationTargets:
    """Journal lines are part of the round-trip verification targets."""

    def test_journal_lines_in_body_targets(self) -> None:
        doc = grp.parse_recap_markdown(_RECAP)
        _modules, body_lines = grp.collect_verification_targets(doc, _RECAP)
        assert any("Focuses the rest of the bootcamp" in line for line in body_lines)


class TestJournalStdlibRender:
    """The stdlib writer renders a first-class Journal section."""

    def test_journal_heading_and_content_survive(self, tmp_path: Path) -> None:
        doc = grp.parse_recap_markdown(_RECAP)
        out = tmp_path / "recap.pdf"
        rpm.render_minimal_pdf(doc, str(out), body_text=_RECAP)
        text = rpr.extract_pdf_text(out.read_bytes())
        assert "Journal" in text, "stdlib PDF has no Journal heading"
        assert "Focuses" in text, "journal content missing from stdlib PDF"

    def test_stdlib_render_passes_verification(self, tmp_path: Path) -> None:
        doc = grp.parse_recap_markdown(_RECAP)
        modules, body_lines = grp.collect_verification_targets(doc, _RECAP)
        out = tmp_path / "recap.pdf"
        rpm.render_minimal_pdf(doc, str(out), body_text=_RECAP)
        # Raises PdfVerificationError if the journal (or any module) was dropped.
        rpr.verify_rendered_pdf(str(out), modules, body_lines)


class TestJournalRichRender:
    """The fpdf2 renderer renders a first-class Journal section (when available)."""

    def test_journal_heading_and_content_survive(self, tmp_path: Path) -> None:
        if not _fpdf2_available():
            pytest.skip("fpdf2 not installed; rich renderer unavailable")
        doc = grp.parse_recap_markdown(_RECAP)
        out = tmp_path / "recap.pdf"
        grp.render_pdf(doc, str(out), body_text=_RECAP)
        text = rpr.extract_pdf_text(out.read_bytes())
        assert "Journal" in text, "rich PDF has no Journal heading"
        assert "Focuses" in text, "journal content missing from rich PDF"
