"""Property-based test for Cover_Page metadata round-trip.

Feature: professional-recap-pdf, Property 1: Cover page metadata round-trip

For any valid RecapDocument with a non-empty bootcamper name, Started value,
Total Duration value, and 1-5 module sections, rendering to a PDF via
``render_pdf`` and extracting its text via ``extract_pdf_text`` produces output
containing the bootcamper name, the Started value, the Total Duration value, and
a ``Modules completed: N`` Headline_Results line where ``N == len(doc.sections)``
(Requirements 2.4, 2.5, 2.6, 2.7).

The ``st_recap_document`` strategy mirrors the pattern established in
``test_generate_recap_pdf.py``: a valid header (non-empty bootcamper, ISO 8601
Started timestamp, human-readable Total Duration) plus 1-5 module sections. The
render path requires the optional ``fpdf2`` dependency, so the property class
skips gracefully when it is absent rather than erroring at collection time.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ``fpdf2`` is an optional dependency. Rendering constructs the ``RecapPDF``
# subclass (built on ``fpdf.FPDF``), so tests that render must skip — not
# error — when fpdf2 is absent.
_FPDF_AVAILABLE = importlib.util.find_spec("fpdf") is not None

# Scripts are not packages; make them importable via the documented sys.path
# pattern (conftest also does this, kept here so the module imports standalone).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import (  # noqa: E402
    RecapDocument,
    RecapHeader,
    RecapSection,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


@st.composite
def st_iso_timestamp(draw: st.DrawFn) -> str:
    """Generate a valid ISO 8601 timestamp with timezone offset.

    Format: ``YYYY-MM-DDTHH:MM:SS±HH:MM`` — all ASCII, so it renders and
    round-trips through the PDF unchanged.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        An ISO 8601 timestamp string.
    """
    year = draw(st.integers(min_value=2024, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    tz_offset_hours = draw(st.integers(min_value=-12, max_value=14))
    tz_offset_minutes = draw(st.sampled_from([0, 30]))

    tz_sign = "+" if tz_offset_hours >= 0 else "-"
    tz_h = abs(tz_offset_hours)

    return (
        f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
        f"{tz_sign}{tz_h:02d}:{tz_offset_minutes:02d}"
    )


@st.composite
def st_duration(draw: st.DrawFn) -> str:
    """Generate a non-empty human-readable duration like ``2h 15m``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A duration string containing an hours and a minutes component.
    """
    hours = draw(st.integers(min_value=0, max_value=100))
    minutes = draw(st.integers(min_value=0, max_value=59))
    return f"{hours}h {minutes}m"


def _non_whitespace_only_text(
    min_size: int = 1, max_size: int = 100
) -> st.SearchStrategy[str]:
    """Generate stripped, non-empty text safe for single-line list rendering.

    Excludes line/paragraph separators so each generated item stays on one line,
    mirroring the text strategy in ``test_generate_recap_pdf.py``.

    Args:
        min_size: Minimum length before stripping.
        max_size: Maximum length before stripping.

    Returns:
        A strategy producing non-empty, whitespace-trimmed strings.
    """
    return (
        st.text(
            min_size=min_size,
            max_size=max_size,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "S", "Zs"),
                blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
            ),
        )
        .map(lambda s: s.strip())
        .filter(lambda s: len(s) > 0)
    )


def st_list_items() -> st.SearchStrategy[list[str]]:
    """Generate a possibly-empty list of non-empty item strings.

    Returns:
        A strategy producing 0-10 non-empty strings.
    """
    return st.lists(
        _non_whitespace_only_text(min_size=1, max_size=100),
        min_size=0,
        max_size=10,
    )


@st.composite
def st_recap_header(draw: st.DrawFn) -> RecapHeader:
    """Generate a RecapHeader with a non-empty bootcamper, Started, and Duration.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapHeader whose three fields are all non-empty.
    """
    bootcamper = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "Zs"),
                blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
            ),
        )
        .map(lambda s: s.strip())
        .filter(lambda s: len(s) > 0)
    )
    return RecapHeader(
        bootcamper=bootcamper,
        started=draw(st_iso_timestamp()),
        total_duration=draw(st_duration()),
    )


@st.composite
def st_recap_section(draw: st.DrawFn) -> RecapSection:
    """Generate a valid RecapSection with paired questions and answers.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapSection with equal-length questions/answers and a duration.
    """
    module_name = draw(
        st.text(
            min_size=1,
            max_size=60,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "Zs"),
                blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
            ),
        )
        .map(lambda s: s.strip())
        .filter(lambda s: len(s) > 0)
    )

    qa_count = draw(st.integers(min_value=0, max_value=10))
    item_strategy = _non_whitespace_only_text(min_size=1, max_size=100)
    questions_asked = draw(
        st.lists(item_strategy, min_size=qa_count, max_size=qa_count)
    )
    answers_given = draw(
        st.lists(item_strategy, min_size=qa_count, max_size=qa_count)
    )

    return RecapSection(
        module_number=draw(st.integers(min_value=1, max_value=11)),
        module_name=module_name,
        timestamp=draw(st_iso_timestamp()),
        information_shared=draw(st_list_items()),
        questions_asked=questions_asked,
        answers_given=answers_given,
        actions_taken=draw(st_list_items()),
        duration=draw(st_duration()),
    )


@st.composite
def st_recap_document(draw: st.DrawFn) -> RecapDocument:
    """Generate a RecapDocument with a full header and 1-5 module sections.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapDocument satisfying the Property 1 precondition (non-empty
        bootcamper, Started, Total Duration, and 1-5 sections).
    """
    header = draw(st_recap_header())
    sections = draw(st.lists(st_recap_section(), min_size=1, max_size=5))
    return RecapDocument(header=header, sections=sections)


# ---------------------------------------------------------------------------
# Property 1: Cover page metadata round-trip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed"
)
class TestPropertyCoverPageMetadataRoundTrip:
    """Property 1: Cover_Page metadata survives the render/extract round-trip.

    **Validates: Requirements 2.4, 2.5, 2.6, 2.7**

    For any RecapDocument from ``st_recap_document`` (non-empty bootcamper,
    Started, Total Duration, and 1-5 sections), rendering the full Recap_PDF via
    ``render_pdf`` and round-tripping its text via ``extract_pdf_text`` shows the
    bootcamper name (Req 2.4), the Started value (Req 2.5), the Total Duration
    value (Req 2.6), and the ``Modules completed: N`` Headline_Results line whose
    count equals ``len(doc.sections)`` (Req 2.7) all survive onto the Cover_Page.
    """

    @given(doc=st_recap_document())
    def test_cover_page_metadata_survives_render(
        self, doc: RecapDocument
    ) -> None:
        """The rendered Cover_Page text carries the name, Started, Total
        Duration, and the module-section count.

        # Feature: professional-recap-pdf, Property 1: Cover page metadata round-trip

        **Validates: Requirements 2.4, 2.5, 2.6, 2.7**
        """
        from generate_recap_pdf import render_pdf
        from recap_pdf_render import extract_pdf_text, safe_text

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "recap.pdf"
            render_pdf(doc, str(output_path))
            text = extract_pdf_text(output_path.read_bytes())

        # Req 2.4: the bootcamper name renders on the Cover_Page. fpdf core
        # fonts are Latin-1, so the renderer emits ``safe_text(name)`` — compare
        # against that same Latin-1-safe form rather than the raw name.
        safe_name = safe_text(doc.header.bootcamper)
        assert safe_name in text, (
            f"Cover_Page missing the bootcamper name "
            f"{doc.header.bootcamper!r} (Latin-1 safe: {safe_name!r}), "
            f"got: {text!r}"
        )

        # Req 2.5: the Started value renders as "Started: {value}" on the cover.
        expected_started = safe_text(f"Started: {doc.header.started}")
        assert expected_started in text, (
            f"Cover_Page missing the Started value {expected_started!r}, "
            f"got: {text!r}"
        )

        # Req 2.6: the Total Duration value renders as "Total Duration: {value}".
        expected_duration = safe_text(
            f"Total Duration: {doc.header.total_duration}"
        )
        assert expected_duration in text, (
            f"Cover_Page missing the Total Duration value "
            f"{expected_duration!r}, got: {text!r}"
        )

        # Req 2.7: Headline_Results shows the module-section count, which equals
        # ``len(doc.sections)`` for a document rendered with sections.
        expected_stats = f"Modules completed: {len(doc.sections)}"
        assert expected_stats in text, (
            f"Cover_Page missing the Headline_Results line {expected_stats!r}, "
            f"got: {text!r}"
        )
