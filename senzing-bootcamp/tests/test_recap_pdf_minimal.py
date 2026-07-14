"""Property-based tests for the Stdlib_PDF_Writer (Tier 3).

Feature: guaranteed-recap-pdf

These tests exercise ``recap_pdf_minimal.render_minimal_pdf`` — the stdlib-only
PDF writer that guarantees a valid ``docs/bootcamp_recap.pdf`` even when the
optional ``fpdf2`` dependency is neither installed nor installable. Because the
writer builds the PDF bytes by hand (no ``fpdf``), these tests never require
``fpdf2`` and therefore never skip: they assert the writer alone produces a
structurally valid, text-extractable PDF for arbitrary ``RecapDocument`` inputs.

The ``st_recap_document`` strategy generates arbitrary documents with varying
module counts, varied subsection presence (paired / split / none question
schemas, empty and populated lists), and unicode-ish text so the writer's
Latin-1 safety, escaping, word-wrapping, and multi-page overflow are all
exercised.

Properties validated (design "Property-Based / Behavioral Tests"):

- Structural validity: the output always starts with the ``%PDF-`` header and
  carries the ``%%EOF`` trailer.
- Content round-trip: ``recap_pdf_render.extract_pdf_text`` recovers every
  module name and every labeled subsection heading (Information Shared,
  Questions & Responses, Actions Taken, Duration, Journal).
- The guarantee holds with ``fpdf2`` simulated as unavailable.

**Validates: Requirements 7.1**
"""

from __future__ import annotations

import contextlib
import re
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Scripts are not packages; make them importable via the documented sys.path
# pattern (conftest also does this, kept here so the module imports standalone).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import (  # noqa: E402
    QRPair,
    RecapDocument,
    RecapHeader,
    RecapSection,
)
from recap_pdf_minimal import (  # noqa: E402
    LABEL_ACTIONS_TAKEN,
    LABEL_DURATION,
    LABEL_INFORMATION_SHARED,
    LABEL_JOURNAL,
    LABEL_QUESTIONS_RESPONSES,
    render_minimal_pdf,
)
from recap_pdf_render import extract_pdf_text, safe_text  # noqa: E402

