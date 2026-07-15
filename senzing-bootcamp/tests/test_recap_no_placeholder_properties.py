"""Property-based test for placeholder-stub absence in substantive recaps.

Feature: professional-recap-pdf, Property 6: No placeholder stubs in substantive recaps

For any RecapDocument whose sections contain only substantive content — no
"N/A" items, no "backfilled at track completion" strings, and no legacy
"Questions Asked" / "Answers Given" text in any field — rendering to a PDF via
``render_pdf`` and extracting its text via ``extract_pdf_text`` produces output
containing zero occurrences of those placeholder / legacy strings
(Requirements 4.5, 5.5, 5.6).

The ``st_recap_document`` strategy mirrors the pattern established in
``test_generate_recap_pdf.py`` and ``test_recap_cover_page_properties.py``: a
valid header (non-empty bootcamper, ISO 8601 Started timestamp, human-readable
Total Duration) plus 1-5 module sections. Every generated text field is drawn
from an alphabet that excludes the solidus ``/`` and the backtick, and is
filtered (case-insensitively) so it can never contain any forbidden substring:

* excluding ``/`` makes "N/A" structurally impossible in generated content;
* excluding the backtick means the renderer's inline-code handling (which drops
  backticks and concatenates the surrounding runs) can never fuse tokens into a
  forbidden substring;
* the substring filter removes the multi-word phrases ("backfilled at track
  completion", "Questions Asked", "Answers Given") on the off chance the
  letters-and-spaces alphabet produces one.

A non-empty ``Duration`` is guaranteed for every section so the generator's
``safe_text(duration) or "N/A"`` empty-duration fallback never fires — the only
"N/A" the renderer itself can emit.

The render path requires the optional ``fpdf2`` dependency, so the property
class skips gracefully when it is absent rather than erroring at collection
time.
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
# Forbidden strings the rendered PDF must never contain (Requirements 4.5, 5.6)
# ---------------------------------------------------------------------------
# Placeholder stubs (Req 4.5) and legacy subsection headings (Req 5.6). Stored
# lowercased so the substantive-content filter can reject any generated string
# that contains one case-insensitively.
_FORBIDDEN_SUBSTRINGS = (
    "n/a",
    "backfilled at track completion",
    "questions asked",
    "answers given",
)

# The exact strings the property asserts are absent from the rendered PDF text.
_FORBIDDEN_ASSERTIONS = (
    "N/A",
    "backfilled at track completion",
    "Questions Asked",
    "Answers Given",
)


def _has_forbidden(text: str) -> bool:
    """Return ``True`` when ``text`` contains any forbidden substring.

    Case-insensitive so a generated string can never smuggle a placeholder or
    legacy-heading substring past the filter regardless of casing.

    Args:
        text: A candidate generated string.

    Returns:
        ``True`` if any forbidden substring appears in ``text``.
    """
    lowered = text.lower()
    return any(sub in lowered for sub in _FORBIDDEN_SUBSTRINGS)


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


@st.composite
def st_iso_timestamp(draw: st.DrawFn) -> str:
    """Generate a valid ISO 8601 timestamp with timezone offset.

    Format: ``YYYY-MM-DDTHH:MM:SS±HH:MM`` — all ASCII with no solidus, so it
    renders and round-trips through the PDF without producing a forbidden
    substring.

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

    Always non-empty so the generator's ``safe_text(duration) or "N/A"``
    empty-duration fallback never fires.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A duration string containing an hours and a minutes component.
    """
    hours = draw(st.integers(min_value=0, max_value=100))
    minutes = draw(st.integers(min_value=0, max_value=59))
    return f"{hours}h {minutes}m"


def _substantive_text(
    min_size: int = 1, max_size: int = 100
) -> st.SearchStrategy[str]:
    """Generate stripped, non-empty text guaranteed free of forbidden substrings.

    The alphabet is letters, numbers, most punctuation/symbols, and spaces, but
    excludes line/paragraph separators (so each item stays on one line), the
    solidus ``/`` (so "N/A" is structurally impossible), and the backtick (so
    the renderer's inline-code handling cannot fuse runs into a forbidden
    substring). A final case-insensitive filter drops any residual string that
    still contains a forbidden multi-word phrase.

    Args:
        min_size: Minimum length before stripping.
        max_size: Maximum length before stripping.

    Returns:
        A strategy producing non-empty, forbidden-substring-free strings.
    """
    return (
        st.text(
            min_size=min_size,
            max_size=max_size,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "S", "Zs"),
                blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029/`",
            ),
        )
        .map(lambda s: s.strip())
        .filter(lambda s: len(s) > 0 and not _has_forbidden(s))
    )


def st_list_items() -> st.SearchStrategy[list[str]]:
    """Generate a possibly-empty list of substantive item strings.

    Returns:
        A strategy producing 0-10 forbidden-substring-free strings.
    """
    return st.lists(
        _substantive_text(min_size=1, max_size=100),
        min_size=0,
        max_size=10,
    )


@st.composite
def st_recap_header(draw: st.DrawFn) -> RecapHeader:
    """Generate a RecapHeader with a substantive bootcamper, Started, Duration.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapHeader whose three fields are all non-empty and substantive.
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
        .filter(lambda s: len(s) > 0 and not _has_forbidden(s))
    )
    return RecapHeader(
        bootcamper=bootcamper,
        started=draw(st_iso_timestamp()),
        total_duration=draw(st_duration()),
    )


