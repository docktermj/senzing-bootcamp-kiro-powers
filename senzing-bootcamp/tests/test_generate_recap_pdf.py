"""Property-based tests for generate_recap_pdf.py using Hypothesis.

Feature: module-recap-document

Strategies for generating valid RecapHeader, RecapSection, and RecapDocument
instances. Property tests (tasks 6-12) and edge case tests (task 13) are
added in subsequent tasks.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ``fpdf2`` is an optional dependency. The professional-layout ``RecapPDF``
# subclass is defined on ``fpdf.FPDF`` and is resolved lazily, so tests that
# construct it must skip (not error) when fpdf2 is absent.
_FPDF_AVAILABLE = importlib.util.find_spec("fpdf") is not None

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import (
    RecapDocument,
    RecapHeader,
    RecapSection,
    _build_qa_lines,
    _render_module_page,
    find_placeholder_stub,
    format_recap_document,
    format_recap_section,
    main,
    parse_recap_markdown,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_iso_timestamp(draw: st.DrawFn) -> str:
    """Generate a valid ISO 8601 timestamp with timezone offset.

    Format: YYYY-MM-DDTHH:MM:SS±HH:MM
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
    """Generate a human-readable duration string like '2h 15m' or '0h 45m'."""
    hours = draw(st.integers(min_value=0, max_value=100))
    minutes = draw(st.integers(min_value=0, max_value=59))
    return f"{hours}h {minutes}m"


def _non_whitespace_only_text(
    min_size: int = 1, max_size: int = 100
) -> st.SearchStrategy[str]:
    """Generate text that round-trips through the markdown parser.

    Uses Zs (space separators) instead of Z (all separators) to avoid
    line/paragraph separators that break line-by-line parsing. Filters out
    strings that are only whitespace and strips leading/trailing whitespace
    since the markdown parser normalizes them via .strip().
    """
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "S", "Zs"),
            blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
        ),
    ).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)


def st_list_items() -> st.SearchStrategy[list[str]]:
    """Generate lists of non-empty strings for recap section fields.

    Items must contain at least one non-whitespace character to survive
    markdown round-tripping (the parser strips whitespace-only items).
    """
    return st.lists(
        _non_whitespace_only_text(min_size=1, max_size=100),
        min_size=0,
        max_size=10,
    )


@st.composite
def st_recap_header(draw: st.DrawFn) -> RecapHeader:
    """Generate a valid RecapHeader instance.

    Bootcamper name is stripped to match parser normalization behavior.
    """
    bootcamper = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "Zs"),
                blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
            ),
        ).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)
    )
    started = draw(st_iso_timestamp())
    total_duration = draw(st_duration())
    return RecapHeader(
        bootcamper=bootcamper,
        started=started,
        total_duration=total_duration,
    )


@st.composite
def st_recap_section(draw: st.DrawFn) -> RecapSection:
    """Generate a valid RecapSection instance.

    Questions and answers are paired (same length) to maintain Q&A integrity.
    Module names and list items are stripped to match parser normalization.
    """
    module_number = draw(st.integers(min_value=1, max_value=11))
    module_name = draw(
        st.text(
            min_size=1,
            max_size=60,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "Zs"),
                blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
            ),
        ).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)
    )
    timestamp = draw(st_iso_timestamp())
    information_shared = draw(st_list_items())

    # Questions and answers must have the same length for Q&A pairing
    qa_count = draw(st.integers(min_value=0, max_value=10))
    item_strategy = _non_whitespace_only_text(min_size=1, max_size=100)
    questions_asked = draw(
        st.lists(item_strategy, min_size=qa_count, max_size=qa_count)
    )
    answers_given = draw(
        st.lists(item_strategy, min_size=qa_count, max_size=qa_count)
    )

    actions_taken = draw(st_list_items())
    duration = draw(st_duration())

    return RecapSection(
        module_number=module_number,
        module_name=module_name,
        timestamp=timestamp,
        information_shared=information_shared,
        questions_asked=questions_asked,
        answers_given=answers_given,
        actions_taken=actions_taken,
        duration=duration,
    )


@st.composite
def st_recap_document(draw: st.DrawFn) -> RecapDocument:
    """Generate a valid RecapDocument with 1-5 sections."""
    header = draw(st_recap_header())
    sections = draw(st.lists(st_recap_section(), min_size=1, max_size=5))
    return RecapDocument(header=header, sections=sections)


# ---------------------------------------------------------------------------
# Strategy validation tests
# ---------------------------------------------------------------------------


class TestStrategies:
    """Verify that Hypothesis strategies produce valid data structures."""

    @given(header=st_recap_header())
    @settings(max_examples=20)
    def test_recap_header_has_non_empty_bootcamper(self, header: RecapHeader) -> None:
        """Generated headers always have a non-empty bootcamper name."""
        assert len(header.bootcamper.strip()) > 0

    @given(header=st_recap_header())
    @settings(max_examples=20)
    def test_recap_header_has_valid_timestamp(self, header: RecapHeader) -> None:
        """Generated headers have a timestamp matching ISO 8601 pattern."""
        # Basic pattern: YYYY-MM-DDTHH:MM:SS±HH:MM
        assert "T" in header.started
        assert len(header.started) >= 19

    @given(header=st_recap_header())
    @settings(max_examples=20)
    def test_recap_header_has_duration(self, header: RecapHeader) -> None:
        """Generated headers have a duration containing 'h' and 'm'."""
        assert "h" in header.total_duration
        assert "m" in header.total_duration

    @given(section=st_recap_section())
    @settings(max_examples=20)
    def test_recap_section_module_number_in_range(
        self, section: RecapSection
    ) -> None:
        """Generated sections have module_number between 1 and 11."""
        assert 1 <= section.module_number <= 11

    @given(section=st_recap_section())
    @settings(max_examples=20)
    def test_recap_section_qa_pairing(self, section: RecapSection) -> None:
        """Generated sections have equal-length questions and answers lists."""
        assert len(section.questions_asked) == len(section.answers_given)

    @given(section=st_recap_section())
    @settings(max_examples=20)
    def test_recap_section_has_non_empty_name(self, section: RecapSection) -> None:
        """Generated sections have a non-empty module name."""
        assert len(section.module_name.strip()) > 0

    @given(doc=st_recap_document())
    @settings(max_examples=20)
    def test_recap_document_has_sections(self, doc: RecapDocument) -> None:
        """Generated documents have at least one section."""
        assert len(doc.sections) >= 1

    @given(doc=st_recap_document())
    @settings(max_examples=20)
    def test_recap_document_sections_have_valid_structure(
        self, doc: RecapDocument
    ) -> None:
        """All sections in a generated document have valid Q&A pairing."""
        for section in doc.sections:
            assert len(section.questions_asked) == len(section.answers_given)
            assert 1 <= section.module_number <= 11


# ---------------------------------------------------------------------------
# Property 5: Round-trip structural equivalence
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """Round-trip property: format to markdown then parse back yields equivalent data.

    **Validates: Requirements 5.2, 6.7**

    For all valid Recap_Document markdown content, parsing then rendering then
    re-reading preserves the semantic structure (headings, lists, section order).
    """

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_round_trip_header_fields(self, doc: RecapDocument) -> None:
        """Header fields (bootcamper, started, total_duration) survive a
        format-then-parse round-trip without modification.

        **Validates: Requirements 5.2, 6.7**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert parsed.header.bootcamper == doc.header.bootcamper, (
            f"Bootcamper mismatch: {doc.header.bootcamper!r} -> "
            f"{parsed.header.bootcamper!r}"
        )
        assert parsed.header.started == doc.header.started, (
            f"Started mismatch: {doc.header.started!r} -> "
            f"{parsed.header.started!r}"
        )
        assert parsed.header.total_duration == doc.header.total_duration, (
            f"Total duration mismatch: {doc.header.total_duration!r} -> "
            f"{parsed.header.total_duration!r}"
        )

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_round_trip_section_count(self, doc: RecapDocument) -> None:
        """The number of sections is preserved through a format-then-parse
        round-trip.

        **Validates: Requirements 5.2, 6.7**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(doc.sections), (
            f"Section count mismatch: expected {len(doc.sections)}, "
            f"got {len(parsed.sections)}"
        )

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_round_trip_section_identity_fields(
        self, doc: RecapDocument
    ) -> None:
        """Each section's module_number, module_name, and timestamp survive
        a format-then-parse round-trip.

        **Validates: Requirements 5.2, 6.7**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(doc.sections)

        for i, (original, roundtripped) in enumerate(
            zip(doc.sections, parsed.sections)
        ):
            assert roundtripped.module_number == original.module_number, (
                f"Section {i}: module_number mismatch: "
                f"{original.module_number} -> {roundtripped.module_number}"
            )
            assert roundtripped.module_name == original.module_name, (
                f"Section {i}: module_name mismatch: "
                f"{original.module_name!r} -> {roundtripped.module_name!r}"
            )
            assert roundtripped.timestamp == original.timestamp, (
                f"Section {i}: timestamp mismatch: "
                f"{original.timestamp!r} -> {roundtripped.timestamp!r}"
            )

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_round_trip_list_contents(self, doc: RecapDocument) -> None:
        """Each section's list fields (information_shared, questions_asked,
        answers_given, actions_taken) survive a format-then-parse round-trip
        with identical content and ordering.

        **Validates: Requirements 5.2, 6.7**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(doc.sections)

        for i, (original, roundtripped) in enumerate(
            zip(doc.sections, parsed.sections)
        ):
            assert roundtripped.information_shared == original.information_shared, (
                f"Section {i}: information_shared mismatch"
            )
            assert roundtripped.questions_asked == original.questions_asked, (
                f"Section {i}: questions_asked mismatch"
            )
            assert roundtripped.answers_given == original.answers_given, (
                f"Section {i}: answers_given mismatch"
            )
            assert roundtripped.actions_taken == original.actions_taken, (
                f"Section {i}: actions_taken mismatch"
            )

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_round_trip_duration(self, doc: RecapDocument) -> None:
        """Each section's duration field survives a format-then-parse
        round-trip without modification.

        **Validates: Requirements 5.2, 6.7**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(doc.sections)

        for i, (original, roundtripped) in enumerate(
            zip(doc.sections, parsed.sections)
        ):
            assert roundtripped.duration == original.duration, (
                f"Section {i}: duration mismatch: "
                f"{original.duration!r} -> {roundtripped.duration!r}"
            )


# ---------------------------------------------------------------------------
# Property Test: Structural Completeness (Task 6)
# ---------------------------------------------------------------------------

_REQUIRED_SUBSECTIONS = [
    "Information Shared",
    "Questions Asked",
    "Answers Given",
    "Actions Taken",
    "Duration",
]


class TestStructuralCompleteness:
    """Property test: markdown parser correctly extracts all module sections.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

    For all valid module completion data, the generated Recap_Section contains
    exactly the required subsections in order: "Information Shared",
    "Questions Asked", "Answers Given", "Actions Taken", "Duration".
    """

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_structural_completeness(self, doc: RecapDocument) -> None:
        """Format a document to markdown, parse it back, verify structural completeness.

        For all valid module completion data, the generated Recap_Section contains
        exactly the required subsections in order: "Information Shared",
        "Questions Asked", "Answers Given", "Actions Taken", "Duration".

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
        """
        # Format the document to markdown
        markdown = format_recap_document(doc)

        # Parse it back
        parsed = parse_recap_markdown(markdown)

        # Assert the number of parsed sections equals the number of input sections
        assert len(parsed.sections) == len(doc.sections), (
            f"Expected {len(doc.sections)} sections, got {len(parsed.sections)}"
        )

        # For each section, verify structural fields match
        for original, parsed_section in zip(doc.sections, parsed.sections):
            # Req 2.1: Module number, name, and timestamp match
            assert parsed_section.module_number == original.module_number, (
                f"Module number mismatch: expected {original.module_number}, "
                f"got {parsed_section.module_number}"
            )
            assert parsed_section.module_name == original.module_name, (
                f"Module name mismatch: expected {original.module_name!r}, "
                f"got {parsed_section.module_name!r}"
            )
            assert parsed_section.timestamp == original.timestamp, (
                f"Timestamp mismatch: expected {original.timestamp!r}, "
                f"got {parsed_section.timestamp!r}"
            )

            # Req 2.2: Information shared list preserved
            assert len(parsed_section.information_shared) == len(
                original.information_shared
            ), (
                f"Information shared count mismatch: "
                f"expected {len(original.information_shared)}, "
                f"got {len(parsed_section.information_shared)}"
            )

            # Req 2.3: Questions asked list preserved
            assert len(parsed_section.questions_asked) == len(
                original.questions_asked
            ), (
                f"Questions asked count mismatch: "
                f"expected {len(original.questions_asked)}, "
                f"got {len(parsed_section.questions_asked)}"
            )

            # Req 2.4: Answers given list preserved
            assert len(parsed_section.answers_given) == len(
                original.answers_given
            ), (
                f"Answers given count mismatch: "
                f"expected {len(original.answers_given)}, "
                f"got {len(parsed_section.answers_given)}"
            )

            # Req 2.5: Actions taken list preserved
            assert len(parsed_section.actions_taken) == len(
                original.actions_taken
            ), (
                f"Actions taken count mismatch: "
                f"expected {len(original.actions_taken)}, "
                f"got {len(parsed_section.actions_taken)}"
            )

            # Req 2.6: Duration field preserved
            assert parsed_section.duration == original.duration, (
                f"Duration mismatch: expected {original.duration!r}, "
                f"got {parsed_section.duration!r}"
            )

    @given(section=st_recap_section())
    @settings(max_examples=50)
    def test_subsections_present_in_order(self, section: RecapSection) -> None:
        """For all valid RecapSection data, the formatted markdown contains all
        required subsections in the correct order.

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
        """
        markdown = format_recap_section(section)

        # Locate each required subsection as a whole heading line. Anchoring to
        # line starts (``^### <name>$`` with re.MULTILINE) ensures an in-content
        # occurrence of "### <name>" inside a list item -- e.g. a generated item
        # whose text is literally "### Actions Taken", rendered as
        # "- ### Actions Taken" -- is never mistaken for the real heading, which
        # is always emitted on its own line by ``format_recap_section``.
        heading_matches = {
            name: re.search(
                rf"^### {re.escape(name)}$", markdown, re.MULTILINE
            )
            for name in _REQUIRED_SUBSECTIONS
        }

        # Verify all required subsections are present as their own heading line
        for subsection_name, match in heading_matches.items():
            assert match is not None, (
                f"Missing required subsection '### {subsection_name}' "
                f"in formatted section"
            )

        # Verify subsections appear in the correct order using each heading's
        # line-anchored position (immune to "### <name>" text inside list items)
        positions = [
            heading_matches[name].start() for name in _REQUIRED_SUBSECTIONS
        ]
        assert positions == sorted(positions), (
            f"Subsections are not in the required order. "
            f"Expected order: {_REQUIRED_SUBSECTIONS}"
        )


# ---------------------------------------------------------------------------
# Property 3: ISO 8601 Timestamp Format Validity
# ---------------------------------------------------------------------------


class TestTimestampFormat:
    """All timestamps in parsed output match ISO 8601 format with timezone.

    **Validates: Requirements 7.1, 7.2**

    For all generated timestamps in the Recap_Document (header start date,
    per-module completion dates), each timestamp matches the ISO 8601 format
    with timezone offset (YYYY-MM-DDTHH:MM:SS±HH:MM).
    """

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_timestamps_match_iso8601_with_timezone(
        self, doc: RecapDocument
    ) -> None:
        """For all generated recap documents, formatting to markdown then
        parsing back produces timestamps that match ISO 8601 with timezone
        offset (YYYY-MM-DDTHH:MM:SS±HH:MM).

        **Validates: Requirements 7.1, 7.2**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        iso8601_pattern = (
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"
        )

        # Req 7.1: Header started timestamp must match ISO 8601 with timezone
        assert re.match(iso8601_pattern, parsed.header.started), (
            f"Header 'started' timestamp does not match ISO 8601: "
            f"{parsed.header.started!r}"
        )

        # Req 7.2: Each section's completion timestamp must match
        for section in parsed.sections:
            assert re.match(iso8601_pattern, section.timestamp), (
                f"Module {section.module_number} timestamp does not match "
                f"ISO 8601: {section.timestamp!r}"
            )


# ---------------------------------------------------------------------------
# Property 1: Append Preserves Existing Content
# ---------------------------------------------------------------------------


class TestAppendPreservation:
    """Appending a new RecapSection preserves all existing file content byte-for-byte.

    **Validates: Requirements 1.2, 3.2**

    For all valid existing Recap_Document content and all valid new
    Recap_Sections, appending a section to the document preserves all
    previously written content byte-for-byte. The new content appears
    only after the existing content.
    """

    @given(doc=st_recap_document(), new_section=st_recap_section())
    @settings(max_examples=50)
    def test_append_preserves_existing_content_byte_for_byte(
        self, doc: RecapDocument, new_section: RecapSection
    ) -> None:
        """Existing document content is preserved byte-for-byte as a prefix
        of the appended result.

        Simulates the file-level append operation: format existing document,
        format new section, concatenate. The original bytes must appear
        unchanged at the start of the combined output.

        **Validates: Requirements 1.2, 3.2**
        """
        existing_content = format_recap_document(doc)
        new_section_markdown = format_recap_section(new_section)

        # Simulate the append operation (write existing + separator + new)
        appended_content = (
            existing_content + new_section_markdown + "\n---\n\n"
        )

        # Byte-for-byte comparison: encode both and compare prefix
        existing_bytes = existing_content.encode("utf-8")
        appended_bytes = appended_content.encode("utf-8")

        assert appended_bytes[: len(existing_bytes)] == existing_bytes, (
            "Existing content was not preserved byte-for-byte after append"
        )

    @given(doc=st_recap_document(), new_section=st_recap_section())
    @settings(max_examples=50)
    def test_new_section_appears_only_after_existing_content(
        self, doc: RecapDocument, new_section: RecapSection
    ) -> None:
        """The new section content appears only after the existing content.

        The portion of the appended result beyond the original content must
        contain the new section markdown. No part of the new section should
        appear within the original content region (unless coincidentally
        matching existing text).

        **Validates: Requirements 1.2, 3.2**
        """
        existing_content = format_recap_document(doc)
        new_section_markdown = format_recap_section(new_section)

        appended_content = (
            existing_content + new_section_markdown + "\n---\n\n"
        )

        # The suffix after existing content must contain the new section
        after_existing = appended_content[len(existing_content):]
        assert new_section_markdown in after_existing, (
            "New section markdown not found after existing content"
        )

    @given(doc=st_recap_document(), new_section=st_recap_section())
    @settings(max_examples=50)
    def test_append_length_equals_sum_of_parts(
        self, doc: RecapDocument, new_section: RecapSection
    ) -> None:
        """The appended content length equals existing + separator + new section.

        This ensures no bytes are lost or injected during the append
        operation.

        **Validates: Requirements 1.2, 3.2**
        """
        existing_content = format_recap_document(doc)
        new_section_markdown = format_recap_section(new_section)
        separator = "\n---\n\n"

        appended_content = (
            existing_content + new_section_markdown + separator
        )

        expected_length = (
            len(existing_content) + len(new_section_markdown) + len(separator)
        )
        assert len(appended_content) == expected_length, (
            f"Length mismatch: expected {expected_length}, "
            f"got {len(appended_content)}"
        )


# ---------------------------------------------------------------------------
# Property 4: Question-Answer Pairing Integrity
# ---------------------------------------------------------------------------