# Every labeled subsection heading the writer emits for each module section.
_SUBSECTION_LABELS = (
    LABEL_INFORMATION_SHARED,
    LABEL_QUESTIONS_RESPONSES,
    LABEL_ACTIONS_TAKEN,
    LABEL_DURATION,
    LABEL_JOURNAL,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# Module-name characters: Latin-1 letters and digits only, with no whitespace.
# Restricting to the Latin-1 range keeps ``safe_text`` an identity map (nothing
# is replaced with '?'), and excluding whitespace means the name is always a
# single wrap-safe token — ``wrap_text`` splits only on whitespace, so a
# whitespace-free name (<= 30 chars, well within one heading line) survives into
# the extracted PDF text verbatim. Latin-1 accented letters (e.g. e-acute,
# n-tilde) supply the "unicode-ish" variation for names.
_NAME_ALPHABET = st.characters(
    whitelist_categories=("Lu", "Ll", "Nd"),
    max_codepoint=0x00FF,
)

# Body-text characters: any assigned, non-control, non-surrogate character up to
# U+2FFF. This deliberately includes spaces and non-Latin-1 characters so the
# writer's wrapping and ``safe_text`` replacement paths are exercised; body text
# is not asserted for round-trip, only that it renders without error.
_BODY_ALPHABET = st.characters(
    blacklist_categories=("Cc", "Cs"),
    max_codepoint=0x2FFF,
)


def st_name_token() -> st.SearchStrategy[str]:
    """Draw a non-empty, whitespace-free, Latin-1-safe module name token.

    Returns:
        A 1-30 character string of Latin-1 letters/digits (no whitespace), so it
        renders on one heading line and round-trips through the PDF verbatim.
    """
    return st.text(alphabet=_NAME_ALPHABET, min_size=1, max_size=30)


def st_body_line() -> st.SearchStrategy[str]:
    """Draw a possibly-empty single line of arbitrary, unicode-ish body text.

    Returns:
        A 0-50 character string free of control characters and surrogates; may
        contain spaces and non-Latin-1 characters.
    """
    return st.text(alphabet=_BODY_ALPHABET, min_size=0, max_size=50)


def st_body_lines() -> st.SearchStrategy[list[str]]:
    """Draw a possibly-empty list of body lines.

    Returns:
        A strategy producing 0-6 body lines.
    """
    return st.lists(st_body_line(), min_size=0, max_size=6)


@st.composite
def st_qr_pair(draw: st.DrawFn) -> QRPair:
    """Draw a QRPair with arbitrary question and response text.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A QRPair whose question and response are arbitrary body lines.
    """
    return QRPair(question=draw(st_body_line()), response=draw(st_body_line()))


@st.composite
def st_recap_header(draw: st.DrawFn) -> RecapHeader:
    """Draw a RecapHeader with optionally-empty metadata fields.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapHeader; each field is independently either empty or populated so
        the writer's "skip empty header field" branches are exercised.
    """
    return RecapHeader(
        bootcamper=draw(st.one_of(st.just(""), st_body_line())),
        started=draw(st.one_of(st.just(""), st_body_line())),
        total_duration=draw(st.one_of(st.just(""), st_body_line())),
    )


@st.composite
def st_recap_section(draw: st.DrawFn) -> RecapSection:
    """Draw a RecapSection with a varied question schema and subsection content.

    The section randomly adopts the paired, split, or none question schema and
    randomly populates (or leaves empty) each subsection list, so the writer
    renders bullets, Q/R pairs, split Q/A lists, the "None" placeholder, and
    Generic_Content across examples.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapSection with a single-token module name and varied content.
    """
    schema = draw(st.sampled_from(["paired", "split", "none"]))
    qr_pairs: list[QRPair] = []
    questions: list[str] = []
    answers: list[str] = []
    if schema == "paired":
        qr_pairs = draw(st.lists(st_qr_pair(), min_size=0, max_size=4))
    elif schema == "split":
        count = draw(st.integers(min_value=0, max_value=4))
        questions = draw(st.lists(st_body_line(), min_size=count, max_size=count))
        answers = draw(st.lists(st_body_line(), min_size=count, max_size=count))

    return RecapSection(
        module_number=draw(st.integers(min_value=1, max_value=11)),
        module_name=draw(st_name_token()),
        timestamp=draw(st.one_of(st.just(""), st_body_line())),
        information_shared=draw(st_body_lines()),
        qr_pairs=qr_pairs,
        questions_asked=questions,
        answers_given=answers,
        schema=schema,
        actions_taken=draw(st_body_lines()),
        duration=draw(st.one_of(st.just(""), st_body_line())),
        generic_content=draw(st.lists(st_body_line(), min_size=0, max_size=3)),
    )


@st.composite
def st_recap_document(draw: st.DrawFn) -> RecapDocument:
    """Draw a RecapDocument with a header and 1-5 module sections.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapDocument with at least one section so every module name and
        subsection label has a rendered occurrence to assert.
    """
    return RecapDocument(
        header=draw(st_recap_header()),
        sections=draw(st.lists(st_recap_section(), min_size=1, max_size=5)),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTINEL = object()


def _render_to_bytes(doc: RecapDocument, *, body_text: str = "") -> bytes:
    """Render ``doc`` to a temporary PDF and return its raw bytes.

    Args:
        doc: The recap document to render.
        body_text: Raw Markdown for the no-section fallback path.

    Returns:
        The generated PDF file's bytes.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "recap.pdf"
        render_minimal_pdf(doc, out_path, body_text=body_text)
        return out_path.read_bytes()


@contextlib.contextmanager
def _fpdf_unavailable():
    """Temporarily make ``import fpdf`` raise ImportError, then restore.

    Setting ``sys.modules['fpdf'] = None`` forces any ``import fpdf`` to raise
    ImportError, simulating an environment where the optional ``fpdf2``
    dependency is unavailable. The previous ``sys.modules`` entry is restored on
    exit so other tests are unaffected.
    """
    saved = sys.modules.get("fpdf", _SENTINEL)
    sys.modules["fpdf"] = None  # type: ignore[assignment]
    try:
        yield
    finally:
        if saved is _SENTINEL:
            sys.modules.pop("fpdf", None)
        else:
            sys.modules["fpdf"] = saved  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Property: structural validity
# ---------------------------------------------------------------------------


class TestMinimalPdfStructure:
    """The stdlib writer always emits a structurally valid PDF.

    **Validates: Requirements 7.1**

    For any arbitrary RecapDocument, ``render_minimal_pdf`` produces bytes that
    begin with the ``%PDF-`` version header and carry the ``%%EOF`` trailer, so
    the output is a parseable PDF file (Requirement 7.1: a valid Recap_PDF).
    """

    @given(doc=st_recap_document())
    def test_output_starts_with_pdf_header(self, doc: RecapDocument) -> None:
        """The rendered bytes begin with the ``%PDF-`` version header.

        **Validates: Requirements 7.1**
        """
        pdf_bytes = _render_to_bytes(doc)
        assert pdf_bytes.startswith(b"%PDF-"), (
            f"output does not start with the PDF header: {pdf_bytes[:16]!r}"
        )

    @given(doc=st_recap_document())
    def test_output_has_eof_trailer(self, doc: RecapDocument) -> None:
        """The rendered bytes contain the ``%%EOF`` trailer marker.

        **Validates: Requirements 7.1**
        """
        pdf_bytes = _render_to_bytes(doc)
        assert b"%%EOF" in pdf_bytes, "output is missing the %%EOF trailer"
        # The trailer must be at the very end of the file (the last marker).
        assert pdf_bytes.rstrip().endswith(b"%%EOF"), (
            "the %%EOF trailer is not at the end of the file"
        )


# ---------------------------------------------------------------------------
# Property: content round-trip via extract_pdf_text
# ---------------------------------------------------------------------------


class TestMinimalPdfContentRoundTrip:
    """Extracted PDF text recovers every module name and subsection label.

    **Validates: Requirements 7.1**

    For any arbitrary RecapDocument, the text recovered by
    ``recap_pdf_render.extract_pdf_text`` contains each section's module name
    and every labeled subsection heading, confirming the guaranteed PDF has
    extractable text reflecting the recap content (Requirement 7.1).
    """

    @given(doc=st_recap_document())
    def test_module_names_survive_round_trip(self, doc: RecapDocument) -> None:
        """Each module name appears in the extracted PDF text.

        **Validates: Requirements 7.1**
        """
        text = extract_pdf_text(_render_to_bytes(doc))
        for section in doc.sections:
            expected = safe_text(section.module_name)
            assert expected in text, (
                f"module name {section.module_name!r} (Latin-1 safe: "
                f"{expected!r}) missing from extracted PDF text"
            )

    @given(doc=st_recap_document())
    def test_subsection_labels_survive_round_trip(
        self, doc: RecapDocument
    ) -> None:
        """Every labeled subsection heading appears in the extracted PDF text.

        **Validates: Requirements 7.1**
        """
        text = extract_pdf_text(_render_to_bytes(doc))
        for label in _SUBSECTION_LABELS:
            assert label in text, (
                f"subsection label {label!r} missing from extracted PDF text"
            )


# ---------------------------------------------------------------------------
# Property: the guarantee holds without fpdf2
# ---------------------------------------------------------------------------


class TestMinimalPdfWithoutFpdf2:
    """The stdlib writer produces a valid PDF with ``fpdf2`` unavailable.

    **Validates: Requirements 7.1**

    With ``fpdf2`` simulated as unavailable, ``render_minimal_pdf`` still yields
    a structurally valid PDF whose extracted text recovers the module names and
    subsection labels — the core guarantee of the Stdlib_PDF_Writer fallback
    (Requirement 7.1).
    """

    @given(doc=st_recap_document())
    def test_valid_pdf_with_fpdf_blocked(self, doc: RecapDocument) -> None:
        """A valid, text-extractable PDF is produced while ``import fpdf`` fails.

        **Validates: Requirements 7.1**
        """
        with _fpdf_unavailable():
            pdf_bytes = _render_to_bytes(doc)
        assert pdf_bytes.startswith(b"%PDF-")
        assert pdf_bytes.rstrip().endswith(b"%%EOF")

        text = extract_pdf_text(pdf_bytes)
        for section in doc.sections:
            assert safe_text(section.module_name) in text
        for label in _SUBSECTION_LABELS:
            assert label in text


# ---------------------------------------------------------------------------
# Example-based edge cases (complement the properties above)
# ---------------------------------------------------------------------------


class TestMinimalPdfExamples:
    """Concrete edge cases for the stdlib writer.

    **Validates: Requirements 7.1**
    """

    def test_empty_document_is_valid_pdf(self) -> None:
        """A document with no sections still yields a valid, single-page PDF."""
        doc = RecapDocument(header=RecapHeader(), sections=[])
        pdf_bytes = _render_to_bytes(doc)
        assert pdf_bytes.startswith(b"%PDF-")
        assert pdf_bytes.rstrip().endswith(b"%%EOF")
        # Even an empty document renders at least one page.
        count_match = re.search(rb"/Type /Pages /Kids \[[^\]]*\] /Count (\d+)", pdf_bytes)
        assert count_match is not None, "page tree /Count not found"
        assert int(count_match.group(1)) >= 1

    def test_single_module_content_round_trips(self) -> None:
        """A known single-module recap renders its name and every label."""
        doc = RecapDocument(
            header=RecapHeader(bootcamper="Ada", started="2025", total_duration="3h"),
            sections=[
                RecapSection(
                    module_number=1,
                    module_name="BusinessProblem",
                    timestamp="2025-01-01",
                    information_shared=["shared a dataset"],
                    schema="paired",
                    qr_pairs=[QRPair(question="why entities", response="because dupes")],
                    actions_taken=["ran senzing demo"],
                    duration="45m",
                    generic_content=["freeform journal note"],
                )
            ],
        )
        text = extract_pdf_text(_render_to_bytes(doc))
        assert "BusinessProblem" in text
        for label in _SUBSECTION_LABELS:
            assert label in text

    def test_overflow_content_spans_multiple_pages(self) -> None:
        """Enough content forces multi-page overflow with one header/trailer."""
        doc = RecapDocument(
            header=RecapHeader(bootcamper="Grace"),
            sections=[
                RecapSection(
                    module_number=2,
                    module_name="Loading",
                    information_shared=[f"fact number {i}" for i in range(120)],
                    schema="none",
                    duration="1h",
                )
            ],
        )
        pdf_bytes = _render_to_bytes(doc)
        assert pdf_bytes.startswith(b"%PDF-")
        assert pdf_bytes.rstrip().endswith(b"%%EOF")
        # Exactly one header and one trailer even across many pages.
        assert pdf_bytes.count(b"%%EOF") == 1
        count_match = re.search(rb"/Type /Pages /Kids \[[^\]]*\] /Count (\d+)", pdf_bytes)
        assert count_match is not None and int(count_match.group(1)) >= 2, (
            "expected multi-page overflow for 120 list items"
        )
        text = extract_pdf_text(pdf_bytes)
        assert "Loading" in text

    def test_no_sections_renders_raw_body_fallback(self) -> None:
        """With no parsed sections, ``body_text`` is rendered as the fallback."""
        doc = RecapDocument(header=RecapHeader(bootcamper="Linus"), sections=[])
        body = "# Recap\n\n- distinctivebodytoken here\n\nsome prose paragraph\n"
        text = extract_pdf_text(_render_to_bytes(doc, body_text=body))
        assert "distinctivebodytoken" in text, (
            "raw body fallback did not render the body text"
        )
