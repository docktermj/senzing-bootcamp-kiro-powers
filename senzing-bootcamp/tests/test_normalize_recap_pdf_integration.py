"""Integration test: normalized recap -> non-empty recap PDF body.

Feature: graduation-markdown-normalization (Task 10.1)

Proves the end-to-end chain that ties this feature to the
``recap-pdf-content-loss-fix`` expectations: a free-form recap, after the
graduation-time normalization pass (``normalize_markdown.normalize_recap`` /
``normalize_file`` on a ``docs/bootcamp_recap.md``), produces Markdown that
``generate_recap_pdf`` turns into a NON-EMPTY recap PDF body — never an empty
document.

The assertions are layered so the test is meaningful whether or not the
optional ``fpdf2`` dependency is installed:

* Data-level guarantee (ALWAYS): the normalized recap parses
  (``parse_recap_markdown``) into a ``RecapDocument`` whose body is non-empty
  (>= 1 section carrying content). This is the "non-empty PDF body" content
  guarantee at the data level — a normalized recap must NOT yield an empty body.
* Canonical-Markdown guarantee (ALWAYS): the canonical Markdown the PDF
  generator renders from (``format_recap_document``) is non-empty and carries
  the module content, independent of ``fpdf2``.
* PDF-bytes guarantee (only when ``fpdf2`` is installed): the actual PDF file is
  written and is non-trivially sized.

Scripts are imported via the project's ``sys.path`` pattern (scripts are not a
package). The scripts themselves are NOT modified by this test.

_Requirements: 8.4, 5.2, 5.3_
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make scripts importable (scripts are not a package).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf
import normalize_markdown

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

#: A deliberately free-form recap: a non-canonical title, header fields, and two
#: module sections whose headings carry the recognized "Module N: name —
#: timestamp" shape with recognized ### subsections holding real content. This is
#: the kind of in-flight Markdown the normalization pass is meant to conform.
_FREE_FORM_RECAP = """\
# My Bootcamp Notes

**Bootcamper:** Ada Lovelace
**Started:** 2025-01-01
**Total Duration:** 3h 30m

Some free-form intro prose that has no place in the strict schema.

## Module 1: Business Problem — 2025-01-01 10:00

### Information Shared
- Entity resolution dedupes records across sources
- Senzing runs on-prem or in the cloud

### Questions Asked
- What is a data source code?

### Answers Given
- A short label identifying the origin of records

### Actions Taken
- Reviewed the demo dataset

### Duration
45m

## Module 2: First Demo — 2025-01-01 11:00

### Information Shared
- The MCP server generates SDK code dynamically

### Questions Asked
- How do I load my own data?

### Answers Given
- Map it to the Senzing generic entity spec, then add records

### Actions Taken
- Loaded 100 sample records