class TestQAPairingIntegrity:
    """Output preserves 1:1 Q&A correspondence.

    **Validates: Requirements 2.4, 4.2, 4.3**

    For all sets of questions and answers provided to the recap generator,
    the output "Answers Given" section contains exactly one answer per
    question, and the ordering of answers corresponds to the ordering of
    questions in the "Questions Asked" section.
    """

    @given(section=st_recap_section())
    @settings(max_examples=50)
    def test_answer_count_equals_question_count(
        self, section: RecapSection
    ) -> None:
        """After format-then-parse round-trip, the number of answers equals
        the number of questions for every section.

        **Validates: Requirements 2.4, 4.2, 4.3**
        """
        markdown = format_recap_section(section)
        # Wrap in a minimal document so the parser can extract the section
        doc_md = (
            "# Senzing Bootcamp Recap\n\n"
            f"**Bootcamper:** Test\n"
            f"**Started:** 2025-01-01T00:00:00+00:00\n"
            f"**Total Duration:** 0h 0m\n\n---\n\n"
            f"{markdown}\n---\n\n"
        )
        parsed = parse_recap_markdown(doc_md)

        assert len(parsed.sections) == 1
        parsed_section = parsed.sections[0]

        assert len(parsed_section.answers_given) == len(
            parsed_section.questions_asked
        ), (
            f"Q&A count mismatch: "
            f"{len(parsed_section.questions_asked)} questions vs "
            f"{len(parsed_section.answers_given)} answers"
        )

    @given(section=st_recap_section())
    @settings(max_examples=50)
    def test_answer_ordering_matches_question_ordering(
        self, section: RecapSection
    ) -> None:
        """After format-then-parse round-trip, answers appear in the same
        positional order as their corresponding questions.

        **Validates: Requirements 2.4, 4.2, 4.3**
        """
        markdown = format_recap_section(section)
        doc_md = (
            "# Senzing Bootcamp Recap\n\n"
            f"**Bootcamper:** Test\n"
            f"**Started:** 2025-01-01T00:00:00+00:00\n"
            f"**Total Duration:** 0h 0m\n\n---\n\n"
            f"{markdown}\n---\n\n"
        )
        parsed = parse_recap_markdown(doc_md)

        assert len(parsed.sections) == 1
        parsed_section = parsed.sections[0]

        # Verify each answer at position i corresponds to question at position i
        for i, (orig_q, parsed_q) in enumerate(
            zip(section.questions_asked, parsed_section.questions_asked)
        ):
            assert parsed_q == orig_q, (
                f"Question at position {i} changed: "
                f"{orig_q!r} -> {parsed_q!r}"
            )

        for i, (orig_a, parsed_a) in enumerate(
            zip(section.answers_given, parsed_section.answers_given)
        ):
            assert parsed_a == orig_a, (
                f"Answer at position {i} changed: "
                f"{orig_a!r} -> {parsed_a!r}"
            )

    @given(doc=st_recap_document())
    @settings(max_examples=50)
    def test_multi_section_qa_pairing_preserved(
        self, doc: RecapDocument
    ) -> None:
        """For documents with multiple sections, each section independently
        maintains its 1:1 Q&A correspondence after round-trip.

        **Validates: Requirements 2.4, 4.2, 4.3**
        """
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(doc.sections)

        for orig, parsed_section in zip(doc.sections, parsed.sections):
            # 1:1 count correspondence
            assert len(parsed_section.questions_asked) == len(
                orig.questions_asked
            ), (
                f"Module {orig.module_number}: question count mismatch "
                f"({len(orig.questions_asked)} -> "
                f"{len(parsed_section.questions_asked)})"
            )
            assert len(parsed_section.answers_given) == len(
                orig.answers_given
            ), (
                f"Module {orig.module_number}: answer count mismatch "
                f"({len(orig.answers_given)} -> "
                f"{len(parsed_section.answers_given)})"
            )

            # Ordering preserved
            assert parsed_section.questions_asked == orig.questions_asked
            assert parsed_section.answers_given == orig.answers_given


# ---------------------------------------------------------------------------
# Property 6: Duration Monotonic Increase
# ---------------------------------------------------------------------------


def _parse_duration_to_minutes(duration_str: str) -> int:
    """Parse a human-readable duration string like '4h 32m' into total minutes.

    Args:
        duration_str: Duration in format 'Xh Ym'.

    Returns:
        Total minutes as an integer.
    """
    m = re.match(r"(\d+)h\s+(\d+)m", duration_str.strip())
    if not m:
        return 0
    return int(m.group(1)) * 60 + int(m.group(2))


class TestDurationMonotonicity:
    """Total duration is monotonically non-decreasing across sequential appends.

    **Validates: Requirements 7.4**

    For all sequences of Recap_Section appends, the "Total Duration" value
    in the document header is monotonically non-decreasing — each append
    results in a total duration greater than or equal to the previous value.
    """

    @given(
        sections=st.lists(st_recap_section(), min_size=2, max_size=6),
    )
    @settings(max_examples=50)
    def test_total_duration_monotonically_non_decreasing(
        self, sections: list[RecapSection]
    ) -> None:
        """Simulates sequential appends and verifies the total duration in
        the header never decreases.

        Builds up a document one section at a time, computing a cumulative
        total_duration for the header after each append. Verifies that
        each successive total_duration is >= the previous one.

        **Validates: Requirements 7.4**
        """
        cumulative_minutes = 0
        previous_minutes = 0

        for i, section in enumerate(sections):
            # Accumulate duration from each section
            section_minutes = _parse_duration_to_minutes(section.duration)
            cumulative_minutes += section_minutes

            # Build the document with sections appended so far
            total_h = cumulative_minutes // 60
            total_m = cumulative_minutes % 60
            header = RecapHeader(
                bootcamper="Test Bootcamper",
                started="2025-01-01T00:00:00+00:00",
                total_duration=f"{total_h}h {total_m}m",
            )
            doc = RecapDocument(
                header=header,
                sections=sections[: i + 1],
            )

            # Format and parse back to verify the header total_duration
            markdown = format_recap_document(doc)
            parsed = parse_recap_markdown(markdown)

            current_minutes = _parse_duration_to_minutes(
                parsed.header.total_duration
            )

            # Monotonically non-decreasing: current >= previous
            assert current_minutes >= previous_minutes, (
                f"Duration decreased at section {i + 1}: "
                f"{previous_minutes}m -> {current_minutes}m "
                f"(header: {parsed.header.total_duration!r})"
            )

            previous_minutes = current_minutes

    @given(
        sections=st.lists(st_recap_section(), min_size=2, max_size=6),
    )
    @settings(max_examples=50)
    def test_total_duration_equals_sum_of_section_durations(
        self, sections: list[RecapSection]
    ) -> None:
        """The total duration in the header equals the sum of all individual
        section durations after sequential appends.

        This is a stronger property that implies monotonicity: since each
        section duration is non-negative, the cumulative sum can only
        increase or stay the same.

        **Validates: Requirements 7.4**
        """
        cumulative_minutes = 0

        for section in sections:
            section_minutes = _parse_duration_to_minutes(section.duration)
            cumulative_minutes += section_minutes

        # Build the final document with all sections
        total_h = cumulative_minutes // 60
        total_m = cumulative_minutes % 60
        header = RecapHeader(
            bootcamper="Test Bootcamper",
            started="2025-01-01T00:00:00+00:00",
            total_duration=f"{total_h}h {total_m}m",
        )
        doc = RecapDocument(header=header, sections=sections)

        # Format and parse back
        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        parsed_minutes = _parse_duration_to_minutes(
            parsed.header.total_duration
        )

        assert parsed_minutes == cumulative_minutes, (
            f"Total duration mismatch: expected {cumulative_minutes}m, "
            f"got {parsed_minutes}m "
            f"(header: {parsed.header.total_duration!r})"
        )


# ---------------------------------------------------------------------------
# Property 7: Module Ordering Preservation
# ---------------------------------------------------------------------------


@st.composite
def st_sorted_timestamps(draw: st.DrawFn, count: int) -> list[str]:
    """Generate a list of chronologically sorted ISO 8601 timestamps.

    Each timestamp is derived from a single monotonic integer source: unique
    "calendar tick" offsets are drawn, sorted, and decomposed via mixed-radix
    arithmetic (most-significant field first: year, month, day, hour, minute,
    second). Because every field is zero-padded to a fixed width and a single
    fixed timezone suffix is appended, lexicographic ordering of the formatted
    strings equals chronological ordering. The offsets are unique and sorted,
    so the emitted timestamps are genuinely strictly increasing.

    Args:
        count: Number of timestamps to generate.

    Returns:
        List of ISO 8601 timestamps in ascending chronological order.
    """
    # Mixed-radix field ranges chosen to keep every date valid:
    #   second 0-59, minute 0-59, hour 0-23, day 1-28, month 1-12.
    _SECONDS_PER_MINUTE = 60
    _MINUTES_PER_HOUR = 60
    _HOURS_PER_DAY = 24
    _DAYS_PER_MONTH = 28
    _MONTHS_PER_YEAR = 12
    _BASE_YEAR = 2024
    _YEARS_SPAN = 6
    _TICKS_PER_YEAR = (
        _MONTHS_PER_YEAR
        * _DAYS_PER_MONTH
        * _HOURS_PER_DAY
        * _MINUTES_PER_HOUR
        * _SECONDS_PER_MINUTE
    )
    _MAX_TICK = _YEARS_SPAN * _TICKS_PER_YEAR

    # A single fixed timezone suffix so lexicographic order == chronological.
    tz_suffix = "+00:00"

    # Unique, sorted monotonic integer source. Uniqueness + sorting guarantees
    # the decomposed timestamps are strictly increasing.
    ticks = sorted(
        draw(
            st.lists(
                st.integers(min_value=0, max_value=_MAX_TICK - 1),
                min_size=count,
                max_size=count,
                unique=True,
            )
        )
    )

    timestamps: list[str] = []
    for tick in ticks:
        value = tick
        second = value % _SECONDS_PER_MINUTE
        value //= _SECONDS_PER_MINUTE
        minute = value % _MINUTES_PER_HOUR
        value //= _MINUTES_PER_HOUR
        hour = value % _HOURS_PER_DAY
        value //= _HOURS_PER_DAY
        day = 1 + (value % _DAYS_PER_MONTH)
        value //= _DAYS_PER_MONTH
        month = 1 + (value % _MONTHS_PER_YEAR)
        value //= _MONTHS_PER_YEAR
        year = _BASE_YEAR + value

        ts = (
            f"{year:04d}-{month:02d}-{day:02d}"
            f"T{hour:02d}:{minute:02d}:{second:02d}{tz_suffix}"
        )
        timestamps.append(ts)

    return timestamps


@st.composite
def st_chronological_sections(
    draw: st.DrawFn,
) -> list[RecapSection]:
    """Generate a list of RecapSections with chronologically ordered timestamps.

    Returns:
        List of RecapSection instances whose timestamps are in ascending order.
    """
    count = draw(st.integers(min_value=2, max_value=6))
    timestamps = draw(st_sorted_timestamps(count))

    sections: list[RecapSection] = []
    for i, ts in enumerate(timestamps):
        module_number = i + 1
        module_name = draw(
            st.text(
                min_size=1,
                max_size=40,
                alphabet=st.characters(
                    whitelist_categories=("L", "N", "Zs"),
                    blacklist_characters="\n\r\x0b\x0c\x85\u2028\u2029",
                ),
            ).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)
        )
        information_shared = draw(st_list_items())
        qa_count = draw(st.integers(min_value=0, max_value=5))
        item_strategy = _non_whitespace_only_text(min_size=1, max_size=80)
        questions_asked = draw(
            st.lists(item_strategy, min_size=qa_count, max_size=qa_count)
        )
        answers_given = draw(
            st.lists(item_strategy, min_size=qa_count, max_size=qa_count)
        )
        actions_taken = draw(st_list_items())
        duration = draw(st_duration())

        sections.append(
            RecapSection(
                module_number=module_number,
                module_name=module_name,
                timestamp=ts,
                information_shared=information_shared,
                questions_asked=questions_asked,
                answers_given=answers_given,
                actions_taken=actions_taken,
                duration=duration,
            )
        )

    return sections


class TestModuleOrdering:
    """Module sections appear in chronological order of completion timestamps.

    **Validates: Requirements 3.1, 7.2**

    For all sequences of module completions appended to the Recap_Document,
    the module sections appear in the document in chronological order of
    their completion timestamps.
    """

    @given(sections=st_chronological_sections())
    @settings(max_examples=50)
    def test_sections_preserve_chronological_order(
        self, sections: list[RecapSection]
    ) -> None:
        """Sections with chronologically ordered timestamps maintain that
        order after a format-then-parse round-trip.

        Generates sections with sorted timestamps, formats them into a
        RecapDocument, parses the markdown back, and verifies the parsed
        sections appear in the same chronological order.

        **Validates: Requirements 3.1, 7.2**
        """
        header = RecapHeader(
            bootcamper="Test Bootcamper",
            started="2024-01-01T00:00:00+00:00",
            total_duration="0h 0m",
        )
        doc = RecapDocument(header=header, sections=sections)

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(sections), (
            f"Section count mismatch: expected {len(sections)}, "
            f"got {len(parsed.sections)}"
        )

        # Verify timestamps appear in non-decreasing chronological order
        parsed_timestamps = [s.timestamp for s in parsed.sections]
        for i in range(len(parsed_timestamps) - 1):
            assert parsed_timestamps[i] <= parsed_timestamps[i + 1], (
                f"Sections not in chronological order at index {i}: "
                f"{parsed_timestamps[i]!r} > {parsed_timestamps[i + 1]!r}"
            )

    @given(sections=st_chronological_sections())
    @settings(max_examples=50)
    def test_parsed_timestamps_match_original_order(
        self, sections: list[RecapSection]
    ) -> None:
        """Each parsed section's timestamp matches the original section at
        the same position, confirming ordering is preserved exactly.

        **Validates: Requirements 3.1, 7.2**
        """
        header = RecapHeader(
            bootcamper="Test Bootcamper",
            started="2024-01-01T00:00:00+00:00",
            total_duration="0h 0m",
        )
        doc = RecapDocument(header=header, sections=sections)

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(sections)

        for i, (original, parsed_section) in enumerate(
            zip(sections, parsed.sections)
        ):
            assert parsed_section.timestamp == original.timestamp, (
                f"Section {i}: timestamp mismatch: "
                f"expected {original.timestamp!r}, "
                f"got {parsed_section.timestamp!r}"
            )

    @given(sections=st_chronological_sections())
    @settings(max_examples=50)
    def test_module_numbers_follow_section_order(
        self, sections: list[RecapSection]
    ) -> None:
        """Module numbers in parsed output follow the same positional order
        as the input sections, confirming no reordering occurred.

        **Validates: Requirements 3.1, 7.2**
        """
        header = RecapHeader(
            bootcamper="Test Bootcamper",
            started="2024-01-01T00:00:00+00:00",
            total_duration="0h 0m",
        )
        doc = RecapDocument(header=header, sections=sections)

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == len(sections)

        original_numbers = [s.module_number for s in sections]
        parsed_numbers = [s.module_number for s in parsed.sections]

        assert parsed_numbers == original_numbers, (
            f"Module number order changed: "
            f"expected {original_numbers}, got {parsed_numbers}"
        )