@st.composite
def st_recap_section(draw: st.DrawFn) -> RecapSection:
    """Generate a substantive RecapSection with paired questions and answers.

    All list fields, the module name, and the (non-empty) duration are
    substantive, so no field contributes a forbidden substring and the empty-
    duration "N/A" fallback never fires.

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
        .filter(lambda s: len(s) > 0 and not _has_forbidden(s))
    )

    qa_count = draw(st.integers(min_value=0, max_value=10))
    item_strategy = _substantive_text(min_size=1, max_size=100)
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
    """Generate a fully substantive RecapDocument with 1-5 module sections.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A RecapDocument whose header and every section carry only substantive
        (forbidden-substring-free) content.
    """
    header = draw(st_recap_header())
    sections = draw(st.lists(st_recap_section(), min_size=1, max_size=5))
    return RecapDocument(header=header, sections=sections)


# ---------------------------------------------------------------------------
# Property 6: No placeholder stubs in substantive recaps
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed"
)
class TestPropertyNoPlaceholderStubs:
    """Property 6: a substantive recap renders no placeholder / legacy strings.

    **Validates: Requirements 4.5, 5.5, 5.6**

    For any RecapDocument from ``st_recap_document`` (non-empty header, 1-5
    sections, every field substantive), rendering the full Recap_PDF via
    ``render_pdf`` and round-tripping its text via ``extract_pdf_text`` shows the
    extracted text contains zero occurrences of the placeholder stubs "N/A" and
    "backfilled at track completion" (Req 4.5, 5.5) and zero occurrences of the
    legacy subsection headings "Questions Asked" and "Answers Given" (Req 5.6).
    """

    @given(doc=st_recap_document())
    def test_substantive_recap_has_no_placeholder_stubs(
        self, doc: RecapDocument
    ) -> None:
        """A rendered substantive recap contains none of the forbidden strings.

        # Feature: professional-recap-pdf, Property 6: No placeholder stubs in substantive recaps

        **Validates: Requirements 4.5, 5.5, 5.6**
        """
        from generate_recap_pdf import render_pdf
        from recap_pdf_render import extract_pdf_text

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "recap.pdf"
            render_pdf(doc, str(output_path))
            text = extract_pdf_text(output_path.read_bytes())

        for forbidden in _FORBIDDEN_ASSERTIONS:
            assert forbidden not in text, (
                f"substantive recap rendered a forbidden string {forbidden!r} "
                f"into the PDF text; placeholder stubs (Req 4.5/5.5) and legacy "
                f"headings (Req 5.6) must be absent. Extracted text: {text!r}"
            )