### Duration
1h 15m
"""


def _section_has_content(section: "generate_recap_pdf.RecapSection") -> bool:
    """Return True when a parsed module section carries any substantive content."""
    return bool(
        section.information_shared
        or section.questions_asked
        or section.answers_given
        or section.actions_taken
        or section.duration
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNormalizedRecapPdfIntegration:
    """Normalized recap -> non-empty recap PDF body (Requirements 8.4, 5.2, 5.3)."""

    def _normalized_recap_via_file(self, tmp_path: Path) -> str:
        """Normalize a free-form recap through ``normalize_file`` on a tmp file.

        Writes the free-form recap to ``<tmp>/docs/bootcamp_recap.md`` so the
        schema normalizer is selected by path (mirroring the real graduation
        flow), runs ``normalize_file``, and returns the normalized file content.
        """
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        recap_path = docs_dir / "bootcamp_recap.md"
        recap_path.write_text(_FREE_FORM_RECAP, encoding="utf-8")

        result = normalize_markdown.normalize_file(str(recap_path))

        assert result.error is None, f"normalization failed: {result.error}"
        assert result.schema_applied, "recap schema normalizer should be applied"
        return recap_path.read_text(encoding="utf-8")

    def test_normalize_file_selects_recap_schema(self, tmp_path: Path) -> None:
        """A docs/bootcamp_recap.md under tmp is recognized as the recap schema."""
        normalized = self._normalized_recap_via_file(tmp_path)
        assert normalized.strip(), "normalized recap must not be empty"
        # Conforms to the canonical title the PDF parser expects.
        assert normalized.lstrip().startswith("# Senzing Bootcamp Recap")

    def test_normalized_recap_parses_to_non_empty_body(self, tmp_path: Path) -> None:
        """Data-level non-empty body guarantee (always runs, no fpdf2 needed).

        The normalized recap must parse into a RecapDocument with at least one
        section that carries content — i.e. a non-empty body. This is the
        content guarantee behind a non-empty PDF body and the core tie to
        recap-pdf-content-loss-fix: a normalized recap must NOT yield an empty
        body. (Requirements 8.4, 5.2)
        """
        normalized = self._normalized_recap_via_file(tmp_path)

        doc = generate_recap_pdf.parse_recap_markdown(normalized)

        assert doc.sections, "normalized recap must parse into >= 1 module section"
        sections_with_content = [s for s in doc.sections if _section_has_content(s)]
        assert sections_with_content, (
            "normalized recap PDF body must be non-empty "
            "(>= 1 section with content)"
        )

        # The originally-authored content survived the normalization round-trip.
        module_names = {s.module_name for s in doc.sections}
        assert "Business Problem" in module_names
        assert "First Demo" in module_names
        first = next(s for s in doc.sections if s.module_name == "Business Problem")
        assert first.information_shared, "module 1 information must be preserved"
        assert first.duration == "45m"

    def test_normalize_recap_direct_non_empty_body(self) -> None:
        """normalize_recap (direct call) also yields a non-empty parsed body.

        Exercises the schema normalizer directly (no file I/O) so the data-level
        guarantee holds regardless of how the pass is invoked. (Requirement 5.2)
        """
        normalized, _warnings = normalize_markdown.normalize_recap(_FREE_FORM_RECAP)

        doc = generate_recap_pdf.parse_recap_markdown(normalized)
        assert doc.sections
        assert any(_section_has_content(s) for s in doc.sections)

    def test_canonical_markdown_body_non_empty_without_fpdf(
        self, tmp_path: Path
    ) -> None:
        """The Markdown the PDF renders from is non-empty (no fpdf2 required).

        ``generate_recap_pdf.format_recap_document`` builds the canonical
        Markdown body from the parsed document; this is the body-building step
        that works without fpdf2. It must contain the module content for a
        normalized recap. (Requirements 8.4, 5.2)
        """
        normalized = self._normalized_recap_via_file(tmp_path)
        doc = generate_recap_pdf.parse_recap_markdown(normalized)

        body = generate_recap_pdf.format_recap_document(doc)

        assert body.strip(), "rendered recap Markdown body must be non-empty"
        assert "Module 1: Business Problem" in body
        assert "Module 2: First Demo" in body
        assert "Entity resolution dedupes records across sources" in body

    def test_normalized_recap_renders_non_empty_pdf(self, tmp_path: Path) -> None:
        """Actual PDF bytes are produced and non-trivially sized.

        Skipped only when the optional fpdf2 dependency is absent; the
        data-level guarantees above still run in that case. (Requirements
        8.4, 5.3)
        """
        pytest.importorskip(
            "fpdf",
            reason="fpdf2 not installed; PDF-bytes check skipped",
            exc_type=ImportError,
        )

        normalized = self._normalized_recap_via_file(tmp_path)
        doc = generate_recap_pdf.parse_recap_markdown(normalized)

        output_path = tmp_path / "bootcamp_recap.pdf"
        generate_recap_pdf.render_pdf(doc, str(output_path))

        assert output_path.is_file(), "PDF output file should be written"
        # A real multi-page recap PDF is well over 1 KB; an empty/degenerate
        # document would be far smaller. Use a conservative threshold.
        size = output_path.stat().st_size
        assert size > 1024, f"recap PDF body should be non-trivially sized, got {size} bytes"