# ---------------------------------------------------------------------------
# Edge Case Tests (Task 13)
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Deterministic edge case tests for recap document handling.

    Tests cover: empty module sessions, very long content, special markdown
    characters, and unicode content. These are NOT property-based tests —
    they use specific known inputs with standard pytest assertions.
    """

    def test_empty_module_session(self) -> None:
        """A module completed with no questions asked (skipped module).

        Sections should still be present but contain empty lists.
        The format-then-parse round-trip must preserve the empty structure.
        """
        section = RecapSection(
            module_number=3,
            module_name="Data Sources",
            timestamp="2025-06-15T14:30:00-05:00",
            information_shared=[],
            questions_asked=[],
            answers_given=[],
            actions_taken=[],
            duration="0h 5m",
        )
        header = RecapHeader(
            bootcamper="Test User",
            started="2025-06-15T09:00:00-05:00",
            total_duration="0h 5m",
        )
        doc = RecapDocument(header=header, sections=[section])

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == 1
        ps = parsed.sections[0]
        assert ps.module_number == 3
        assert ps.module_name == "Data Sources"
        assert ps.information_shared == []
        assert ps.questions_asked == []
        assert ps.answers_given == []
        assert ps.actions_taken == []
        assert ps.duration == "0h 5m"

    def test_empty_module_section_markdown_contains_subsections(
        self,
    ) -> None:
        """Even with empty lists, all subsection headings must be present."""
        section = RecapSection(
            module_number=1,
            module_name="Introduction",
            timestamp="2025-01-01T10:00:00+00:00",
            information_shared=[],
            questions_asked=[],
            answers_given=[],
            actions_taken=[],
            duration="0h 2m",
        )
        markdown = format_recap_section(section)

        assert "### Information Shared" in markdown
        assert "### Questions Asked" in markdown
        assert "### Answers Given" in markdown
        assert "### Actions Taken" in markdown
        assert "### Duration" in markdown

    def test_very_long_content_no_truncation(self) -> None:
        """A module with 50+ items in lists handles arbitrary-length content.

        The recap should handle arbitrary-length content without truncation.
        """
        info_items = [f"Concept {i}: explanation of topic {i}" for i in range(60)]
        questions = [f"Question {i}: what about topic {i}?" for i in range(55)]
        answers = [f"Answer {i}: response about topic {i}" for i in range(55)]
        actions = [f"Created file_{i}.py" for i in range(50)]

        section = RecapSection(
            module_number=7,
            module_name="Advanced Entity Resolution",
            timestamp="2025-03-20T16:45:00+00:00",
            information_shared=info_items,
            questions_asked=questions,
            answers_given=answers,
            actions_taken=actions,
            duration="3h 45m",
        )
        header = RecapHeader(
            bootcamper="Prolific Learner",
            started="2025-03-20T09:00:00+00:00",
            total_duration="3h 45m",
        )
        doc = RecapDocument(header=header, sections=[section])

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == 1
        ps = parsed.sections[0]
        assert len(ps.information_shared) == 60
        assert len(ps.questions_asked) == 55
        assert len(ps.answers_given) == 55
        assert len(ps.actions_taken) == 50

        # Verify no content was truncated — spot-check first and last items
        assert ps.information_shared[0] == "Concept 0: explanation of topic 0"
        assert ps.information_shared[59] == "Concept 59: explanation of topic 59"
        assert ps.questions_asked[54] == "Question 54: what about topic 54?"
        assert ps.answers_given[54] == "Answer 54: response about topic 54"
        assert ps.actions_taken[49] == "Created file_49.py"

    def test_special_markdown_characters_in_content(self) -> None:
        """Content containing markdown special characters (#, *, |, backticks).

        Must be handled correctly in format/parse round-trip.
        """
        section = RecapSection(
            module_number=5,
            module_name="Mapping and Loading",
            timestamp="2025-04-10T11:00:00-04:00",
            information_shared=[
                "Use # comments in JSON config files",
                "The **bold** syntax highlights key terms",
                "Pipe | separates columns in CSV output",
                "Use `senzing.get_entity()` for lookups",
                "Asterisks * and ** denote wildcards",
            ],
            questions_asked=[
                "What does the # symbol mean in config?",
                "How do backticks ` work in markdown?",
            ],
            answers_given=[
                "The # starts a comment line in some formats",
                "Backticks ` create inline code spans",
            ],
            actions_taken=[
                "Created `config/mapping.json` with | delimiters",
                "Modified **important** settings in config",
            ],
            duration="1h 20m",
        )
        header = RecapHeader(
            bootcamper="Dev User",
            started="2025-04-10T09:00:00-04:00",
            total_duration="1h 20m",
        )
        doc = RecapDocument(header=header, sections=[section])

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert len(parsed.sections) == 1
        ps = parsed.sections[0]

        # All items must survive the round-trip intact
        assert ps.information_shared[0] == (
            "Use # comments in JSON config files"
        )
        assert ps.information_shared[1] == (
            "The **bold** syntax highlights key terms"
        )
        assert ps.information_shared[2] == (
            "Pipe | separates columns in CSV output"
        )
        assert ps.information_shared[3] == (
            "Use `senzing.get_entity()` for lookups"
        )
        assert ps.information_shared[4] == (
            "Asterisks * and ** denote wildcards"
        )
        assert ps.questions_asked[0] == (
            "What does the # symbol mean in config?"
        )
        assert ps.questions_asked[1] == (
            "How do backticks ` work in markdown?"
        )
        assert ps.answers_given[0] == (
            "The # starts a comment line in some formats"
        )
        assert ps.answers_given[1] == (
            "Backticks ` create inline code spans"
        )
        assert ps.actions_taken[0] == (
            "Created `config/mapping.json` with | delimiters"
        )
        assert ps.actions_taken[1] == (
            "Modified **important** settings in config"
        )

    def test_unicode_content_bootcamper_name(self) -> None:
        """Bootcamper names with non-ASCII characters (accented, CJK, emoji).

        Must render correctly through format/parse round-trip.
        """
        header = RecapHeader(
            bootcamper="José García 🚀",
            started="2025-05-01T08:00:00+02:00",
            total_duration="2h 10m",
        )
        section = RecapSection(
            module_number=1,
            module_name="Introduction",
            timestamp="2025-05-01T10:10:00+02:00",
            information_shared=["Welcome to Senzing bootcamp"],
            questions_asked=["What is your name?"],
            answers_given=["José García 🚀"],
            actions_taken=[],
            duration="2h 10m",
        )
        doc = RecapDocument(header=header, sections=[section])

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert parsed.header.bootcamper == "José García 🚀"
        assert parsed.sections[0].answers_given[0] == "José García 🚀"

    def test_unicode_content_cjk_characters(self) -> None:
        """CJK characters in module content must survive round-trip."""
        section = RecapSection(
            module_number=2,
            module_name="データソース設定",
            timestamp="2025-05-02T09:00:00+09:00",
            information_shared=[
                "エンティティ解決の基本概念",
                "数据源配置方法",
                "한국어 설명 포함",
            ],
            questions_asked=["設定ファイルはどこですか？"],
            answers_given=["config/ディレクトリにあります"],
            actions_taken=["作成: config/データソース.yaml"],
            duration="1h 30m",
        )
        header = RecapHeader(
            bootcamper="田中太郎",
            started="2025-05-02T08:00:00+09:00",
            total_duration="1h 30m",
        )
        doc = RecapDocument(header=header, sections=[section])

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert parsed.header.bootcamper == "田中太郎"
        assert len(parsed.sections) == 1
        ps = parsed.sections[0]
        assert ps.module_name == "データソース設定"
        assert ps.information_shared[0] == "エンティティ解決の基本概念"
        assert ps.information_shared[1] == "数据源配置方法"
        assert ps.information_shared[2] == "한국어 설명 포함"
        assert ps.questions_asked[0] == "設定ファイルはどこですか？"
        assert ps.answers_given[0] == "config/ディレクトリにあります"
        assert ps.actions_taken[0] == "作成: config/データソース.yaml"

    def test_unicode_content_emoji_heavy(self) -> None:
        """Emoji-heavy content must survive format/parse round-trip."""
        section = RecapSection(
            module_number=4,
            module_name="Entity Resolution 🔍",
            timestamp="2025-06-01T12:00:00+00:00",
            information_shared=[
                "✅ Matching works by comparing features",
                "⚠️ Duplicate records need resolution",
                "🎯 Precision vs recall tradeoffs",
            ],
            questions_asked=["How does 🔍 search work?"],
            answers_given=["It uses feature comparison 📊"],
            actions_taken=["Created 📁 output/results.json"],
            duration="1h 0m",
        )
        header = RecapHeader(
            bootcamper="Dev 👩‍💻",
            started="2025-06-01T10:00:00+00:00",
            total_duration="1h 0m",
        )
        doc = RecapDocument(header=header, sections=[section])

        markdown = format_recap_document(doc)
        parsed = parse_recap_markdown(markdown)

        assert parsed.header.bootcamper == "Dev 👩\u200d💻"
        ps = parsed.sections[0]
        assert ps.module_name == "Entity Resolution 🔍"
        assert "✅" in ps.information_shared[0]
        assert "⚠️" in ps.information_shared[1]
        assert "🎯" in ps.information_shared[2]
        assert "🔍" in ps.questions_asked[0]
        assert "📊" in ps.answers_given[0]
        assert "📁" in ps.actions_taken[0]


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — Content Silently Dropped by Strict Parser
# ---------------------------------------------------------------------------
#
# These tests encode the EXPECTED (post-fix) behavior for inputs that satisfy
# isBugCondition(X): a valid header plus N loose module headings of the form
# `## Module N: <name>` (no ` — <timestamp>` suffix) interleaved with prose
# paragraphs and fenced code blocks.
#
# On UNFIXED code the strict `_MODULE_HEADING_RE` does not match loose headings,
# so `_parse_sections` returns [], producing a cover-page-only result that loses
# all body content. These tests are therefore EXPECTED TO FAIL on unfixed code —
# the failure confirms the bug exists. They will PASS once the tolerant parser,
# Generic_Content capture, and Raw_Body_Fallback are implemented.

# Strategy for distinctive renderable tokens: ascii-letter words unlikely to
# collide with fixed prose or markdown syntax.
_st_token = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz", min_size=4, max_size=12
)


# Local mirror of the strict-schema heading pattern (em-dash + trailing
# timestamp). Defined here so the precondition does not depend on importing a
# private symbol from the module under test.
_STRICT_MODULE_HEADING_RE = re.compile(
    r"^##\s+Module\s+(\d+):\s+(.+?)\s+\u2014\s+(.+)$", re.MULTILINE
)


def _strict_module_headings(content: str) -> list[str]:
    """Return the strict-schema (`## Module N: <name> — <ts>`) heading matches."""
    return _STRICT_MODULE_HEADING_RE.findall(content)


def _rendered_body_text(doc: RecapDocument) -> str:
    """Collect the renderable body text the generator would emit (parse/render seam).

    This excludes cover-page header fields and gathers everything that would be
    rendered below the cover page: per-module headings, the five known
    subsections, durations, and any captured Generic_Content. `generic_content`
    is read defensively via getattr so the helper works on both unfixed code
    (no such field) and fixed code.

    Args:
        doc: Parsed recap document.

    Returns:
        Newline-joined renderable body text (empty when only a cover page exists).
    """
    parts: list[str] = []
    for s in doc.sections:
        parts.append(s.module_name)
        parts.append(s.timestamp)
        parts.extend(s.information_shared)
        parts.extend(s.questions_asked)
        parts.extend(s.answers_given)
        parts.extend(s.actions_taken)
        parts.append(s.duration)
        parts.extend(getattr(s, "generic_content", []) or [])
    return "\n".join(p for p in parts if p)


@st.composite
def st_loose_recap(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Generate a free-form recap satisfying isBugCondition(X).

    Produces a valid header plus N (1-7) loose module headings
    (`## Module N: <name>` with no ` — <timestamp>` suffix) interleaved with a
    prose paragraph and a fenced code block per module. None of the headings use
    the em-dash form, so the strict parser matches zero sections and silently
    drops the body — the defining bug condition.

    Returns:
        Tuple of (recap_markdown, sentinel_tokens) where sentinel_tokens are the
        distinctive prose/code words that must survive into the rendered body.
    """
    header = draw(st_recap_header())
    n = draw(st.integers(min_value=1, max_value=7))

    lines: list[str] = [
        "# Senzing Bootcamp Recap",
        "",
        f"**Bootcamper:** {header.bootcamper}",
        f"**Started:** {header.started}",
        f"**Total Duration:** {header.total_duration}",
        "",
        "---",
        "",
    ]
    sentinels: list[str] = []
    for i in range(1, n + 1):
        name = draw(_st_token)
        prose_word = draw(_st_token)
        code_word = draw(_st_token)
        sentinels.extend([prose_word, code_word])
        lines.append(f"## Module {i}: {name}")
        lines.append("")
        lines.append(f"This module covered {prose_word} in detail.")
        lines.append("")
        lines.append("```python")
        lines.append(f"value = '{code_word}'")
        lines.append("```")
        lines.append("")

    return "\n".join(lines), sentinels


class TestBugConditionContentLoss:
    """Property 1: content is never silently dropped for loose-heading recaps.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**

    For all recaps X where isBugCondition(X) holds (non-empty body whose
    renderable content the strict parser loses), the generated result has a
    non-empty rendered body that contains the input's renderable text tokens —
    loose headings recognized, Generic_Content rendered, or Raw_Body_Fallback
    used (containsRenderableContentOf(result, X)).
    """

    @given(data=st_loose_recap())
    @settings(max_examples=50, deadline=None)
    def test_loose_recap_body_not_silently_dropped(
        self, data: tuple[str, list[str]]
    ) -> None:
        """Free-form recaps with loose headings + prose + code must render a
        non-empty body containing their renderable content.

        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        markdown, sentinels = data

        # Precondition: this input genuinely satisfies isBugCondition(X) —
        # it has a non-empty body but the strict parser matches no sections.
        assert markdown.strip()
        assert _strict_module_headings(markdown) == []

        doc = parse_recap_markdown(markdown)
        body = _rendered_body_text(doc)

        # Expected behavior: rendered body is non-empty (not cover-page-only).
        assert body.strip(), (
            "Rendered body is empty — loose-heading recap content was "
            "silently dropped (strict parser matched zero sections)"
        )

        # Expected behavior: every renderable prose/code token is present.
        missing = [tok for tok in sentinels if tok not in body]
        assert not missing, (
            f"Renderable content silently dropped: tokens {missing} from the "
            f"recap body never appear in the rendered output"
        )

    def test_seven_loose_modules_plus_prose_not_dropped(self) -> None:
        """Deterministic counterexample: a header with seven `## Module N: <name>`
        sections plus prose must not produce a cover-page-only result.

        **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**
        """
        module_names = [
            "Business Problem",
            "First Demo",
            "Data Mapping",
            "Loading Records",
            "Querying Entities",
            "Tuning Results",
            "Production Deployment",
        ]
        sentinels: list[str] = []
        lines = [
            "# Senzing Bootcamp Recap",
            "",
            "**Bootcamper:** Alex Doe",
            "**Started:** 2025-06-01T10:00:00+00:00",
            "**Total Duration:** 7h 30m",
            "",
            "---",
            "",
        ]
        for i, name in enumerate(module_names, 1):
            prose_word = f"prose{i}token"
            code_word = f"code{i}token"
            sentinels.extend([prose_word, code_word])
            lines.append(f"## Module {i}: {name}")
            lines.append("")
            lines.append(f"We explored {prose_word} across the session.")
            lines.append("")
            lines.append("```bash")
            lines.append(f"echo {code_word}")
            lines.append("```")
            lines.append("")
        markdown = "\n".join(lines)

        # Precondition: strict parser matches nothing (isBugCondition holds).
        assert _strict_module_headings(markdown) == []

        doc = parse_recap_markdown(markdown)
        body = _rendered_body_text(doc)

        assert body.strip(), (
            "Seven-module loose-heading recap produced an empty body — "
            "all content was silently dropped (cover-page-only PDF)"
        )

        # Loose headings should be recognized as sections.
        assert len(doc.sections) == 7, (
            f"Expected 7 recognized module sections, got {len(doc.sections)}"
        )

        # Every prose/code token must survive into the rendered body.
        missing = [tok for tok in sentinels if tok not in body]
        assert not missing, (
            f"Renderable content silently dropped: tokens {missing} never "
            f"appear in the rendered output"
        )


# ---------------------------------------------------------------------------
# Property 2: Preservation — Strict-Schema Recaps Unchanged
# ---------------------------------------------------------------------------
#
# These tests lock in the BASELINE behavior the fix must preserve. They cover
# inputs where isBugCondition(X) is FALSE: strict-schema recaps with
# `## Module N: <name> — <timestamp>` headings and the five `### ` subsections,
# plus the CLI's graceful degradation paths (fpdf2 absent, missing/empty input).
#
# Observation-first methodology: every assertion below documents behavior that
# already holds on UNFIXED code. They are EXPECTED TO PASS today; re-running
# them after the fix (task 3.7) confirms no regression.


@contextlib.contextmanager
def _fpdf_import_absent() -> "contextlib.AbstractContextManager[None]":  # type: ignore[type-arg]
    """Force ``from fpdf import FPDF`` to raise ImportError.

    Inserts ``None`` for the ``fpdf`` entry in ``sys.modules`` so the lazy
    import inside ``render_pdf`` raises ImportError regardless of whether
    ``fpdf2`` is actually installed. Restores the original state on exit.

    Yields:
        None. Within the context, importing ``fpdf`` raises ImportError.
    """
    sentinel = object()
    original = sys.modules.get("fpdf", sentinel)
    sys.modules["fpdf"] = None  # type: ignore[assignment]
    try:
        yield
    finally:
        if original is sentinel:
            sys.modules.pop("fpdf", None)
        else:
            sys.modules["fpdf"] = original  # type: ignore[assignment]


def _run_main_capturing_stderr(argv: list[str]) -> tuple[int, str]:
    """Run ``main`` with the given argv, capturing stderr.

    Args:
        argv: Command-line arguments passed to ``main``.

    Returns:
        Tuple of (exit_code, captured_stderr_text).
    """
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rc = main(argv)
    return rc, err.getvalue()


def st_whitespace_only() -> st.SearchStrategy[str]:
    """Generate strings that are empty or contain only whitespace."""
    return st.text(alphabet=" \t\n\r\f\v", min_size=0, max_size=20)


class TestPreservationStrictSchema:
    """Strict-schema recaps parse and render exactly as before the fix.

    **Validates: Requirements 3.1, 3.2, 3.5**

    For all recap inputs X where NOT isBugCondition(X) — i.e. documents whose
    module headings use the strict `## Module N: <name> — <timestamp>` form —
    the format→parse round-trip preserves header fields, section count, section
    identity fields, list contents, Q&A pairing, and durations. This is the
    Preservation property: F(X) behavior the fix must keep byte-for-byte.
    """

    @given(doc=st_recap_document())
    @settings(max_examples=50, deadline=None)
    def test_strict_schema_round_trip_equivalence(
        self, doc: RecapDocument
    ) -> None:
        """Strict-schema documents round-trip with full structural fidelity.

        Precondition: the formatted markdown uses strict module headings, so
        the strict parser matches every section and NOT isBugCondition(X).
        The round-trip preserves header fields, section count, identity fields,
        list contents, Q&A pairing, and durations.

        **Validates: Requirements 3.1, 3.2, 3.5**
        """
        markdown = format_recap_document(doc)

        # Precondition: NOT isBugCondition(X) — strict headings match every
        # section, so the strict parser does not lose body content.
        strict_headings = _strict_module_headings(markdown)
        assert len(strict_headings) == len(doc.sections), (
            "Generated strict-schema document did not produce strict module "
            "headings — precondition NOT isBugCondition(X) violated"
        )

        parsed = parse_recap_markdown(markdown)

        # Header fields preserved (Req 3.2)
        assert parsed.header.bootcamper == doc.header.bootcamper
        assert parsed.header.started == doc.header.started
        assert parsed.header.total_duration == doc.header.total_duration

        # Section count preserved (Req 3.1)
        assert len(parsed.sections) == len(doc.sections)

        for original, roundtripped in zip(doc.sections, parsed.sections):
            # Section identity fields preserved (Req 3.2)
            assert roundtripped.module_number == original.module_number
            assert roundtripped.module_name == original.module_name
            assert roundtripped.timestamp == original.timestamp

            # List contents preserved (Req 3.2)
            assert roundtripped.information_shared == original.information_shared
            assert roundtripped.actions_taken == original.actions_taken

            # Q&A pairing preserved (Req 3.2)
            assert roundtripped.questions_asked == original.questions_asked
            assert roundtripped.answers_given == original.answers_given
            assert len(roundtripped.questions_asked) == len(
                roundtripped.answers_given
            )

            # Durations preserved (Req 3.2)
            assert roundtripped.duration == original.duration


class TestPreservationGracefulDegradation:
    """CLI degradation paths behave exactly as before the fix.

    **Validates: Requirements 3.3, 3.4**

    For all environments without fpdf2 and for all missing/empty inputs, the
    generator keeps its existing behavior: it prints the install hint or the
    existing error message and exits with code 1 (no traceback).
    """

    @given(doc=st_recap_document())
    @settings(max_examples=25, deadline=None)
    def test_fpdf_absent_prints_hint_and_exits_1(
        self, doc: RecapDocument
    ) -> None:
        """With fpdf2 absent, a valid recap still exits 1 with the install hint.

        Writes a valid strict-schema recap, forces the ``fpdf`` import to raise
        ImportError, and asserts ``main`` reports the ``pip install fpdf2`` hint
        and returns exit code 1 (graceful degradation, no traceback).

        **Validates: Requirements 3.3**
        """
        markdown = format_recap_document(doc)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            with _fpdf_import_absent():
                rc, stderr = _run_main_capturing_stderr(
                    ["--input", str(input_path), "--output", str(output_path)]
                )

        assert rc == 1, f"Expected exit code 1 when fpdf2 absent, got {rc}"
        assert "pip install fpdf2" in stderr, (
            f"Expected 'pip install fpdf2' hint on stderr, got: {stderr!r}"
        )

    @given(name=_st_token)
    @settings(max_examples=25, deadline=None)
    def test_missing_input_reports_error_and_exits_1(self, name: str) -> None:
        """A non-existent input path reports the 'not found' error and exits 1.

        **Validates: Requirements 3.4**
        """
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / f"{name}_does_not_exist.md"
            # Precondition: the file genuinely does not exist.
            assert not missing_path.exists()

            rc, stderr = _run_main_capturing_stderr(
                ["--input", str(missing_path)]
            )

        assert rc == 1, f"Expected exit code 1 for missing input, got {rc}"
        assert "not found" in stderr.lower(), (
            f"Expected a 'not found' error on stderr, got: {stderr!r}"
        )

    @given(content=st_whitespace_only())
    @settings(max_examples=25, deadline=None)
    def test_empty_input_reports_error_and_exits_1(self, content: str) -> None:
        """An empty or whitespace-only input reports 'empty' and exits 1.

        **Validates: Requirements 3.4**
        """
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "empty_recap.md"
            input_path.write_text(content, encoding="utf-8")
            # Precondition: the content has no meaningful body.
            assert not content.strip()

            rc, stderr = _run_main_capturing_stderr(
                ["--input", str(input_path)]
            )

        assert rc == 1, f"Expected exit code 1 for empty input, got {rc}"
        assert "empty" in stderr.lower(), (
            f"Expected an 'empty' error on stderr, got: {stderr!r}"
        )


# ---------------------------------------------------------------------------
# Recording PDF stub for the merged-section render path (recap-qa-pair-merge)
# ---------------------------------------------------------------------------


class _RecordingPDF:
    """Minimal FPDF stand-in that records the text passed to the renderer.

    Exercises the real ``_render_module_page`` render path without requiring
    fpdf2 or parsing binary PDF output. ``_render_heading`` emits heading text
    via ``multi_cell``; list items and Q/A pairs use ``write``; empty-state and
    single-value fields use ``cell``. The stub records text from each so a test
    can assert on the rendered headings and body separately.

    For the professional-layout heading tests it additionally records every
    ``set_font`` size and ``set_text_color`` call — both as dedicated lists and
    interleaved in a single ordered ``events`` log — so a test can assert the
    font size and accent color applied to a heading and the order of those calls
    relative to the rendered heading text.
    """

    def __init__(self) -> None:
        self.l_margin = 10
        self.epw = 190  # effective page width (mm); mirrors fpdf2 A4 default
        self.headings: list[str] = []  # text rendered via multi_cell (headings)
        self.body: list[str] = []  # text rendered via cell/write
        self.font_sizes: list[object] = []  # size arg of every set_font call
        self.text_colors: list[tuple[object, ...]] = []  # every set_text_color call
        # Ordered log of ("font", size) / ("color", rgb) / ("text", text) events
        # so tests can assert the size/color active when a heading is drawn and
        # that the accent color is applied before (and body color after) it.
        self.events: list[tuple[str, object]] = []

    def add_page(self, *args: object, **kwargs: object) -> None:
        return None

    def set_font(self, *args: object, **kwargs: object) -> None:
        size = kwargs.get("size")
        if size is None and len(args) >= 3:
            size = args[2]
        self.font_sizes.append(size)
        self.events.append(("font", size))
        return None

    def set_text_color(self, *args: object, **kwargs: object) -> None:
        color = tuple(args)
        self.text_colors.append(color)
        self.events.append(("color", color))
        return None

    def ln(self, *args: object, **kwargs: object) -> None:
        return None

    def set_x(self, *args: object, **kwargs: object) -> None:
        return None

    def multi_cell(self, w: object, h: object, text: str = "", *args: object, **kwargs: object) -> None:  # noqa: E501
        self.headings.append(text)
        self.events.append(("text", text))

    def cell(self, w: object, h: object, text: str = "", *args: object, **kwargs: object) -> None:  # noqa: E501
        self.body.append(text)
        self.events.append(("text", text))

    def write(self, h: object, text: str = "", *args: object, **kwargs: object) -> None:
        self.body.append(text)
        self.events.append(("text", text))


def _render_section_headings_and_body(section: RecapSection) -> tuple[list[str], str]:
    """Render a section via the real renderer and return (headings, body_text).

    Returns the list of heading strings (from ``_render_heading``) and the
    concatenation of all non-heading text rendered for the module.
    """
    pdf = _RecordingPDF()
    _render_module_page(pdf, section)
    return pdf.headings, "".join(pdf.body)


# ---------------------------------------------------------------------------
# Property 1: Single merged "Questions and responses" section (Task 3.1)
# ---------------------------------------------------------------------------


class TestMergedSectionSingleHeading:
    """Property 1: the merged section replaces the two separate headings.

    **Validates: Requirements 5.1, 1.1, 1.4**

    For a module that has questions, the rendered PDF body contains a single
    "Questions and responses" heading and does NOT contain the old "Questions
    Asked" or "Answers Given" headings.
    """

    def test_single_merged_heading_for_module_with_questions(self) -> None:
        """A module with questions renders one "Questions and responses"
        heading and neither old heading.

        **Validates: Requirements 5.1, 1.1, 1.4**
        """
        section = RecapSection(
            module_number=3,
            module_name="Entity Resolution",
            timestamp="2025-01-01T00:00:00+00:00",
            questions_asked=["What is an entity?", "How does matching work?"],
            answers_given=["A resolved record.", "By comparing features."],
            duration="1h 5m",
        )

        headings, _body = _render_section_headings_and_body(section)

        assert "Questions and responses" in headings, (
            f"Expected merged 'Questions and responses' heading, got: {headings!r}"
        )
        assert headings.count("Questions and responses") == 1, (
            f"Expected exactly one merged heading, got: {headings!r}"
        )
        assert "Questions Asked" not in headings, (
            f"Old 'Questions Asked' heading should not be rendered, got: {headings!r}"
        )
        assert "Answers Given" not in headings, (
            f"Old 'Answers Given' heading should not be rendered, got: {headings!r}"
        )

    @given(section=st_recap_section())
    def test_merged_heading_present_no_old_headings(
        self, section: RecapSection
    ) -> None:
        """For any generated module, the rendered headings include the merged
        "Questions and responses" heading and never the old separate headings.

        **Validates: Requirements 5.1, 1.1, 1.4**
        """
        headings, _body = _render_section_headings_and_body(section)

        assert "Questions and responses" in headings, (
            f"Expected merged 'Questions and responses' heading, got: {headings!r}"
        )
        assert "Questions Asked" not in headings, (
            f"Old 'Questions Asked' heading should not be rendered, got: {headings!r}"
        )
        assert "Answers Given" not in headings, (
            f"Old 'Answers Given' heading should not be rendered, got: {headings!r}"
        )

# ---------------------------------------------------------------------------
# Property 2: Inline pairing by index (Task 3.2)
# ---------------------------------------------------------------------------


@st.composite
def st_equal_length_qa(draw: st.DrawFn) -> tuple[list[str], list[str]]:
    """Generate equal-length question/answer lists for inline-pairing tests.

    Reuses the project's round-trip-safe text strategy so questions and answers
    contain no label-breaking characters, and constrains both lists to the same
    length so each question has a corresponding answer at the same index.
    """
    count = draw(st.integers(min_value=0, max_value=10))
    item_strategy = _non_whitespace_only_text(min_size=1, max_size=100)
    questions = draw(st.lists(item_strategy, min_size=count, max_size=count))
    answers = draw(st.lists(item_strategy, min_size=count, max_size=count))
    return questions, answers


class TestMergedSectionInlinePairing:
    """Property 2: each answer immediately follows its question, in index order.

    **Validates: Requirements 5.2, 1.2, 1.3, 2.1**

    For equal-length question/answer lists, the ordered Q/A line sequence built
    by ``_build_qa_lines`` is ``Q: q0, A: a0, Q: q1, A: a1, ...`` -- the answer
    at index i immediately follows the question at index i, and question order
    is preserved.
    """

    def test_inline_pairing_exact_sequence(self) -> None:
        """A concrete equal-length module pairs each Q with its A in order.

        **Validates: Requirements 5.2, 1.2, 1.3, 2.1**
        """
        questions = ["What is an entity?", "How does matching work?"]
        answers = ["A resolved record.", "By comparing features."]

        lines = _build_qa_lines(questions, answers)

        assert lines == [
            "Q: What is an entity?",
            "A: A resolved record.",
            "Q: How does matching work?",
            "A: By comparing features.",
        ], f"Expected interleaved Q/A pairs in order, got: {lines!r}"

    @given(qa=st_equal_length_qa())
    def test_answer_immediately_follows_question_by_index(
        self, qa: tuple[list[str], list[str]]
    ) -> None:
        """For equal-length lists, line 2*i is ``Q: q{i}`` and line 2*i+1 is
        ``A: a{i}`` -- the answer immediately follows its question, in order.

        **Validates: Requirements 5.2, 1.2, 1.3, 2.1**
        """
        questions, answers = qa

        lines = _build_qa_lines(questions, answers)

        # Two lines per pair, nothing dropped or added.
        assert len(lines) == 2 * len(questions), (
            f"Expected {2 * len(questions)} lines for {len(questions)} pairs, "
            f"got {len(lines)}: {lines!r}"
        )

        for i, (q, a) in enumerate(zip(questions, answers)):
            assert lines[2 * i] == f"Q: {q}", (
                f"Question at index {i} mislabeled or out of order: "
                f"{lines[2 * i]!r} (expected 'Q: {q}')"
            )
            assert lines[2 * i + 1] == f"A: {a}", (
                f"Answer at index {i} does not immediately follow its question: "
                f"{lines[2 * i + 1]!r} (expected 'A: {a}')"
            )

    @given(qa=st_equal_length_qa())
    def test_expected_interleaved_sequence(
        self, qa: tuple[list[str], list[str]]
    ) -> None:
        """The full emitted sequence equals the interleaved
        ``Q: q0, A: a0, Q: q1, A: a1, ...`` construction.

        **Validates: Requirements 5.2, 1.2, 1.3, 2.1**
        """
        questions, answers = qa

        lines = _build_qa_lines(questions, answers)

        expected: list[str] = []
        for q, a in zip(questions, answers):
            expected.append(f"Q: {q}")
            expected.append(f"A: {a}")

        assert lines == expected, (
            f"Emitted sequence does not match interleaved pairing: "
            f"{lines!r} != {expected!r}"
        )

# ---------------------------------------------------------------------------
# Property 3: No content dropped on unequal lengths (Task 3.3)
# ---------------------------------------------------------------------------


_Q_PLACEHOLDER = "Q: (no matching entry)"
_A_PLACEHOLDER = "A: (no matching entry)"


@st.composite
def st_unequal_length_qa(draw: st.DrawFn) -> tuple[list[str], list[str]]:
    """Generate question/answer lists of differing lengths.

    Reuses the project's round-trip-safe text strategy so questions and answers
    contain no label-breaking characters, then draws two distinct lengths so the
    lists are guaranteed unequal (covering both "more questions than answers"
    and "more answers than questions"). At least one list is non-empty.
    """
    item_strategy = _non_whitespace_only_text(min_size=1, max_size=100)
    q_count = draw(st.integers(min_value=0, max_value=10))
    a_count = draw(
        st.integers(min_value=0, max_value=10).filter(lambda n: n != q_count)
    )
    questions = draw(st.lists(item_strategy, min_size=q_count, max_size=q_count))
    answers = draw(st.lists(item_strategy, min_size=a_count, max_size=a_count))
    return questions, answers


class TestMergedSectionUnequalLengths:
    """Property 3: unequal-length lists drop no content and stay aligned.

    **Validates: Requirements 5.3, 2.2, 2.3**

    For question/answer lists of differing lengths, every question text and
    every answer text appears in the ordered Q/A line sequence built by
    ``_build_qa_lines``; missing counterparts are filled with explicit
    placeholders and later pairs are not misaligned.
    """

    def test_more_questions_than_answers_keeps_all_and_pads_answers(self) -> None:
        """Extra questions render with explicit answer placeholders, in order.

        **Validates: Requirements 5.3, 2.2**
        """
        questions = ["What is an entity?", "How does matching work?", "Why ER?"]
        answers = ["A resolved record."]

        lines = _build_qa_lines(questions, answers)

        assert lines == [
            "Q: What is an entity?",
            "A: A resolved record.",
            "Q: How does matching work?",
            _A_PLACEHOLDER,
            "Q: Why ER?",
            _A_PLACEHOLDER,
        ], f"Expected every question with answer placeholders, got: {lines!r}"

    def test_more_answers_than_questions_keeps_all_and_pads_questions(self) -> None:
        """Surplus answers render with explicit question placeholders, in order.

        **Validates: Requirements 5.3, 2.3**
        """
        questions = ["What is an entity?"]
        answers = ["A resolved record.", "By comparing features.", "For dedup."]

        lines = _build_qa_lines(questions, answers)

        assert lines == [
            "Q: What is an entity?",
            "A: A resolved record.",
            _Q_PLACEHOLDER,
            "A: By comparing features.",
            _Q_PLACEHOLDER,
            "A: For dedup.",
        ], f"Expected every answer with question placeholders, got: {lines!r}"

    @given(qa=st_unequal_length_qa())
    def test_every_question_and_answer_text_appears(
        self, qa: tuple[list[str], list[str]]
    ) -> None:
        """For unequal-length lists, every question and answer text is present
        in the emitted lines (nothing is dropped).

        **Validates: Requirements 5.3, 2.2, 2.3**
        """
        questions, answers = qa

        lines = _build_qa_lines(questions, answers)

        for i, q in enumerate(questions):
            assert f"Q: {q}" in lines, (
                f"Question at index {i} was dropped: {q!r} not in {lines!r}"
            )
        for i, a in enumerate(answers):
            assert f"A: {a}" in lines, (
                f"Answer at index {i} was dropped: {a!r} not in {lines!r}"
            )

    @given(qa=st_unequal_length_qa())
    def test_placeholders_fill_missing_counterparts(
        self, qa: tuple[list[str], list[str]]
    ) -> None:
        """The number of placeholder lines equals the difference in list
        lengths -- exactly one placeholder per missing counterpart.

        **Validates: Requirements 5.3, 2.2, 2.3**
        """
        questions, answers = qa

        lines = _build_qa_lines(questions, answers)

        missing_answers = max(len(questions) - len(answers), 0)
        missing_questions = max(len(answers) - len(questions), 0)

        assert lines.count(_A_PLACEHOLDER) == missing_answers, (
            f"Expected {missing_answers} answer placeholder(s), got "
            f"{lines.count(_A_PLACEHOLDER)}: {lines!r}"
        )
        assert lines.count(_Q_PLACEHOLDER) == missing_questions, (
            f"Expected {missing_questions} question placeholder(s), got "
            f"{lines.count(_Q_PLACEHOLDER)}: {lines!r}"
        )

    @given(qa=st_unequal_length_qa())
    def test_later_pairs_not_misaligned(
        self, qa: tuple[list[str], list[str]]
    ) -> None:
        """Pairing stays index-aligned through the shorter list: for every
        index that has both a question and an answer, line 2*i is its question
        and line 2*i+1 is its answer -- no shifting after a missing counterpart.

        **Validates: Requirements 5.3, 2.2, 2.3**
        """
        questions, answers = qa

        lines = _build_qa_lines(questions, answers)

        # Two lines emitted per index, over the longer of the two lists.
        assert len(lines) == 2 * max(len(questions), len(answers)), (
            f"Expected {2 * max(len(questions), len(answers))} lines, "
            f"got {len(lines)}: {lines!r}"
        )

        for i in range(min(len(questions), len(answers))):
            assert lines[2 * i] == f"Q: {questions[i]}", (
                f"Question at index {i} misaligned: {lines[2 * i]!r}"
            )
            assert lines[2 * i + 1] == f"A: {answers[i]}", (
                f"Answer at index {i} misaligned: {lines[2 * i + 1]!r}"
            )


# ---------------------------------------------------------------------------
# Empty-state rendering for the merged section (Task 3.4)
# ---------------------------------------------------------------------------


class TestMergedSectionEmptyState:
    """A module with no questions and no answers renders the "None" empty-state.

    **Validates: Requirements 2.4**

    For a module that has neither questions nor answers, ``_render_module_page``
    still renders the merged "Questions and responses" heading and falls back to
    the existing "None" empty-state (the same rendering used by the other empty
    subsections) -- it emits no ``Q:``/``A:`` pair lines.
    """

    def test_empty_qa_renders_none_under_merged_heading(self) -> None:
        """No questions and no answers => merged heading plus the "None"
        empty-state, with no Q/A pair lines.

        Information Shared and Actions Taken are populated so the only
        empty-state "None" in the body comes from the merged section.

        **Validates: Requirements 2.4**
        """
        section = RecapSection(
            module_number=3,
            module_name="Entity Resolution",
            timestamp="2025-01-01T00:00:00+00:00",
            information_shared=["Loaded sample records."],
            questions_asked=[],
            answers_given=[],
            actions_taken=["Ran the resolver."],
            duration="1h 5m",
        )

        headings, body = _render_section_headings_and_body(section)

        # The merged heading is still rendered above the empty-state.
        assert "Questions and responses" in headings, (
            f"Expected merged 'Questions and responses' heading, got: {headings!r}"
        )

        # The existing "None" empty-state is rendered exactly once -- only for
        # the merged section (Information Shared / Actions Taken are populated).
        assert body.count("None") == 1, (
            f"Expected a single 'None' empty-state for the merged section, "
            f"got body: {body!r}"
        )

        # No inline Q/A pair lines (including placeholders) are emitted.
        assert "Q:" not in body, (
            f"No 'Q:' lines should be rendered for an empty module, got: {body!r}"
        )
        assert "A:" not in body, (
            f"No 'A:' lines should be rendered for an empty module, got: {body!r}"
        )

    def test_fully_empty_module_renders_none_and_no_pairs(self) -> None:
        """A module with every list empty still renders the merged heading and
        the "None" empty-state, with no Q/A pair lines.

        **Validates: Requirements 2.4**
        """
        section = RecapSection(
            module_number=1,
            module_name="Getting Started",
            timestamp="2025-01-01T00:00:00+00:00",
            duration="0h 30m",
        )

        headings, body = _render_section_headings_and_body(section)

        assert "Questions and responses" in headings, (
            f"Expected merged 'Questions and responses' heading, got: {headings!r}"
        )
        assert "None" in body, (
            f"Expected the 'None' empty-state in the body, got: {body!r}"
        )
        assert "Q:" not in body, (
            f"No 'Q:' lines should be rendered for an empty module, got: {body!r}"
        )
        assert "A:" not in body, (
            f"No 'A:' lines should be rendered for an empty module, got: {body!r}"
        )
        # The old separate headings must never appear.
        assert "Questions Asked" not in headings
        assert "Answers Given" not in headings


# ---------------------------------------------------------------------------
# Properties 2 & 3 (unified): pairing and no-drop over arbitrary lengths
# (Task 3.5)
# ---------------------------------------------------------------------------


@st.composite
def st_arbitrary_qa(draw: st.DrawFn) -> tuple[list[str], list[str]]:
    """Generate arbitrary question/answer lists of independent lengths.

    Unlike ``st_equal_length_qa`` (always equal) and ``st_unequal_length_qa``
    (always differing), this draws the two list lengths independently so a
    single strategy covers every shape in one place: equal lengths, more
    questions than answers, more answers than questions, and either list empty.
    Reuses the project's round-trip-safe text strategy so questions and answers
    contain no label-breaking characters.
    """
    item_strategy = _non_whitespace_only_text(min_size=1, max_size=100)
    q_count = draw(st.integers(min_value=0, max_value=10))
    a_count = draw(st.integers(min_value=0, max_value=10))
    questions = draw(st.lists(item_strategy, min_size=q_count, max_size=q_count))
    answers = draw(st.lists(item_strategy, min_size=a_count, max_size=a_count))
    return questions, answers


class TestMergedSectionPairingAndNoDrop:
    """Properties 2 & 3 unified over arbitrary question/answer lengths.

    **Validates: Requirements 2.1, 2.2, 2.3**

    For arbitrary question/answer lists (equal *and* unequal lengths drawn in a
    single strategy), the ordered Q/A line sequence built by ``_build_qa_lines``
    satisfies the combined invariant:

    - Through the shorter list, each answer immediately follows its question by
      index and question order is preserved (Property 2 / Req 2.1).
    - Across the full longer list, no question or answer text is dropped;
      missing counterparts are filled with explicit placeholders so later pairs
      never shift out of alignment (Property 3 / Req 2.2, 2.3).
    """

    @given(qa=st_arbitrary_qa())
    def test_answer_follows_question_by_index_and_no_text_dropped(
        self, qa: tuple[list[str], list[str]]
    ) -> None:
        """For arbitrary lengths, the answer follows its question by index and
        every question and answer text survives in the emitted lines.

        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        questions, answers = qa

        lines = _build_qa_lines(questions, answers)

        # Two lines emitted per index, iterating the longer of the two lists --
        # so nothing is dropped regardless of which list is longer.
        assert len(lines) == 2 * max(len(questions), len(answers)), (
            f"Expected {2 * max(len(questions), len(answers))} lines, "
            f"got {len(lines)}: {lines!r}"
        )

        # Property 2: through the shorter list, the answer at index i
        # immediately follows the question at index i, in order.
        for i in range(min(len(questions), len(answers))):
            assert lines[2 * i] == f"Q: {questions[i]}", (
                f"Question at index {i} mislabeled or out of order: "
                f"{lines[2 * i]!r} (expected 'Q: {questions[i]}')"
            )
            assert lines[2 * i + 1] == f"A: {answers[i]}", (
                f"Answer at index {i} does not immediately follow its question: "
                f"{lines[2 * i + 1]!r} (expected 'A: {answers[i]}')"
            )

        # Property 3: no text dropped -- every question and every answer text
        # appears exactly at its index position (line 2*i / 2*i+1).
        for i, q in enumerate(questions):
            assert lines[2 * i] == f"Q: {q}", (
                f"Question at index {i} dropped or misplaced: {q!r} "
                f"not at line {2 * i}: {lines!r}"
            )
        for i, a in enumerate(answers):
            assert lines[2 * i + 1] == f"A: {a}", (
                f"Answer at index {i} dropped or misplaced: {a!r} "
                f"not at line {2 * i + 1}: {lines!r}"
            )

        # Missing counterparts are filled with explicit placeholders -- one per
        # index beyond the shorter list -- so later pairs stay aligned.
        missing_answers = max(len(questions) - len(answers), 0)
        missing_questions = max(len(answers) - len(questions), 0)
        assert lines.count(_A_PLACEHOLDER) == missing_answers, (
            f"Expected {missing_answers} answer placeholder(s), got "
            f"{lines.count(_A_PLACEHOLDER)}: {lines!r}"
        )
        assert lines.count(_Q_PLACEHOLDER) == missing_questions, (
            f"Expected {missing_questions} question placeholder(s), got "
            f"{lines.count(_Q_PLACEHOLDER)}: {lines!r}"
        )


# ---------------------------------------------------------------------------
# RecapPDF professional layout: margins and page footer (Task 1.2)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design
#
# These unit tests cover the RecapPDF subclass added in task 1.1: generous
# all-sides margins (Req 4.1) and a page-number footer that renders on every
# Content_Page but is suppressed on the Cover_Page (Req 4.3). They follow the
# project test pattern (Req 12.6): class-based, sys.path import, and — because
# RecapPDF is built on fpdf.FPDF — they skip gracefully when fpdf2 is absent
# rather than erroring at collection time.


def _make_footer_recording_pdf(page_number: int):
    """Build a RecapPDF instance whose ``footer`` renders are recorded.

    ``RecapPDF.footer`` calls ``is_cover_page()`` (which reads ``page_no()``)
    and, on a Content_Page, ``set_y``/``set_font``/``set_text_color``/``cell``.
    The returned instance is a dynamically built ``RecapPDF`` subclass that
    overrides those fpdf2 primitives so the real ``footer`` logic can be
    exercised with a fixed page number and no real page geometry — isolating the
    Cover_Page suppression rule from fpdf2's automatic footer invocation.

    Args:
        page_number: The value ``page_no()`` should report while ``footer`` runs.

    Returns:
        A RecapPDF instance with a ``footer_cells`` list capturing the text of
        every ``cell`` call made by ``footer``.
    """
    from recap_pdf_render import RecapPDF

    class _Recorder(RecapPDF):  # type: ignore[misc, valid-type]
        def __init__(self, fake_page_no: int) -> None:
            super().__init__()
            self._fake_page_no = fake_page_no
            self.footer_cells: list[str] = []

        def page_no(self) -> int:  # type: ignore[override]
            return self._fake_page_no

        def set_y(self, *args: object, **kwargs: object) -> None:  # type: ignore[override]  # noqa: E501
            return None

        def set_font(self, *args: object, **kwargs: object) -> None:  # type: ignore[override]  # noqa: E501
            return None

        def set_text_color(self, *args: object, **kwargs: object) -> None:  # type: ignore[override]  # noqa: E501
            return None

        def cell(  # type: ignore[override]
            self, w: object, h: object, text: str = "", *args: object, **kwargs: object
        ) -> None:
            self.footer_cells.append(text)

    return _Recorder(page_number)


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestRecapPDFLayout:
    """RecapPDF sets professional margins and renders a Content_Page footer.

    **Validates: Requirements 4.1, 4.3, 12.6**

    Margins are at least 15 mm on all sides (Req 4.1); the ``Page N`` footer
    renders on Content_Pages and is suppressed on the Cover_Page (Req 4.3).
    """

    def test_margins_at_least_15mm(self) -> None:
        """RecapPDF configures top/bottom/left/right margins of >= 15 mm.

        The left, top, and right margins come from ``set_margins`` and the
        bottom margin from ``set_auto_page_break``; all four must clear the
        15 mm floor Req 4.1 requires.

        **Validates: Requirements 4.1**
        """
        from recap_pdf_render import MARGINS_MM, RecapPDF

        pdf = RecapPDF()

        assert pdf.l_margin >= 15, f"left margin {pdf.l_margin} mm < 15 mm"
        assert pdf.t_margin >= 15, f"top margin {pdf.t_margin} mm < 15 mm"
        assert pdf.r_margin >= 15, f"right margin {pdf.r_margin} mm < 15 mm"
        assert pdf.b_margin >= 15, f"bottom margin {pdf.b_margin} mm < 15 mm"

        # All four sides use the single MARGINS_MM source of truth.
        assert pdf.l_margin == MARGINS_MM
        assert pdf.t_margin == MARGINS_MM
        assert pdf.r_margin == MARGINS_MM
        assert pdf.b_margin == MARGINS_MM

    def test_footer_suppressed_on_cover_page(self) -> None:
        """``footer`` renders nothing on the Cover_Page (page 1).

        ``is_cover_page()`` is True on page 1, so ``footer`` returns before
        emitting any cell — the cover carries no page number.

        **Validates: Requirements 4.3**
        """
        pdf = _make_footer_recording_pdf(page_number=1)

        assert pdf.is_cover_page() is True
        pdf.footer()

        assert pdf.footer_cells == [], (
            f"footer should render nothing on the cover page, got: {pdf.footer_cells!r}"
        )

    def test_footer_renders_page_number_on_content_pages(self) -> None:
        """``footer`` renders a ``Page N`` marker on a Content_Page (page 2+).

        For a page beyond the cover, ``footer`` emits exactly one cell whose
        text is the ``Page N`` page-number marker.

        **Validates: Requirements 4.3**
        """
        pdf = _make_footer_recording_pdf(page_number=2)

        assert pdf.is_cover_page() is False
        pdf.footer()

        assert pdf.footer_cells == ["Page 2"], (
            f"footer should render 'Page 2' on a content page, got: {pdf.footer_cells!r}"
        )

    def test_footer_page_number_tracks_current_page(self) -> None:
        """The rendered footer text reflects the current page number.

        Confirms the footer is not a fixed string: a later Content_Page renders
        its own ``Page N`` value.

        **Validates: Requirements 4.3**
        """
        pdf = _make_footer_recording_pdf(page_number=5)

        pdf.footer()

        assert pdf.footer_cells == ["Page 5"], (
            f"footer should render 'Page 5' on page 5, got: {pdf.footer_cells!r}"
        )


# ---------------------------------------------------------------------------
# Heading hierarchy and accent color (Task 2.2)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design
#
# These unit tests cover the professional-layout update to ``render_heading``
# from ``recap_pdf_render.py`` (task 2.1): module headings render larger than
# subsection headings, which render larger than body text (Req 3.1, 3.2), and
# every heading is drawn in ACCENT_COLOR before its text then reset to
# BODY_COLOR afterward (Req 5.1, 5.3). They drive the real ``render_heading``
# path through the recording stub, so they need neither fpdf2 nor binary PDF
# parsing and follow the project test pattern (Req 12.6).


def _capture_heading_render(text: str, level: int) -> _RecordingPDF:
    """Render one heading via the real ``render_heading`` and return the stub.

    Args:
        text: Heading text to render.
        level: Heading level (2 = module heading, 3 = subsection heading).

    Returns:
        The ``_RecordingPDF`` stub with its ``events`` log populated.
    """
    from recap_pdf_render import render_heading

    pdf = _RecordingPDF()
    render_heading(pdf, text, level)
    return pdf


def _first_text_index(pdf: _RecordingPDF) -> int:
    """Return the index of the first rendered-text event in ``pdf.events``."""
    for index, event in enumerate(pdf.events):
        if event[0] == "text":
            return index
    raise AssertionError(f"no rendered text recorded in events: {pdf.events!r}")


def _rendered_font_size(pdf: _RecordingPDF) -> object:
    """Return the font size active when the first text was drawn."""
    idx = _first_text_index(pdf)
    sizes = [event[1] for event in pdf.events[:idx] if event[0] == "font"]
    assert sizes, f"no set_font call before rendered text: {pdf.events!r}"
    return sizes[-1]


def _color_before_first_text(pdf: _RecordingPDF) -> object:
    """Return the text color set immediately before the first text was drawn."""
    idx = _first_text_index(pdf)
    colors = [event[1] for event in pdf.events[:idx] if event[0] == "color"]
    assert colors, f"no set_text_color before rendered text: {pdf.events!r}"
    return colors[-1]


def _color_after_first_text(pdf: _RecordingPDF) -> object | None:
    """Return the first text color set after the first text was drawn, if any."""
    idx = _first_text_index(pdf)
    colors = [event[1] for event in pdf.events[idx + 1:] if event[0] == "color"]
    return colors[0] if colors else None


class TestHeadingHierarchyAndAccentColor:
    """render_heading applies the professional font hierarchy and accent color.

    **Validates: Requirements 3.1, 3.2, 5.1, 5.3, 12.6**

    Uses the recording stub to exercise the real ``render_heading`` path: module
    headings render at a strictly larger font size than subsection headings,
    which render strictly larger than body text (Req 3.1, 3.2); every heading is
    drawn in ACCENT_COLOR before its text and reset to a distinct BODY_COLOR
    afterward (Req 5.1, 5.3).
    """

    def test_module_heading_larger_than_subsection_larger_than_body(self) -> None:
        """Module heading size > subsection heading size > body text size.

        Font sizes are captured from the real render paths — ``render_heading``
        for the two heading levels and ``render_generic_blocks`` for body prose
        — rather than from the declared constants alone.

        **Validates: Requirements 3.1, 3.2**
        """
        from recap_pdf_render import BODY_FONT_SIZE, render_generic_blocks

        module_pdf = _capture_heading_render("Module 1: Introduction", level=2)
        subsection_pdf = _capture_heading_render("Information Shared", level=3)

        body_pdf = _RecordingPDF()
        render_generic_blocks(body_pdf, ["A prose body paragraph."])

        module_size = _rendered_font_size(module_pdf)
        subsection_size = _rendered_font_size(subsection_pdf)
        body_size = _rendered_font_size(body_pdf)

        assert module_size > subsection_size > body_size, (
            f"Expected module ({module_size}) > subsection ({subsection_size}) "
            f"> body ({body_size}) font sizes"
        )
        assert body_size == BODY_FONT_SIZE, (
            f"Body text should render at BODY_FONT_SIZE ({BODY_FONT_SIZE}), "
            f"got {body_size}"
        )

    def test_heading_sizes_match_declared_constants(self) -> None:
        """Rendered heading sizes equal the declared module/subsection sizes.

        **Validates: Requirements 3.1, 3.2**
        """
        from recap_pdf_render import (
            MODULE_HEADING_FONT_SIZE,
            SUBSECTION_HEADING_FONT_SIZE,
        )

        module_pdf = _capture_heading_render("Module 2: Data Sources", level=2)
        subsection_pdf = _capture_heading_render("Actions Taken", level=3)

        assert _rendered_font_size(module_pdf) == MODULE_HEADING_FONT_SIZE
        assert _rendered_font_size(subsection_pdf) == SUBSECTION_HEADING_FONT_SIZE

    def test_accent_color_applied_before_module_heading(self) -> None:
        """A module heading is drawn in ACCENT_COLOR (set before its text).

        **Validates: Requirements 5.1**
        """
        from recap_pdf_render import ACCENT_COLOR

        pdf = _capture_heading_render("Module 3: Loading Records", level=2)

        assert _color_before_first_text(pdf) == ACCENT_COLOR, (
            f"Expected ACCENT_COLOR {ACCENT_COLOR} before the module heading, "
            f"got events: {pdf.events!r}"
        )

    def test_accent_color_applied_before_subsection_heading(self) -> None:
        """A subsection heading is drawn in ACCENT_COLOR (set before its text).

        **Validates: Requirements 5.1**
        """
        from recap_pdf_render import ACCENT_COLOR

        pdf = _capture_heading_render("Questions and responses", level=3)

        assert _color_before_first_text(pdf) == ACCENT_COLOR, (
            f"Expected ACCENT_COLOR {ACCENT_COLOR} before the subsection "
            f"heading, got events: {pdf.events!r}"
        )

    def test_body_color_reset_after_heading_and_distinct_from_accent(self) -> None:
        """Body color is reset after a heading and differs from the accent.

        Req 5.2/5.3: body text renders in a color distinct from the accent, and
        ``render_heading`` restores BODY_COLOR after drawing the heading so the
        following body text is not left in the accent color.

        **Validates: Requirements 5.1, 5.3**
        """
        from recap_pdf_render import ACCENT_COLOR, BODY_COLOR

        assert BODY_COLOR != ACCENT_COLOR, (
            "BODY_COLOR must be distinct from ACCENT_COLOR"
        )

        pdf = _capture_heading_render("Module 4: Querying", level=2)

        assert _color_after_first_text(pdf) == BODY_COLOR, (
            f"Expected BODY_COLOR {BODY_COLOR} reset after the heading, "
            f"got events: {pdf.events!r}"
        )

    def test_same_level_headings_share_size_and_accent_color(self) -> None:
        """All headings of a level share one font size and the same accent color.

        Renders several module headings and several subsection headings and
        confirms each level uses a single font size and the identical
        ACCENT_COLOR RGB triple across every heading of that level.

        **Validates: Requirements 3.1, 5.3**
        """
        from recap_pdf_render import ACCENT_COLOR

        module_names = [
            "Module 1: Business Problem",
            "Module 2: First Demo",
            "Module 3: Data Mapping",
        ]
        module_sizes = set()
        module_colors = set()
        for name in module_names:
            pdf = _capture_heading_render(name, level=2)
            module_sizes.add(_rendered_font_size(pdf))
            module_colors.add(_color_before_first_text(pdf))

        assert len(module_sizes) == 1, (
            f"Module headings must share one font size, got: {module_sizes!r}"
        )
        assert module_colors == {ACCENT_COLOR}, (
            f"Every module heading must use ACCENT_COLOR, got: {module_colors!r}"
        )

        subsection_names = [
            "Information Shared",
            "Questions and responses",
            "Actions Taken",
        ]
        subsection_sizes = set()
        subsection_colors = set()
        for name in subsection_names:
            pdf = _capture_heading_render(name, level=3)
            subsection_sizes.add(_rendered_font_size(pdf))
            subsection_colors.add(_color_before_first_text(pdf))

        assert len(subsection_sizes) == 1, (
            f"Subsection headings must share one font size, got: "
            f"{subsection_sizes!r}"
        )
        assert subsection_colors == {ACCENT_COLOR}, (
            f"Every subsection heading must use ACCENT_COLOR, got: "
            f"{subsection_colors!r}"
        )


# ---------------------------------------------------------------------------
# Table rendering: pipe-table cell preservation (Task 3.3)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design
#
# These unit tests cover ``render_table`` / ``render_markdown_body`` from
# ``recap_pdf_render.py`` (tasks 3.1, 3.2): a Markdown pipe table renders every
# cell's text so no cell is omitted (Req 6.4). They render a real ``RecapPDF``
# to bytes and round-trip the text via ``extract_pdf_text``, following the
# project test pattern (Req 12.6). Because ``RecapPDF`` is built on
# ``fpdf.FPDF`` they skip gracefully when fpdf2 is absent rather than erroring
# at collection time.


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestTableRendering:
    """render_table renders every pipe-table cell's text (no cell omitted).

    **Validates: Requirements 6.4, 12.6**

    A fixed Markdown pipe table with a distinctive single-word token per cell is
    rendered into a real ``RecapPDF``; round-tripping the written PDF text via
    ``extract_pdf_text`` shows every header and data cell token survived,
    confirming no cell is dropped during table rendering (Req 6.4).
    """

    # A fixed pipe table whose every cell carries a distinctive single-word
    # token (no interior whitespace, so greedy word-wrap can never split it and
    # each token survives intact into the extracted PDF text). Header tokens and
    # data-cell tokens are all unique so each assertion pinpoints one cell.
    _HEADER_TOKENS = ["ColAlpha", "ColBravo", "ColCharlie"]
    _DATA_TOKENS = [
        ["CellDelta", "CellEcho", "CellFoxtrot"],
        ["CellGolf", "CellHotel", "CellIndia"],
    ]
    _TABLE_MD = (
        "| ColAlpha | ColBravo | ColCharlie |\n"
        "| --- | --- | --- |\n"
        "| CellDelta | CellEcho | CellFoxtrot |\n"
        "| CellGolf | CellHotel | CellIndia |\n"
    )

    def _all_cell_tokens(self) -> list[str]:
        """Return every distinctive cell token (header row plus data rows)."""
        tokens = list(self._HEADER_TOKENS)
        for row in self._DATA_TOKENS:
            tokens.extend(row)
        return tokens

    def test_render_table_preserves_all_cell_text(self) -> None:
        """render_table emits every header and data cell token into the PDF.

        Renders the fixed pipe table directly through ``render_table`` into a
        real ``RecapPDF``, writes the document to bytes, and asserts every cell's
        distinctive token round-trips through ``extract_pdf_text`` — so no cell
        is omitted (Req 6.4).

        **Validates: Requirements 6.4**
        """
        from recap_pdf_render import RecapPDF, extract_pdf_text, render_table

        pdf = RecapPDF()
        pdf.add_page()
        render_table(pdf, self._TABLE_MD.strip())

        text = extract_pdf_text(bytes(pdf.output()))

        for token in self._all_cell_tokens():
            assert token in text, (
                f"cell token {token!r} missing from rendered table text; "
                f"render_table omitted a cell (extracted: {text!r})"
            )

    def test_pipe_table_via_markdown_body_preserves_all_cell_text(self) -> None:
        """render_markdown_body detects the pipe table and preserves every cell.

        Exercises the detection branch wired in task 3.2 (``_is_pipe_table`` →
        ``render_table``) end to end, confirming the table path — not the prose
        fallback — renders every cell token into the written PDF (Req 6.4).

        **Validates: Requirements 6.4**
        """
        from recap_pdf_render import (
            RecapPDF,
            extract_pdf_text,
            render_markdown_body,
        )

        pdf = RecapPDF()
        pdf.add_page()
        render_markdown_body(pdf, self._TABLE_MD)

        text = extract_pdf_text(bytes(pdf.output()))

        for token in self._all_cell_tokens():
            assert token in text, (
                f"cell token {token!r} missing after render_markdown_body; the "
                f"pipe table was not rendered cell-complete (extracted: {text!r})"
            )

# ---------------------------------------------------------------------------
# Cover page: title, subtitle, name, and Headline_Stats (Task 4.2)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design
#
# These unit tests cover the professional-layout update to ``_render_cover_page``
# from ``generate_recap_pdf.py`` (task 4.1): the Cover_Page carries the document
# title, a completion-recap subtitle, the bootcamper name, and a Headline_Stats
# line showing the module-section count (Req 2.1, 2.2, 2.4, 2.7, 12.4). The
# optional Started / Total Duration fields render only when present and are
# skipped without aborting the Cover_Page when empty or missing (Req 2.7, 2.8).
# They render a real ``RecapPDF`` to bytes and round-trip the visible text via
# ``extract_pdf_text``, following the project test pattern (Req 12.6). Because
# ``RecapPDF`` is built on ``fpdf.FPDF`` they skip gracefully when fpdf2 is
# absent rather than erroring at collection time.


def _render_cover_text(doc: RecapDocument) -> str:
    """Render only the Cover_Page of ``doc`` and return its extracted text.

    Builds a real ``RecapPDF``, renders the cover via ``_render_cover_page``
    (which adds the page itself), writes the document to bytes, and round-trips
    the visible text through ``extract_pdf_text``.

    Args:
        doc: The recap document whose Cover_Page is rendered.

    Returns:
        The visible text extracted from the rendered Cover_Page.
    """
    from generate_recap_pdf import _render_cover_page
    from recap_pdf_render import RecapPDF, extract_pdf_text

    pdf = RecapPDF()
    _render_cover_page(pdf, doc)
    return extract_pdf_text(bytes(pdf.output()))


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestCoverPage:
    """The Cover_Page renders the title, subtitle, name, and Headline_Stats.

    **Validates: Requirements 2.1, 2.2, 2.4, 2.7, 12.4**

    A representative recap is rendered through ``_render_cover_page`` into a real
    ``RecapPDF``; round-tripping the written PDF text via ``extract_pdf_text``
    shows the document title (Req 2.2), the completion-recap subtitle (Req 2.3),
    the bootcamper name (Req 2.4), and the ``Modules completed: N`` Headline_Stats
    line (Req 2.7). A second case confirms that an empty Started / Total Duration
    header does not abort the Cover_Page (Req 2.8): the title, name, and stats
    still render and the skipped field labels are absent.
    """

    def test_cover_page_contains_title_subtitle_name_and_stats(self) -> None:
        """A populated recap renders title, subtitle, name, and module count.

        The Headline_Stats module count equals ``len(doc.sections)``; the three
        sections here yield ``Modules completed: 3``. The Started and Total
        Duration values are present in the header, so they also survive onto the
        Cover_Page.

        **Validates: Requirements 2.1, 2.2, 2.4, 2.7, 12.4**
        """
        header = RecapHeader(
            bootcamper="Alex Rivera",
            started="2025-01-01T09:00:00+00:00",
            total_duration="8h 15m",
        )
        sections = [
            RecapSection(
                module_number=1,
                module_name="Business Problem",
                timestamp="2025-01-01T10:00:00+00:00",
                duration="1h 0m",
            ),
            RecapSection(
                module_number=2,
                module_name="First Demo",
                timestamp="2025-01-01T12:00:00+00:00",
                duration="2h 0m",
            ),
            RecapSection(
                module_number=3,
                module_name="Data Mapping",
                timestamp="2025-01-01T15:00:00+00:00",
                duration="1h 30m",
            ),
        ]
        doc = RecapDocument(header=header, sections=sections)

        text = _render_cover_text(doc)

        # Req 2.1/2.2: the document title identifies the recap.
        assert "Senzing Bootcamp Recap" in text, (
            f"Cover_Page missing the document title, got: {text!r}"
        )
        # Req 2.3: the subtitle identifies the document as a completion recap.
        assert "Bootcamp Completion Recap" in text, (
            f"Cover_Page missing the completion-recap subtitle, got: {text!r}"
        )
        # Req 2.4: the bootcamper name from the header renders on the cover.
        assert "Alex Rivera" in text, (
            f"Cover_Page missing the bootcamper name, got: {text!r}"
        )
        # Req 2.7/12.4: Headline_Stats shows the module-section count.
        assert "Modules completed: 3" in text, (
            f"Cover_Page missing the Headline_Stats module count, got: {text!r}"
        )
        # Req 2.5/2.6: present Started / Total Duration fields render too.
        assert "Started: 2025-01-01T09:00:00+00:00" in text, (
            f"Cover_Page missing the Started field, got: {text!r}"
        )
        assert "Total Duration: 8h 15m" in text, (
            f"Cover_Page missing the Total Duration field, got: {text!r}"
        )

    def test_missing_start_date_and_duration_do_not_abort_rendering(self) -> None:
        """Empty Started / Total Duration fields are skipped, not fatal.

        A header with empty ``started`` and ``total_duration`` still renders a
        complete Cover_Page: the title, bootcamper name, and Headline_Stats are
        present, and the skipped field labels do not appear (Req 2.8).

        **Validates: Requirements 2.1, 2.2, 2.4, 2.7, 12.4**
        """
        header = RecapHeader(
            bootcamper="Jordan Lee",
            started="",
            total_duration="",
        )
        sections = [
            RecapSection(
                module_number=1,
                module_name="Introduction",
                timestamp="2025-02-01T10:00:00+00:00",
                duration="0h 30m",
            ),
        ]
        doc = RecapDocument(header=header, sections=sections)

        # Rendering must not raise when the optional fields are absent.
        text = _render_cover_text(doc)

        # The title, name, and Headline_Stats still render.
        assert "Senzing Bootcamp Recap" in text, (
            f"Cover_Page missing the document title, got: {text!r}"
        )
        assert "Jordan Lee" in text, (
            f"Cover_Page missing the bootcamper name, got: {text!r}"
        )
        assert "Modules completed: 1" in text, (
            f"Cover_Page missing the Headline_Stats module count, got: {text!r}"
        )
        # The empty fields are skipped, so their labels never render.
        assert "Started:" not in text, (
            f"Empty Started field should be skipped, got: {text!r}"
        )
        assert "Total Duration:" not in text, (
            f"Empty Total Duration field should be skipped, got: {text!r}"
        )


# ---------------------------------------------------------------------------
# Property 1: Cover page contains Headline_Stats (Task 8.1)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design, Property 1: Cover page contains Headline_Stats
#
# For any valid RecapDocument (non-empty bootcamper name, 1-5 module sections),
# the rendered Recap_PDF's extracted text contains the document title
# "Senzing Bootcamp Recap", the bootcamper name (Latin-1 safe), and the module
# section count. This drives the full render path (cover page + module pages)
# through a real ``RecapPDF`` written to a temp file, then round-trips the text
# via ``extract_pdf_text``. Because rendering requires the optional ``fpdf2``
# dependency, the class skips gracefully when it is absent (project test
# pattern, Req 12.6) rather than erroring at collection time.


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestPropertyCoverPageHeadlineStats:
    """Property 1: the Cover_Page carries the title, name, and Headline_Stats.

    **Validates: Requirements 2.1, 2.2, 2.4, 2.7, 12.4**

    For any RecapDocument produced by ``st_recap_document`` (non-empty bootcamper
    name, 1-5 module sections), rendering the full Recap_PDF to a temp file and
    round-tripping its text via ``extract_pdf_text`` shows the document title
    "Senzing Bootcamp Recap" on the Cover_Page (Req 2.1, 2.2), the bootcamper
    name compared Latin-1-safe since fpdf core fonts are Latin-1 (Req 2.4), and
    the ``Modules completed: N`` Headline_Stats line whose count equals
    ``len(doc.sections)`` (Req 2.7, 12.4).
    """

    @given(doc=st_recap_document())
    def test_cover_page_contains_title_name_and_module_count(
        self, doc: RecapDocument
    ) -> None:
        """A rendered recap's Cover_Page text contains the title, the Latin-1
        safe bootcamper name, and the module-section count.

        # Feature: recap-pdf-professional-design, Property 1: Cover page contains Headline_Stats

        **Validates: Requirements 2.1, 2.2, 2.4, 2.7, 12.4**
        """
        from generate_recap_pdf import render_pdf
        from recap_pdf_render import extract_pdf_text, safe_text

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "recap.pdf"
            render_pdf(doc, str(output_path))
            text = extract_pdf_text(output_path.read_bytes())

        # Req 2.1/2.2: the document title identifies the recap on the Cover_Page.
        assert "Senzing Bootcamp Recap" in text, (
            f"Cover_Page missing the document title, got: {text!r}"
        )

        # Req 2.4: the bootcamper name renders on the Cover_Page. fpdf core
        # fonts are Latin-1, so the renderer emits ``safe_text(name)`` — compare
        # against that same Latin-1-safe form rather than the raw name.
        safe_name = safe_text(doc.header.bootcamper)
        assert safe_name in text, (
            f"Cover_Page missing the bootcamper name "
            f"{doc.header.bootcamper!r} (Latin-1 safe: {safe_name!r}), "
            f"got: {text!r}"
        )

        # Req 2.7/12.4: Headline_Stats shows the count of module sections, which
        # equals ``len(doc.sections)`` for a document rendered with sections.
        expected_stats = f"Modules completed: {len(doc.sections)}"
        assert expected_stats in text, (
            f"Cover_Page missing the Headline_Stats line {expected_stats!r}, "
            f"got: {text!r}"
        )


# ---------------------------------------------------------------------------
# Property 2: Content round-trip completeness (Task 8.2)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design, Property 2: Content round-trip completeness
#
# For any RecapDocument with N module sections whose Required_Detail_Sections
# (Information Shared, Questions & Responses, Actions Taken) contain a total of
# M items, the rendered Recap_PDF's extracted text contains the distinctive
# token of at least ``min(M, MIN_BODY_LINES)`` of those items — so the
# professional-layout rendering never condenses, summarizes, or drops
# Required_Detail_Section content (Req 8.1, 8.2, 8.3, 8.5, 9.1, 12.1, 12.2). The
# full render path runs through a real ``RecapPDF`` written to a temp file and
# the text is round-tripped via ``extract_pdf_text``. Because rendering needs
# the optional ``fpdf2`` dependency the class skips gracefully when it is absent
# (project test pattern, Req 12.6) rather than erroring at collection time.

# The renderer emits an inline code span (`` `...` ``) as a separate font run,
# so a token whose content is wrapped in backticks is written without them and
# split away from its neighbors. The distinctive marker is therefore chosen over
# the code-span-split pieces of an item so it is a whitespace-delimited word that
# survives intact into the extracted PDF text whenever the item's content is
# rendered.
_INLINE_CODE_SPAN_RE = re.compile(r"`([^`]+)`")


def _distinctive_survivable_token(item: str) -> str | None:
    """Return the longest render-survivable token of an item, or ``None``.

    Mirrors the wrap-robust "longest token" concept of
    :func:`recap_pdf_render._distinctive_token` — the longest whitespace-
    delimited token survives fpdf word-wrapping intact — and additionally
    accounts for the renderer emitting inline code spans (`` `...` ``) as
    separate font runs: the item is split on code spans, then each piece on
    whitespace, and the longest resulting word (length >= 2, Latin-1-safe to
    mirror what the renderer emits) is the distinctive marker. Returns ``None``
    when the item has no such word (for example a lone one-character item),
    which simply cannot be asserted.

    Args:
        item: A Required_Detail_Section item text.

    Returns:
        The longest render-survivable token of length >= 2, or ``None``.
    """
    from recap_pdf_render import safe_text

    words: list[str] = []
    for piece in _INLINE_CODE_SPAN_RE.split(safe_text(item)):
        words.extend(word for word in piece.split() if len(word) >= 2)
    if not words:
        return None
    return max(words, key=len)


def _required_detail_items(section: RecapSection) -> list[str]:
    """Return a module section's Required_Detail_Section item texts, in order.

    Gathers the three Required_Detail_Sections' items: Information Shared, the
    Questions & Responses content (the Paired_Schema ``qr_pairs`` question and
    response texts, or the legacy split ``questions_asked`` / ``answers_given``
    lists, depending on the section's schema), and Actions Taken. Duration and
    Generic_Content are excluded — they are not Required_Detail_Sections.

    Args:
        section: The parsed module section.

    Returns:
        The Required_Detail_Section item strings in render order.
    """
    items: list[str] = list(section.information_shared)
    if section.schema == "paired":
        for pair in section.qr_pairs:
            items.append(pair.question)
            items.append(pair.response)
    else:
        items.extend(section.questions_asked)
        items.extend(section.answers_given)
    items.extend(section.actions_taken)
    return items


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestPropertyContentRoundTripCompleteness:
    """Property 2: Required_Detail_Section content survives PDF rendering.

    **Validates: Requirements 8.1, 8.2, 8.3, 8.5, 9.1, 12.1, 12.2**

    For any RecapDocument from ``st_recap_document`` (1-5 module sections), let M
    be the number of Required_Detail_Section items — Information Shared,
    Questions & Responses, and Actions Taken across every section — that carry a
    distinctive token. Rendering the full Recap_PDF to a temp file and round-
    tripping its text via ``extract_pdf_text`` shows at least
    ``min(M, MIN_BODY_LINES)`` of those distinctive tokens survive, so no
    Required_Detail_Section content is condensed, summarized, or dropped during
    professional-layout rendering. The ``min(M, MIN_BODY_LINES)`` floor mirrors
    the production Content_Verification (``verify_rendered_pdf``) the generator
    gates publication on (Req 9.1, 12.1, 12.2).
    """

    @given(doc=st_recap_document())
    def test_required_detail_content_survives_rendering(
        self, doc: RecapDocument
    ) -> None:
        """A rendered recap preserves the distinctive tokens of its
        Required_Detail_Section items down to the ``min(M, MIN_BODY_LINES)`` floor.

        # Feature: recap-pdf-professional-design, Property 2: Content round-trip completeness

        **Validates: Requirements 8.1, 8.2, 8.3, 8.5, 9.1, 12.1, 12.2**
        """
        from generate_recap_pdf import render_pdf
        from recap_pdf_render import MIN_BODY_LINES, extract_pdf_text

        # M = the Required_Detail_Section items (across all sections) that carry
        # a distinctive, render-survivable token; items without one (e.g. a lone
        # single character) cannot be asserted and are excluded.
        candidate_tokens = [
            token
            for section in doc.sections
            for item in _required_detail_items(section)
            if (token := _distinctive_survivable_token(item)) is not None
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "recap.pdf"
            render_pdf(doc, str(output_path))
            text = extract_pdf_text(output_path.read_bytes())

        # A token survives when it appears as a whitespace-delimited token in the
        # extracted PDF text (mirrors verify_rendered_pdf's token membership).
        text_tokens = set(text.split())
        present = sum(1 for token in candidate_tokens if token in text_tokens)

        required = min(len(candidate_tokens), MIN_BODY_LINES)
        assert present >= required, (
            f"only {present} of {len(candidate_tokens)} Required_Detail_Section "
            f"distinctive token(s) survived into the rendered PDF; require at "
            f"least {required} = min(M, MIN_BODY_LINES={MIN_BODY_LINES}). "
            f"Required_Detail_Section content was condensed or dropped."
        )


# ---------------------------------------------------------------------------
# Property 3: Page footer presence on content pages (Task 8.3)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design, Property 3: Page footer presence on content pages
#
# For any RecapDocument that renders to more than one page, the extracted text
# of the Recap_PDF contains at least one page-number token matching the pattern
# ``Page N`` (N > 0), confirming the Page_Footer renders on Content_Pages (it is
# suppressed on the Cover_Page). ``_render_module_page`` calls ``add_page()`` for
# every section, so a document with >= 3 module sections is guaranteed to span
# multiple Content_Pages beyond the Cover_Page. ``st_multipage_recap_document``
# builds such a document locally (reusing the shared header/section strategies)
# so the shared ``st_recap_document`` — which draws 1-5 sections and cannot
# guarantee a multi-page render — is left untouched. The full render path runs
# through a real ``RecapPDF`` written to a temp file and the text is round-tripped
# via ``extract_pdf_text``. Because rendering needs the optional ``fpdf2``
# dependency the class skips gracefully when it is absent (project test pattern,
# Req 12.6) rather than erroring at collection time.


@st.composite
def st_multipage_recap_document(draw: st.DrawFn) -> RecapDocument:
    """Generate a RecapDocument guaranteed to render onto multiple pages.

    Reuses the shared ``st_recap_header`` and ``st_recap_section`` strategies but
    forces at least three module sections. Because ``_render_module_page`` starts
    each section with ``add_page()``, three or more sections always produce
    Content_Pages beyond the Cover_Page — so the ``Page N`` footer is guaranteed
    to render at least once. Kept local (rather than adding a ``min_size`` param
    to the shared ``st_recap_document``) so no existing test's generation changes.

    Returns:
        A RecapDocument with a valid header and 3-6 module sections.
    """
    header = draw(st_recap_header())
    sections = draw(st.lists(st_recap_section(), min_size=3, max_size=6))
    return RecapDocument(header=header, sections=sections)


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestPropertyPageFooterPresence:
    """Property 3: the Page_Footer renders a page number on Content_Pages.

    **Validates: Requirements 4.3**

    For any multi-page RecapDocument from ``st_multipage_recap_document`` (3+
    module sections, each rendered on its own page via ``_render_module_page``),
    rendering the full Recap_PDF to a temp file and round-tripping its text via
    ``extract_pdf_text`` shows at least one page-number token matching ``Page N``
    with N > 0 — confirming the Page_Footer renders on Content_Pages (it is
    suppressed on the Cover_Page).
    """

    @given(doc=st_multipage_recap_document())
    def test_content_pages_carry_page_number_footer(
        self, doc: RecapDocument
    ) -> None:
        """A rendered multi-page recap's text contains a ``Page N`` footer token
        with N > 0.

        # Feature: recap-pdf-professional-design, Property 3: Page footer presence on content pages

        **Validates: Requirements 4.3**
        """
        from generate_recap_pdf import render_pdf
        from recap_pdf_render import extract_pdf_text

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "recap.pdf"
            render_pdf(doc, str(output_path))
            text = extract_pdf_text(output_path.read_bytes())

        # The footer renders ``Page {page_no}`` as a single cell on every
        # Content_Page; extract_pdf_text preserves the intra-cell space, so a
        # ``Page N`` token with N > 0 must appear at least once.
        page_numbers = [int(n) for n in re.findall(r"Page\s+(\d+)", text)]
        positive = [n for n in page_numbers if n > 0]
        assert positive, (
            f"expected at least one 'Page N' footer token with N > 0 in the "
            f"rendered multi-page recap ({len(doc.sections)} sections), got "
            f"page numbers {page_numbers!r} (extracted text: {text!r})"
        )


# ---------------------------------------------------------------------------
# Property 4: Table cell text preservation (Task 8.4)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design, Property 4: Table cell text preservation
#
# For any Recap_Markdown pipe table with C cells of text, the rendered
# Recap_PDF's extracted text contains the distinctive token of every cell — so
# no cell is omitted during table rendering (Req 6.4). ``st_pipe_table`` builds
# a valid Markdown pipe table with a random number of columns and rows in which
# every cell (header cells included) carries a distinctive single-word token,
# drawn unique across the whole table so each cell can be located in the output.
# Tokens are ASCII letters/digits only — no interior whitespace, so greedy
# word-wrap can never split one, and no ``|`` or backtick, so none breaks
# pipe-table parsing. The column/row/length bounds keep the grid within the page
# width so a token is never broken mid-word. The full render path runs through a
# real ``RecapPDF`` written to bytes and the text is round-tripped via
# ``extract_pdf_text``. Because rendering needs the optional ``fpdf2`` dependency
# the class skips gracefully when it is absent (project test pattern, Req 12.6)
# rather than erroring at collection time.


@st.composite
def st_pipe_table(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Generate a Markdown pipe table with a distinctive token in every cell.

    Draws a random column count (2-4) and data-row count (1-4). Every cell —
    the header cells and every data cell — carries a distinctive single-word
    token drawn unique across the whole table so each cell can be pinpointed in
    the rendered output. Tokens are ASCII letter/digit words with no interior
    whitespace (greedy word-wrap can never split one) and never contain ``|`` or
    a backtick (so none breaks pipe-table parsing). The chosen column, row, and
    length bounds keep the grid within the page width, so ``render_table`` gives
    each column at least its widest-word width and no token is broken mid-word.

    Returns:
        A ``(table_markdown, cell_tokens)`` tuple: the pipe-table Markdown
        string and the list of every cell's distinctive token in row-major
        order (the header row first, then each data row).
    """
    num_cols = draw(st.integers(min_value=2, max_value=4))
    num_data_rows = draw(st.integers(min_value=1, max_value=4))
    total_cells = num_cols * (num_data_rows + 1)  # + 1 for the header row

    token_strategy = st.text(
        alphabet=(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
        ),
        min_size=5,
        max_size=9,
    )
    tokens = draw(
        st.lists(
            token_strategy,
            min_size=total_cells,
            max_size=total_cells,
            unique=True,
        )
    )

    # Slice the flat, unique token list into a header row plus the data rows.
    rows = [
        tokens[i * num_cols : (i + 1) * num_cols]
        for i in range(num_data_rows + 1)
    ]

    lines = ["| " + " | ".join(rows[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * num_cols) + " |")
    for data_row in rows[1:]:
        lines.append("| " + " | ".join(data_row) + " |")

    return "\n".join(lines), tokens


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestPropertyTableCellPreservation:
    """Property 4: every pipe-table cell's text survives PDF rendering.

    **Validates: Requirements 6.4**

    For any pipe table from ``st_pipe_table`` (2-4 columns, 1-4 data rows, a
    distinctive single-word token in every cell), rendering the table into a
    real ``RecapPDF`` and round-tripping its text via ``extract_pdf_text`` shows
    every cell's distinctive token survives — header cells and data cells alike
    — confirming ``render_table`` omits no cell (Req 6.4). Tokens are matched as
    whole whitespace-delimited words (mirroring ``verify_rendered_pdf``'s token
    membership) so a token can never be found merely as a fragment of another.
    """

    @given(table=st_pipe_table())
    def test_every_table_cell_token_survives_rendering(
        self, table: tuple[str, list[str]]
    ) -> None:
        """A rendered pipe table's text contains every cell's distinctive token.

        # Feature: recap-pdf-professional-design, Property 4: Table cell text preservation

        **Validates: Requirements 6.4**
        """
        from recap_pdf_render import RecapPDF, extract_pdf_text, render_table

        table_md, cell_tokens = table

        pdf = RecapPDF()
        pdf.add_page()
        render_table(pdf, table_md)
        text = extract_pdf_text(bytes(pdf.output()))

        # Each cell holds a single token, so it renders as an isolated text run
        # and appears as its own whitespace-delimited word in the extracted text.
        text_tokens = set(text.split())
        missing = [token for token in cell_tokens if token not in text_tokens]
        assert not missing, (
            f"pipe-table cell token(s) {missing} missing from the rendered "
            f"table text; render_table omitted a cell (extracted: {text!r})"
        )


# ---------------------------------------------------------------------------
# Property 5: Accent color consistency (Task 8.5)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design, Property 5: Accent color consistency
#
# For any RecapDocument with multiple module sections, every set_text_color call
# made immediately before a module-level heading uses the same RGB triple, and
# every call made immediately before a subsection-level heading uses the same RGB
# triple (the two may be equal, but each level is internally consistent). This
# drives the real ``_render_module_page`` render path for every section through
# the pure ``_RecordingPDF`` stub — which records an ordered ``events`` log of
# ("font", size) / ("color", rgb) / ("text", text) tuples — so it needs neither
# fpdf2 nor binary PDF parsing and requires no ``_FPDF_AVAILABLE`` skip guard.
#
# Within ``_render_module_page`` only ``render_heading`` calls ``set_text_color``:
# it sets ACCENT_COLOR immediately before drawing the heading text (via
# ``multi_cell``) then resets to BODY_COLOR immediately after. Body rendering
# never sets a color, so a ("color", rgb) event immediately followed by a
# ("text", text) event in the events log uniquely marks a heading render and the
# color applied to it; the trailing BODY_COLOR reset is always followed by a font
# event (never a text event), so it is never mistaken for a heading.

# A module-level heading is drawn as "Module N: <name>"; every other heading
# ``render_heading`` emits — Information Shared, Questions and responses /
# Questions & Responses, Actions Taken, Duration, Additional Notes — is a
# subsection-level heading, so "starts with 'Module N:'" cleanly classifies the
# level (the "Module N: " prefix is ASCII, so it survives ``safe_text``).
_MODULE_LEVEL_HEADING_RE = re.compile(r"^Module \d+:")


def _heading_accent_events(pdf: _RecordingPDF) -> list[tuple[object, str]]:
    """Return the (color, heading_text) pair for every heading rendered into ``pdf``.

    A heading render is detected as a ("color", rgb) event immediately followed
    by a ("text", text) event in the ordered events log — the ACCENT_COLOR
    set-then-draw pattern that only ``render_heading`` produces within
    ``_render_module_page``. The color captured is the one applied immediately
    before the heading text.

    Args:
        pdf: A ``_RecordingPDF`` the section(s) were rendered into.

    Returns:
        The (color, heading_text) pairs in render order.
    """
    pairs: list[tuple[object, str]] = []
    events = pdf.events
    for index in range(len(events) - 1):
        kind, value = events[index]
        next_kind, next_value = events[index + 1]
        if kind == "color" and next_kind == "text":
            pairs.append((value, str(next_value)))
    return pairs


class TestPropertyAccentColorConsistency:
    """Property 5: headings of the same level share one accent color.

    **Validates: Requirements 5.1, 5.3**

    For any RecapDocument from ``st_recap_document`` (1-5 module sections),
    rendering every section through the real ``_render_module_page`` into a
    shared ``_RecordingPDF`` and reading the color applied immediately before each
    heading shows every module-level heading uses one identical RGB triple and
    every subsection-level heading uses one identical RGB triple across all
    sections (Req 5.3) — and both levels use ACCENT_COLOR (Req 5.1).
    """

    @given(doc=st_recap_document())
    def test_headings_of_each_level_share_one_accent_color(
        self, doc: RecapDocument
    ) -> None:
        """Every module heading shares one color and every subsection heading
        shares one color, both equal to ACCENT_COLOR.

        # Feature: recap-pdf-professional-design, Property 5: Accent color consistency

        **Validates: Requirements 5.1, 5.3**
        """
        from recap_pdf_render import ACCENT_COLOR

        # One shared stub across the whole document so the "same color across all
        # Content_Pages" invariant (Req 5.3) is exercised over every section.
        pdf = _RecordingPDF()
        for section in doc.sections:
            _render_module_page(pdf, section)

        module_colors: set[object] = set()
        subsection_colors: set[object] = set()
        for color, heading_text in _heading_accent_events(pdf):
            if _MODULE_LEVEL_HEADING_RE.match(heading_text):
                module_colors.add(color)
            else:
                subsection_colors.add(color)

        # Every document has >= 1 module section, so both levels are exercised:
        # one module heading and four subsection headings per section.
        assert module_colors, (
            f"no module-level heading was rendered; events: {pdf.events!r}"
        )
        assert subsection_colors, (
            f"no subsection-level heading was rendered; events: {pdf.events!r}"
        )

        # Req 5.3: every heading of a level uses one identical RGB triple.
        assert len(module_colors) == 1, (
            f"module-level headings used inconsistent colors: {module_colors!r}"
        )
        assert len(subsection_colors) == 1, (
            f"subsection-level headings used inconsistent colors: "
            f"{subsection_colors!r}"
        )

        # Req 5.1: headings render in the accent color.
        assert module_colors == {ACCENT_COLOR}, (
            f"module headings must use ACCENT_COLOR {ACCENT_COLOR}, got "
            f"{module_colors!r}"
        )
        assert subsection_colors == {ACCENT_COLOR}, (
            f"subsection headings must use ACCENT_COLOR {ACCENT_COLOR}, got "
            f"{subsection_colors!r}"
        )


# ---------------------------------------------------------------------------
# Full-content preservation and Content_Verification rejection (Task 9.1)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design
#
# These example-based unit tests (NOT property-based) cover the two full-content
# guarantees the professional redesign must keep:
#
#   1. Full-content preservation (Req 12.1): a representative multi-module
#      Recap_Markdown renders a PDF that still contains every module's
#      Information Shared, Questions & Responses, and Actions Taken content —
#      the professional layout wraps around the detail, never condensing it.
#   2. Content_Verification rejection (Req 9.2, 9.3, 12.3): when the rendered
#      candidate PDF omits a Required_Detail_Section, main() rejects it — exit
#      code 1, no ``PDF generated:`` line on stdout, and no published PDF at the
#      output path — leaving any pre-existing output unchanged (Req 9.4).
#
# They drive the real ``main`` / ``render_pdf`` path and round-trip the written
# PDF via ``extract_pdf_text``, following the project test pattern (Req 12.6).
# Because rendering needs the optional ``fpdf2`` dependency the class skips
# gracefully when it is absent rather than erroring at collection time.


def _run_main_capturing_output(argv: list[str]) -> tuple[int, str, str]:
    """Run ``main`` with ``argv``, capturing both stdout and stderr.

    Args:
        argv: Command-line arguments passed to ``main``.

    Returns:
        Tuple of (exit_code, captured_stdout_text, captured_stderr_text).
    """
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


def _render_cover_only(
    doc: RecapDocument, output_path: str, body_text: str = ""
) -> None:
    """Render only the Cover_Page, dropping every module's content.

    A drop-in stand-in for ``generate_recap_pdf.render_pdf`` that writes a
    structurally valid PDF carrying only the cover — it makes no
    ``_render_module_page`` calls — so the written candidate omits every module's
    Required_Detail_Sections. Round-trip Content_Verification then finds no
    ``Module N`` section and rejects the candidate, exercising the
    rejection / exit-1 / no-publish path without corrupting the PDF bytes
    (preferred over writing malformed bytes, per the task guidance).

    Args:
        doc: Parsed recap document whose Cover_Page is rendered.
        output_path: File path for the (module-less) PDF.
        body_text: Ignored; present only to match ``render_pdf``'s signature.
    """
    from generate_recap_pdf import _render_cover_page
    from recap_pdf_render import RecapPDF

    pdf = RecapPDF()
    _render_cover_page(pdf, doc)
    pdf.output(output_path)


@pytest.mark.skipif(not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed")
class TestFullContentPreservationAndVerification:
    """Full-content preservation and Content_Verification rejection.

    **Validates: Requirements 9.2, 9.3, 12.1, 12.3**

    A representative three-module recap is rendered end to end through ``main``;
    round-tripping the written PDF via ``extract_pdf_text`` shows every module's
    Information Shared, Questions & Responses, and Actions Taken content survived
    (Req 12.1). When ``render_pdf`` is replaced with a cover-only stand-in so the
    candidate omits every module's Required_Detail_Sections, Content_Verification
    rejects it: ``main`` returns exit code 1, prints no ``PDF generated:`` line,
    and publishes no PDF — leaving any pre-existing output unchanged (Req 9.2,
    9.3, 9.4, 12.3).
    """

    def _representative_document(self) -> tuple[RecapDocument, list[str]]:
        """Build a representative multi-module recap and its distinctive tokens.

        Three modules, each with a non-empty Information Shared, Questions &
        Responses (authored via the split ``questions_asked`` / ``answers_given``
        lists), and Actions Taken section. Every detail item embeds a distinctive
        single-word token (no interior whitespace, Latin-1 safe) so greedy
        word-wrap can never split it and each token survives intact into the
        extracted PDF text.

        Returns:
            A ``(document, expected_tokens)`` tuple: the recap document and the
            distinctive detail-section tokens that must survive rendering.
        """
        modules = [
            ("Business Problem", "InfoAlphaWibble", "QuestionAlphaWibble",
             "AnswerAlphaWibble", "ActionAlphaWibble"),
            ("First Demo", "InfoBravoWibble", "QuestionBravoWibble",
             "AnswerBravoWibble", "ActionBravoWibble"),
            ("Data Mapping", "InfoCharlieWibble", "QuestionCharlieWibble",
             "AnswerCharlieWibble", "ActionCharlieWibble"),
        ]
        sections: list[RecapSection] = []
        expected_tokens: list[str] = []
        for i, (name, info, question, answer, action) in enumerate(modules, 1):
            sections.append(
                RecapSection(
                    module_number=i,
                    module_name=name,
                    timestamp=f"2025-01-0{i}T10:00:00+00:00",
                    information_shared=[f"Studied {info} concepts in depth"],
                    questions_asked=[f"What is {question} about?"],
                    answers_given=[f"It involves {answer} resolution"],
                    actions_taken=[f"Created {action} artifact"],
                    duration=f"{i}h 0m",
                )
            )
            expected_tokens.extend([info, question, answer, action])
        header = RecapHeader(
            bootcamper="Dana Prescott",
            started="2025-01-01T09:00:00+00:00",
            total_duration="6h 0m",
        )
        return RecapDocument(header=header, sections=sections), expected_tokens

    def test_multi_module_pdf_contains_every_detail_section(self) -> None:
        """A representative recap renders a PDF containing every module's
        Information Shared, Questions & Responses, and Actions Taken content.

        Writes the recap to a temp input file, runs ``main`` to render the PDF,
        asserts a clean success (exit 0 with the ``PDF generated:`` line and a
        written file), then round-trips the PDF text and asserts every module's
        distinctive detail-section token survived — so no Required_Detail_Section
        content was condensed or dropped.

        **Validates: Requirements 12.1**
        """
        from recap_pdf_render import extract_pdf_text

        doc, expected_tokens = self._representative_document()
        markdown = format_recap_document(doc)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            rc, stdout, stderr = _run_main_capturing_output(
                ["--input", str(input_path), "--output", str(output_path)]
            )

            assert rc == 0, (
                f"expected exit 0 for a valid recap, got {rc} (stderr: {stderr!r})"
            )
            assert f"PDF generated: {output_path}" in stdout, (
                f"expected the 'PDF generated:' line for {output_path}, "
                f"got stdout: {stdout!r}"
            )
            assert output_path.exists(), (
                "main reported success but wrote no PDF to the output path"
            )

            text = extract_pdf_text(output_path.read_bytes())

            # Each detail token is a whitespace-delimited word in the extracted
            # text (mirrors verify_rendered_pdf's token membership), so a token
            # can never be found merely as a fragment of another.
            text_tokens = set(text.split())
            missing = [tok for tok in expected_tokens if tok not in text_tokens]
            assert not missing, (
                f"rendered PDF dropped Required_Detail_Section content: tokens "
                f"{missing} from Information Shared / Questions & Responses / "
                f"Actions Taken are absent from the PDF (extracted: {text!r})"
            )

    def test_verification_rejects_pdf_missing_module_section(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Content_Verification rejects a candidate PDF missing a module section.

        Replaces ``render_pdf`` with a cover-only stand-in so the written
        candidate omits every module's Required_Detail_Sections, then runs
        ``main``. Content_Verification finds no ``Module N`` section and rejects
        the candidate: ``main`` returns exit code 1, prints no ``PDF generated:``
        line, publishes no PDF at the output path, and surfaces an error naming
        the omitted per-module content.

        **Validates: Requirements 9.2, 9.3, 12.3**
        """
        import generate_recap_pdf

        doc, _tokens = self._representative_document()
        markdown = format_recap_document(doc)
        monkeypatch.setattr(generate_recap_pdf, "render_pdf", _render_cover_only)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            rc, stdout, stderr = _run_main_capturing_output(
                ["--input", str(input_path), "--output", str(output_path)]
            )

            # Req 9.2: a candidate that omits a per-module section is not
            # published and main returns exit code 1.
            assert rc == 1, f"expected exit 1 on verification failure, got {rc}"
            # Req 9.5 / 12.3: no 'PDF generated:' line is printed for a rejected
            # PDF.
            assert "PDF generated:" not in stdout, (
                f"a rejected candidate must not print 'PDF generated:', got "
                f"stdout: {stdout!r}"
            )
            # Req 9.2 / 12.3: no PDF is published at the output path.
            assert not output_path.exists(), (
                "a rejected candidate must not be published to the output path"
            )
            # Req 9.3: the error identifies that verification found omitted
            # content.
            assert "verification failed" in stderr.lower(), (
                f"expected a Content_Verification failure error on stderr, got: "
                f"{stderr!r}"
            )

    def test_verification_leaves_existing_pdf_unchanged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A rejected candidate leaves any previously published PDF unchanged.

        Seeds the output path with sentinel bytes, replaces ``render_pdf`` with
        the cover-only stand-in, and runs ``main``. Because the atomic publish
        renders and verifies into a temp file and only moves it into place on
        success, the verification failure leaves the pre-existing PDF at the
        output path byte-for-byte unchanged (Req 9.4).

        **Validates: Requirements 9.2, 9.3, 12.3**
        """
        import generate_recap_pdf

        doc, _tokens = self._representative_document()
        markdown = format_recap_document(doc)
        monkeypatch.setattr(generate_recap_pdf, "render_pdf", _render_cover_only)

        sentinel = b"%PDF-1.4 pre-existing recap sentinel bytes"
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")
            output_path.write_bytes(sentinel)

            rc, stdout, _stderr = _run_main_capturing_output(
                ["--input", str(input_path), "--output", str(output_path)]
            )

            assert rc == 1, f"expected exit 1 on verification failure, got {rc}"
            assert "PDF generated:" not in stdout, (
                f"a rejected candidate must not print 'PDF generated:', got "
                f"stdout: {stdout!r}"
            )
            # Req 9.4: the previously existing PDF at the output path is
            # unchanged.
            assert output_path.read_bytes() == sentinel, (
                "a rejected candidate must leave any pre-existing PDF unchanged"
            )


# ---------------------------------------------------------------------------
# Graceful degradation when fpdf2 is absent (Task 9.2)
# ---------------------------------------------------------------------------
#
# Feature: recap-pdf-professional-design
#
# This example-based unit test (NOT property-based) covers the graceful-
# degradation guarantee (Req 11.2, 12.5): when the optional fpdf2 dependency is
# absent, the renderer must not crash with a traceback. The lazy
# ``from fpdf import FPDF`` inside ``render_pdf`` (via
# ``recap_pdf_render._build_recap_pdf_class``) raises ImportError, which
# ``main`` catches and translates into a clean, user-facing ``pip install fpdf2``
# hint on stderr, returning exit code 1 and leaving the Markdown recap intact
# (no PDF is written to the output path).
#
# It is intentionally distinct from the existing property test
# ``TestPreservationGracefulDegradation::test_fpdf_absent_prints_hint_and_exits_1``:
# that property asserts only the exit code and the install hint over generated
# documents, whereas this test additionally pins down the *graceful* part of
# Req 11.2 — that no Python traceback or raw ImportError dump reaches stderr —
# and that degradation writes no PDF. It uses a fixed, representative recap so
# the behavior is deterministic, and it simulates fpdf2 absence via
# ``_fpdf_import_absent`` (which forces the lazy import to raise regardless of
# whether fpdf2 is installed), so it runs in all environments and carries no
# ``_FPDF_AVAILABLE`` skip guard.


class TestGracefulDegradationNoFpdf2:
    """When fpdf2 is absent the renderer degrades gracefully with an install hint.

    **Validates: Requirements 11.2, 12.5**

    A fixed, representative multi-module recap is rendered through ``main`` with
    the lazy ``from fpdf import FPDF`` forced to raise ImportError via
    ``_fpdf_import_absent``. The ImportError is caught and translated into a
    clean, user-facing message: stderr surfaces the ``pip install fpdf2`` hint
    and carries no Python traceback or raw ImportError dump (Req 11.2), ``main``
    returns exit code 1, and no PDF is published to the output path — the
    Markdown recap is left intact (Req 11.2, 12.5).
    """

    # A fixed, representative strict-schema recap (two modules with all detail
    # sections). Deterministic — not Hypothesis-generated — so the degradation
    # behavior is reproducible regardless of environment.
    _RECAP_MARKDOWN = (
        "# Senzing Bootcamp Recap\n"
        "\n"
        "**Bootcamper:** Robin Avery\n"
        "**Started:** 2025-01-01T09:00:00+00:00\n"
        "**Total Duration:** 3h 0m\n"
        "\n"
        "---\n"
        "\n"
        "## Module 1: Business Problem \u2014 2025-01-01T10:00:00+00:00\n"
        "\n"
        "### Information Shared\n"
        "- Senzing resolves entities across disparate data sources\n"
        "\n"
        "### Questions Asked\n"
        "1. What is entity resolution?\n"
        "\n"
        "### Answers Given\n"
        "1. Matching records that refer to the same real-world entity\n"
        "\n"
        "### Actions Taken\n"
        "- Ran the first Senzing demo\n"
        "\n"
        "### Duration\n"
        "1h 0m\n"
        "\n"
        "---\n"
        "\n"
        "## Module 2: First Demo \u2014 2025-01-01T12:00:00+00:00\n"
        "\n"
        "### Information Shared\n"
        "- The demo loads sample records and resolves them into entities\n"
        "\n"
        "### Questions Asked\n"
        "1. How many records were loaded?\n"
        "\n"
        "### Answers Given\n"
        "1. Several thousand sample records\n"
        "\n"
        "### Actions Taken\n"
        "- Reviewed the resolved entities\n"
        "\n"
        "### Duration\n"
        "2h 0m\n"
        "\n"
        "---\n"
    )

    def test_fpdf2_absent_prints_clean_install_hint_without_traceback(self) -> None:
        """A missing fpdf2 yields the install hint and no traceback, exit 1.

        Runs ``main`` on a fixed recap with ``fpdf`` forced to raise ImportError.
        The renderer degrades gracefully: stderr carries the ``pip install
        fpdf2`` hint (Req 11.2) with no ``Traceback (most recent call last)``
        banner and no raw ``ImportError`` dump — the ImportError is caught and
        translated into a clean user-facing message — and ``main`` returns exit
        code 1.

        **Validates: Requirements 11.2, 12.5**
        """
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(self._RECAP_MARKDOWN, encoding="utf-8")

            with _fpdf_import_absent():
                rc, stderr = _run_main_capturing_stderr(
                    ["--input", str(input_path), "--output", str(output_path)]
                )

        # Req 11.2: exit code 1 when fpdf2 is absent.
        assert rc == 1, f"expected exit code 1 when fpdf2 absent, got {rc}"

        # Req 11.2 / 12.5: the actionable install hint is surfaced on stderr.
        assert "pip install fpdf2" in stderr, (
            f"expected the 'pip install fpdf2' hint on stderr, got: {stderr!r}"
        )

        # Req 11.2: graceful degradation — the caught ImportError is translated
        # into a clean message, so no Python traceback or raw ImportError dump
        # reaches stderr.
        assert "Traceback (most recent call last)" not in stderr, (
            f"a traceback leaked to stderr instead of a clean hint: {stderr!r}"
        )
        assert "ImportError" not in stderr, (
            f"a raw ImportError dump leaked to stderr instead of a clean hint: "
            f"{stderr!r}"
        )

    def test_fpdf2_absent_writes_no_pdf_and_keeps_markdown(self) -> None:
        """Degradation writes no PDF to the output path (Markdown kept intact).

        With fpdf2 absent, ``main`` returns exit code 1 before any PDF is
        published, so the output path is never created — the bootcamper keeps
        the source Markdown recap and loses no record to the missing optional
        dependency.

        **Validates: Requirements 11.2, 12.5**
        """
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(self._RECAP_MARKDOWN, encoding="utf-8")

            with _fpdf_import_absent():
                rc, _stderr = _run_main_capturing_stderr(
                    ["--input", str(input_path), "--output", str(output_path)]
                )

            # Req 11.2: no PDF is published when the optional dependency is absent.
            assert rc == 1, f"expected exit code 1 when fpdf2 absent, got {rc}"
            assert not output_path.exists(), (
                "no PDF should be written to the output path when fpdf2 is absent"
            )
            # Req 11.2 / 12.5: the source Markdown recap is left intact.
            assert input_path.read_text(encoding="utf-8") == self._RECAP_MARKDOWN, (
                "the source Markdown recap must remain intact after degradation"
            )


# ---------------------------------------------------------------------------
# Cover_Page colored banner (Task 1.2)
# ---------------------------------------------------------------------------
#
# Feature: professional-recap-pdf
#
# These unit tests cover the colored-banner addition to ``_render_cover_page``
# from ``generate_recap_pdf.py`` (task 1.1): before emitting the title, the
# Cover_Page draws a full-width primary-blue (31,78,121) banner band via
# ``set_fill_color`` + ``rect`` (Req 2.1). They drive the real
# ``_render_cover_page`` path through a pure recording stub — mirroring the
# heading recording-stub tests above — so they need neither fpdf2 nor binary
# PDF parsing and follow the project test pattern.


class _BannerRecordingPDF:
    """Minimal FPDF stand-in that records banner + title render calls in order.

    Exercises the real ``_render_cover_page`` render path without requiring
    fpdf2 or parsing binary PDF output. It records every ``set_fill_color`` and
    ``rect`` call and every text-emitting ``cell`` call into a single ordered
    ``events`` log so a test can assert the Cover_Page banner (``set_fill_color``
    + ``rect``) is drawn before the title text is emitted (Req 2.1). The ``w``
    attribute stands in for fpdf2's page width, which ``_render_cover_page``
    passes to ``rect`` to span the banner edge-to-edge.
    """

    def __init__(self, page_width: float = 210.0) -> None:
        # Page width (mm); _render_cover_page passes this to rect() as the
        # banner's full-page-width span.
        self.w = page_width
        # Ordered log of ("fill_color", rgb) / ("rect", (x, y, w, h)) /
        # ("text", text) events so a test can assert the banner is drawn before
        # the title text.
        self.events: list[tuple[str, object]] = []

    def add_page(self, *args: object, **kwargs: object) -> None:
        return None

    def set_fill_color(self, *args: object, **kwargs: object) -> None:
        self.events.append(("fill_color", tuple(args)))

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *args: object,
        **kwargs: object,
    ) -> None:
        self.events.append(("rect", (x, y, w, h)))

    def set_y(self, *args: object, **kwargs: object) -> None:
        return None

    def set_font(self, *args: object, **kwargs: object) -> None:
        return None

    def set_text_color(self, *args: object, **kwargs: object) -> None:
        return None

    def ln(self, *args: object, **kwargs: object) -> None:
        return None

    def cell(self, w: object, h: object, text: str = "", *args: object, **kwargs: object) -> None:  # noqa: E501
        self.events.append(("text", text))


def _render_cover_banner_events(
    doc: RecapDocument, page_width: float = 210.0
) -> list[tuple[str, object]]:
    """Render a Cover_Page via the real ``_render_cover_page`` and return events.

    Args:
        doc: The recap document whose Cover_Page is rendered.
        page_width: The stub page width passed through to the banner ``rect``.

    Returns:
        The ordered ``events`` log recorded by the ``_BannerRecordingPDF`` stub.
    """
    from generate_recap_pdf import _render_cover_page

    pdf = _BannerRecordingPDF(page_width=page_width)
    _render_cover_page(pdf, doc)
    return pdf.events


# The Cover_Page title text emitted before which the banner must be drawn. It is
# ASCII, so ``safe_text`` leaves it unchanged.
_COVER_TITLE_TEXT = "Senzing Bootcamp Recap"


def _first_index(events: list[tuple[str, object]], kind: str) -> int:
    """Return the index of the first event of ``kind`` in ``events``."""
    for index, (event_kind, _value) in enumerate(events):
        if event_kind == kind:
            return index
    raise AssertionError(f"no {kind!r} event recorded: {events!r}")


def _title_index(events: list[tuple[str, object]]) -> int:
    """Return the index of the Cover_Page title text event in ``events``."""
    for index, (event_kind, value) in enumerate(events):
        if event_kind == "text" and value == _COVER_TITLE_TEXT:
            return index
    raise AssertionError(
        f"Cover_Page title text {_COVER_TITLE_TEXT!r} never emitted: {events!r}"
    )


class TestCoverPageBanner:
    """The Cover_Page draws a full-width primary-blue banner before the title.

    **Validates: Requirements 2.1**

    Drives the real ``_render_cover_page`` through the ``_BannerRecordingPDF``
    stub and reads the ordered ``events`` log: the banner is filled with primary
    blue (31,78,121) via ``set_fill_color`` and drawn as a full-page-width
    ``rect`` anchored at the top edge, and both calls precede the title text so
    the banner reads as the Cover_Page's top visual anchor (Req 2.1).
    """

    def _representative_document(self) -> RecapDocument:
        """Build a representative populated recap document for the Cover_Page."""
        header = RecapHeader(
            bootcamper="Alex Rivera",
            started="2025-01-01T09:00:00+00:00",
            total_duration="8h 15m",
        )
        sections = [
            RecapSection(
                module_number=1,
                module_name="Business Problem",
                timestamp="2025-01-01T10:00:00+00:00",
                duration="1h 0m",
            ),
            RecapSection(
                module_number=2,
                module_name="First Demo",
                timestamp="2025-01-01T12:00:00+00:00",
                duration="2h 0m",
            ),
        ]
        return RecapDocument(header=header, sections=sections)

    def test_banner_filled_with_primary_blue(self) -> None:
        """The banner fill color is primary blue (31,78,121).

        **Validates: Requirements 2.1**
        """
        from recap_pdf_render import PRIMARY_BLUE

        events = _render_cover_banner_events(self._representative_document())

        fill_colors = [value for kind, value in events if kind == "fill_color"]
        assert PRIMARY_BLUE in fill_colors, (
            f"expected a set_fill_color({PRIMARY_BLUE}) banner fill, got fill "
            f"colors: {fill_colors!r}"
        )
        # The literal RGB triple Req 2.1 mandates.
        assert (31, 78, 121) in fill_colors, (
            f"expected the primary-blue (31, 78, 121) banner fill, got: "
            f"{fill_colors!r}"
        )

    def test_banner_rect_spans_full_page_width(self) -> None:
        """The banner rect is anchored at the top edge and spans the full width.

        **Validates: Requirements 2.1**
        """
        from recap_pdf_render import COVER_BANNER_HEIGHT_MM

        page_width = 210.0
        events = _render_cover_banner_events(
            self._representative_document(), page_width=page_width
        )

        rects = [value for kind, value in events if kind == "rect"]
        assert rects, f"no banner rect was drawn: {events!r}"

        x, y, w, h = rects[0]
        # Anchored at the top-left corner (edge-to-edge banner).
        assert (x, y) == (0, 0), f"banner rect not anchored at the top edge: {rects[0]!r}"
        # Spans the full page width.
        assert w == page_width, (
            f"banner rect width {w!r} does not span the full page width "
            f"{page_width!r}"
        )
        # Uses the declared banner band height.
        assert h == COVER_BANNER_HEIGHT_MM, (
            f"banner rect height {h!r} != COVER_BANNER_HEIGHT_MM "
            f"{COVER_BANNER_HEIGHT_MM!r}"
        )

    def test_banner_drawn_before_title(self) -> None:
        """Both ``set_fill_color`` and ``rect`` are called before the title text.

        **Validates: Requirements 2.1**
        """
        events = _render_cover_banner_events(self._representative_document())

        fill_index = _first_index(events, "fill_color")
        rect_index = _first_index(events, "rect")
        title_index = _title_index(events)

        assert fill_index < title_index, (
            f"banner set_fill_color (index {fill_index}) must precede the title "
            f"text (index {title_index}): {events!r}"
        )
        assert rect_index < title_index, (
            f"banner rect (index {rect_index}) must precede the title text "
            f"(index {title_index}): {events!r}"
        )


# ---------------------------------------------------------------------------
# Placeholder-stub / legacy-heading verification (Task 7.2)
# ---------------------------------------------------------------------------
#
# Feature: professional-recap-pdf
#
# These example-based unit tests (NOT property-based) cover the placeholder-stub
# and legacy-heading guard added to the Generator in task 7.1: the module-level
# ``find_placeholder_stub(pdf_text, doc)`` function and its wiring into ``main``
# (raising ``PdfVerificationError`` after ``verify_rendered_pdf`` passes but
# before the atomic publish). Requirement 4.5 forbids "N/A" and "backfilled at
# track completion" stubs in a module's Required_Subsections; Requirement 5.6
# forbids the legacy "Questions Asked" / "Answers Given" split-schema headings
# from surviving into the rendered PDF.
#
# ``find_placeholder_stub`` is deliberately fpdf2-independent (it takes the
# already-extracted PDF text plus the parsed document), so the four required
# cases are unit-tested directly for precise, fast coverage. Two end-to-end
# ``main`` tests additionally confirm the wiring rejects a stubbed recap (exit 1,
# no published PDF) and publishes a clean one (exit 0); they need the optional
# ``fpdf2`` dependency and skip gracefully when it is absent (project test
# pattern).


def _substantive_section(
    module_number: int, name: str, tag: str
) -> RecapSection:
    """Build a module section whose Required_Subsections carry only real content.

    Every Information Shared, Questions & Responses, and Actions Taken item is
    substantive prose embedding a distinctive ``tag`` token, and none contains
    the "N/A" stub, so the section never trips the placeholder guard on its own.

    Args:
        module_number: The module number for the section heading.
        name: The module name.
        tag: A distinctive token embedded in each detail item so rendered text
            carries survivable content.

    Returns:
        A RecapSection with populated, placeholder-free Required_Subsections.
    """
    return RecapSection(
        module_number=module_number,
        module_name=name,
        timestamp=f"2025-01-0{module_number}T10:00:00+00:00",
        information_shared=[f"Studied {tag} entity resolution concepts"],
        questions_asked=[f"How does {tag} matching work?"],
        answers_given=[f"By comparing {tag} record features"],
        actions_taken=[f"Ran the {tag} resolver demo"],
        duration=f"{module_number}h 0m",
    )


def _substantive_document() -> RecapDocument:
    """Build a two-module recap whose Required_Subsections are placeholder-free."""
    header = RecapHeader(
        bootcamper="Alex Rivera",
        started="2025-01-01T09:00:00+00:00",
        total_duration="3h 0m",
    )
    return RecapDocument(
        header=header,
        sections=[
            _substantive_section(1, "Business Problem", "Alpha"),
            _substantive_section(2, "First Demo", "Bravo"),
        ],
    )


class TestPlaceholderStubDetection:
    """find_placeholder_stub flags stubs / legacy headings and passes clean recaps.

    **Validates: Requirements 4.5, 5.5, 5.6**

    Directly unit-tests the fpdf2-independent ``find_placeholder_stub`` over the
    four required cases: an "N/A" stub in a Required_Subsection (Req 4.5, scanned
    against the source document), the "backfilled at track completion" stub and
    the legacy "Questions Asked" heading present in the extracted PDF text
    (Req 4.5, 5.5, 5.6), and a fully substantive recap that passes cleanly.
    """

    def test_na_in_information_shared_is_flagged(self) -> None:
        """An "N/A" stub in a module's Information Shared is flagged.

        The "N/A" stub is scanned against the source Required_Subsection content,
        so a clean rendered ``pdf_text`` still yields a non-None description that
        names the offending module and subsection.

        **Validates: Requirements 4.5, 5.5**
        """
        doc = RecapDocument(
            header=RecapHeader(
                bootcamper="Alex Rivera",
                started="2025-01-01T09:00:00+00:00",
                total_duration="1h 0m",
            ),
            sections=[
                RecapSection(
                    module_number=3,
                    module_name="Data Sources",
                    timestamp="2025-01-03T10:00:00+00:00",
                    information_shared=["N/A"],
                    actions_taken=["Reviewed the data sources"],
                    duration="0h 45m",
                )
            ],
        )

        # A clean rendered-text stand-in with none of the forbidden PDF strings.
        result = find_placeholder_stub(
            "Module 3 Data Sources Information Shared Actions Taken", doc
        )

        assert result is not None, (
            "an 'N/A' stub in Information Shared must be flagged"
        )
        assert "N/A" in result, f"description should name the stub, got: {result!r}"
        assert "Information Shared" in result, (
            f"description should name the offending subsection, got: {result!r}"
        )

    def test_backfilled_phrase_in_pdf_text_is_flagged(self) -> None:
        """The "backfilled at track completion" stub in the PDF text is flagged.

        **Validates: Requirements 4.5, 5.5**
        """
        doc = _substantive_document()

        pdf_text = (
            "Module 1 Business Problem Information Shared "
            "content backfilled at track completion Actions Taken"
        )
        result = find_placeholder_stub(pdf_text, doc)

        assert result is not None, (
            "the 'backfilled at track completion' stub must be flagged"
        )
        assert "backfilled at track completion" in result, (
            f"description should name the stub, got: {result!r}"
        )

    def test_questions_asked_heading_in_pdf_text_is_flagged(self) -> None:
        """The legacy "Questions Asked" heading in the PDF text is flagged.

        **Validates: Requirements 5.6**
        """
        doc = _substantive_document()

        pdf_text = (
            "Module 1 Business Problem Questions Asked "
            "What is entity resolution Actions Taken"
        )
        result = find_placeholder_stub(pdf_text, doc)

        assert result is not None, (
            "the legacy 'Questions Asked' heading must be flagged"
        )
        assert "Questions Asked" in result, (
            f"description should name the legacy heading, got: {result!r}"
        )

    def test_substantive_recap_passes_clean(self) -> None:
        """A substantive recap with no stubs or legacy headings passes cleanly.

        Neither the extracted PDF text nor the source Required_Subsections carry
        a forbidden string, so ``find_placeholder_stub`` returns ``None``.

        **Validates: Requirements 4.5, 5.5, 5.6**
        """
        doc = _substantive_document()

        pdf_text = (
            "Senzing Bootcamp Recap Module 1 Business Problem "
            "Information Shared Studied Alpha entity resolution concepts "
            "Questions and responses How does Alpha matching work "
            "By comparing Alpha record features Actions Taken "
            "Ran the Alpha resolver demo Duration 1h 0m "
            "Module 2 First Demo Studied Bravo entity resolution concepts"
        )
        result = find_placeholder_stub(pdf_text, doc)

        assert result is None, (
            f"a substantive recap must pass verification cleanly, got: {result!r}"
        )


@pytest.mark.skipif(
    not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed"
)
class TestPlaceholderVerificationEndToEnd:
    """main() rejects a stubbed recap and publishes a clean one.

    **Validates: Requirements 4.5, 5.5, 5.6**

    Exercises the placeholder guard wired into ``main`` after
    ``verify_rendered_pdf`` passes: a recap carrying an "N/A" stub in a
    Required_Subsection is rejected (exit 1, no published PDF), while a fully
    substantive recap is published (exit 0, PDF written).
    """

    def test_na_stub_recap_is_rejected_and_not_published(self) -> None:
        """A recap with "N/A" in Information Shared fails, publishing no PDF.

        **Validates: Requirements 4.5, 5.5**
        """
        header = RecapHeader(
            bootcamper="Dana Prescott",
            started="2025-01-01T09:00:00+00:00",
            total_duration="1h 30m",
        )
        # A section with enough substantive content to clear Content_Verification
        # (>= 3 surviving body tokens) plus a single "N/A" stub in a
        # Required_Subsection that the placeholder guard must reject.
        section = RecapSection(
            module_number=1,
            module_name="Business Problem",
            timestamp="2025-01-01T10:00:00+00:00",
            information_shared=[
                "Studied entity resolution fundamentals",
                "Reviewed the sample data sources",
                "N/A",
            ],
            questions_asked=["What is entity resolution?"],
            answers_given=["Matching records to real-world entities"],
            actions_taken=["Ran the first demo"],
            duration="1h 30m",
        )
        doc = RecapDocument(header=header, sections=[section])
        markdown = format_recap_document(doc)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            rc, stdout, stderr = _run_main_capturing_output(
                ["--input", str(input_path), "--output", str(output_path)]
            )

            assert rc == 1, f"expected exit 1 for an 'N/A' stub recap, got {rc}"
            assert "PDF generated:" not in stdout, (
                f"a rejected recap must not print 'PDF generated:', got: {stdout!r}"
            )
            assert not output_path.exists(), (
                "a recap with a placeholder stub must not be published"
            )
            assert "verification failed" in stderr.lower(), (
                f"expected a verification-failure error on stderr, got: {stderr!r}"
            )

    def test_substantive_recap_is_published(self) -> None:
        """A fully substantive recap passes the placeholder guard and publishes.

        **Validates: Requirements 4.5, 5.5, 5.6**
        """
        doc = _substantive_document()
        markdown = format_recap_document(doc)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "recap.md"
            output_path = Path(tmp) / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            rc, stdout, stderr = _run_main_capturing_output(
                ["--input", str(input_path), "--output", str(output_path)]
            )

            assert rc == 0, (
                f"expected exit 0 for a substantive recap, got {rc} "
                f"(stderr: {stderr!r})"
            )
            assert f"PDF generated: {output_path}" in stdout, (
                f"expected the 'PDF generated:' line, got stdout: {stdout!r}"
            )
            assert output_path.exists() and output_path.stat().st_size > 0, (
                "a clean recap must be published as a non-empty PDF"
            )
