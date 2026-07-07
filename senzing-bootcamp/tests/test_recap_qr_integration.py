"""End-to-end integration test for both recap PDF generators.

Feature: recap-qr-formatting

Exercises the two recap PDF generators — the Bundled_Generator
(``generate_recap_pdf.py``) and the Inline_Generator
(``generate_recap_pdf_inline.py``) — against a single recap that MIXES a
Paired_Schema module section (``### Questions & Responses`` with
``- **Q:**`` / ``    - **R:**`` pairs) and a legacy Split_List_Schema module
section (``### Questions Asked`` + ``### Answers Given`` numbered lists).

These are example-based integration tests (one representative mixed recap), not
property-based: PDF generation is comparatively expensive and the binary output
does not vary meaningfully with input beyond what the pure property suites
already cover.

Validates:
    Requirement 3.1 — the renderer honors indentation depth (paired content
        nests and survives rendering).
    Requirement 4.1 — every QR_Pair present in the recap is rendered (round-trip
        verification inside ``main`` passes).
    Requirement 5.1 — every legacy split-list question and answer is rendered.
    Requirement 5.5 — a recap mixing paired and split sections classifies and
        renders each section by its own schema.

PDF generation requires the optional ``fpdf2`` dependency; the whole module is
guarded with ``pytest.importorskip("fpdf")``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# PDF generation requires fpdf2 (import name ``fpdf``). Skip the whole module
# when it is absent so environments without the optional dependency stay green.
pytest.importorskip("fpdf")

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf  # noqa: E402
import generate_recap_pdf_inline  # noqa: E402
from recap_pdf_render import extract_pdf_text  # noqa: E402

# ---------------------------------------------------------------------------
# Mixed-schema recap fixture (one Paired_Schema + one Split_List_Schema module).
# ---------------------------------------------------------------------------

# Distinctive text so extracted PDF tokens are unambiguous. The em-dash (U+2014)
# separates the module name from the timestamp per the recap heading schema.
_PAIRED_Q1 = "What problem does entity resolution solve?"
_PAIRED_R1 = "It links records that refer to the same real-world entity."
_PAIRED_Q2 = "Which datasource format is expected?"
_PAIRED_R2 = "A mapped JSON document with a DATA_SOURCE and RECORD_ID."

_SPLIT_Q1 = "How is a license configured?"
_SPLIT_Q2 = "Where does the engine write results?"
_SPLIT_A1 = "Through the SENZING_ENGINE_CONFIGURATION_JSON setting."
_SPLIT_A2 = "Into the configured Senzing repository."

MIXED_RECAP = (
    "# Senzing Bootcamp Recap\n"
    "\n"
    "**Bootcamper:** Integration Tester\n"
    "**Started:** 2025-01-01T09:00:00-05:00\n"
    "**Total Duration:** 2h 0m\n"
    "\n"
    "---\n"
    "\n"
    # Paired_Schema module section.
    "## Module 1: Entity Resolution Intro \u2014 2025-01-01T10:00:00-05:00\n"
    "\n"
    "### Information Shared\n"
    "- Core entity-resolution concepts\n"
    "\n"
    "### Questions & Responses\n"
    "\n"
    f"- **Q:** {_PAIRED_Q1}\n"
    f"    - **R:** {_PAIRED_R1}\n"
    f"- **Q:** {_PAIRED_Q2}\n"
    f"    - **R:** {_PAIRED_R2}\n"
    "\n"
    "### Actions Taken\n"
    "- Reviewed the mapping guide\n"
    "\n"
    "### Duration\n"
    "1h 0m\n"
    "\n"
    "---\n"
    "\n"
    # Legacy Split_List_Schema module section.
    "## Module 2: Licensing \u2014 2025-01-01T11:00:00-05:00\n"
    "\n"
    "### Information Shared\n"
    "- Licensing and configuration basics\n"
    "\n"
    "### Questions Asked\n"
    f"1. {_SPLIT_Q1}\n"
    f"2. {_SPLIT_Q2}\n"
    "\n"
    "### Answers Given\n"
    f"1. {_SPLIT_A1}\n"
    f"2. {_SPLIT_A2}\n"
    "\n"
    "### Actions Taken\n"
    "- Configured the engine\n"
    "\n"
    "### Duration\n"
    "1h 0m\n"
    "\n"
    "---\n"
)

# The distinctive tokens whose presence in extracted PDF text proves each
# question/response/answer rendered. Wrapping only ever splits at whitespace, so
# an individual long token survives intact into the extracted text.
_PAIRED_TOKENS = ("resolution", "real-world", "datasource", "DATA_SOURCE")
_SPLIT_TOKENS = (
    "license",
    "SENZING_ENGINE_CONFIGURATION_JSON",
    "engine",
    "repository",
)


def _write_recap(tmp_path: Path) -> str:
    """Write the mixed-schema recap fixture and return its path.

    Args:
        tmp_path: The per-test temporary directory.

    Returns:
        The path to the written recap Markdown file, as a string.
    """
    recap_md = tmp_path / "bootcamp_recap.md"
    recap_md.write_text(MIXED_RECAP, encoding="utf-8")
    return str(recap_md)


class TestRecapQRIntegration:
    """End-to-end integration for the bundled and inline recap PDF generators.

    Validates: Requirements 3.1, 4.1, 5.1, 5.5
    """

    def test_bundled_generator_renders_mixed_recap(self, tmp_path: Path) -> None:
        """The Bundled_Generator renders a mixed paired/split recap end to end.

        Running ``generate_recap_pdf.main`` returns 0 (round-trip verification
        inside ``main`` passed), writes the PDF, and the extracted text contains
        the ``Questions & Responses`` heading, both paired questions/responses,
        and the split section's questions/answers.

        Validates: Requirements 3.1, 4.1, 5.1, 5.5
        """
        recap_md = _write_recap(tmp_path)
        out_pdf = tmp_path / "bootcamp_recap.pdf"

        exit_code = generate_recap_pdf.main(
            ["--input", recap_md, "--output", str(out_pdf)]
        )

        assert exit_code == 0, "generate_recap_pdf.main must succeed (round-trip ok)"
        assert out_pdf.exists(), "the recap PDF must be written on success"

        text = extract_pdf_text(out_pdf.read_bytes())

        # Requirement 3.5 / 5.5: the paired section renders under a single
        # "Questions & Responses" heading.
        assert "Questions & Responses" in text

        # Requirement 3.1 / 4.1: both paired questions and responses render.
        for token in _PAIRED_TOKENS:
            assert token in text, f"paired token {token!r} missing from PDF text"

        # Requirement 5.1 / 5.5: the legacy split section's questions and answers
        # render too, classified independently from the paired section.
        for token in _SPLIT_TOKENS:
            assert token in text, f"split token {token!r} missing from PDF text"

    def test_inline_generator_renders_mixed_recap(self, tmp_path: Path) -> None:
        """The Inline_Generator renders the SAME recap with the same key content.

        ``generate_recap_pdf_inline.main`` reuses the bundled parser/renderer, so
        its output must carry the same paired and split content, proving it
        inherits the indent-aware rendering and wrapping fixes.

        Validates: Requirements 3.1, 4.1, 5.1, 5.5
        """
        recap_md = _write_recap(tmp_path)
        out_pdf = tmp_path / "bootcamp_recap_inline.pdf"

        exit_code = generate_recap_pdf_inline.main(
            ["--input", recap_md, "--output", str(out_pdf)]
        )

        assert exit_code == 0, "inline generator must succeed (round-trip ok)"
        assert out_pdf.exists(), "the inline recap PDF must be written on success"

        text = extract_pdf_text(out_pdf.read_bytes())

        # The inline generator inherits the schema-aware/indent-aware rendering:
        # the paired content and the split content are both present.
        for token in _PAIRED_TOKENS:
            assert token in text, f"inline: paired token {token!r} missing"
        for token in _SPLIT_TOKENS:
            assert token in text, f"inline: split token {token!r} missing"

    def test_inline_generator_reuses_bundled_parser_no_duplicated_schema(self) -> None:
        """The Inline_Generator holds no duplicated schema-parsing logic.

        Confirms by reading the source that ``generate_recap_pdf_inline.py``
        reuses the bundled parser/renderer (imports ``parse_recap_markdown`` /
        ``render_pdf`` from ``generate_recap_pdf``) and does not re-implement the
        Paired_Schema classification/parsing (no ``classify_section`` /
        ``parse_qr_section`` / ``format_qr_section`` definitions of its own).

        Validates: Requirements 5.5
        """
        inline_source = Path(
            generate_recap_pdf_inline.__file__
        ).read_text(encoding="utf-8")

        # It reuses the bundled parser/renderer rather than duplicating it.
        assert "from generate_recap_pdf import" in inline_source
        assert "parse_recap_markdown" in inline_source
        assert "render_pdf" in inline_source

        # It defines no schema-parsing helpers of its own — those live only in
        # the bundled generator / shared renderer.
        assert "def classify_section" not in inline_source
        assert "def parse_qr_section" not in inline_source
        assert "def format_qr_section" not in inline_source

    def test_both_generators_produce_consistent_key_content(
        self, tmp_path: Path
    ) -> None:
        """Both generators reproduce the same key paired/split content.

        Rendering the same recap through each generator yields extracted text
        that contains the same distinctive question/response/answer tokens,
        demonstrating the inline generator inherits the bundled behavior.

        Validates: Requirements 4.1, 5.1
        """
        recap_md = _write_recap(tmp_path)
        bundled_pdf = tmp_path / "bundled.pdf"
        inline_pdf = tmp_path / "inline.pdf"

        assert (
            generate_recap_pdf.main(["--input", recap_md, "--output", str(bundled_pdf)])
            == 0
        )
        assert (
            generate_recap_pdf_inline.main(
                ["--input", recap_md, "--output", str(inline_pdf)]
            )
            == 0
        )

        bundled_text = extract_pdf_text(bundled_pdf.read_bytes())
        inline_text = extract_pdf_text(inline_pdf.read_bytes())

        for token in (*_PAIRED_TOKENS, *_SPLIT_TOKENS):
            assert token in bundled_text, f"bundled missing {token!r}"
            assert token in inline_text, f"inline missing {token!r}"
