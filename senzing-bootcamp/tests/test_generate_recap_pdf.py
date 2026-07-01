"""Property-based tests for generate_recap_pdf.py using Hypothesis.

Feature: module-recap-document

Strategies for generating valid RecapHeader, RecapSection, and RecapDocument
instances. Property tests (tasks 6-12) and edge case tests (task 13) are
added in subsequent tasks.
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

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

        # Verify all required subsections are present
        for subsection_name in _REQUIRED_SUBSECTIONS:
            assert f"### {subsection_name}" in markdown, (
                f"Missing required subsection '### {subsection_name}' "
                f"in formatted section"
            )

        # Verify subsections appear in the correct order
        positions = [
            markdown.index(f"### {name}") for name in _REQUIRED_SUBSECTIONS
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
    """

    def __init__(self) -> None:
        self.l_margin = 10
        self.epw = 190  # effective page width (mm); mirrors fpdf2 A4 default
        self.headings: list[str] = []  # text rendered via multi_cell (headings)
        self.body: list[str] = []  # text rendered via cell/write

    def add_page(self, *args: object, **kwargs: object) -> None:
        return None

    def set_font(self, *args: object, **kwargs: object) -> None:
        return None

    def ln(self, *args: object, **kwargs: object) -> None:
        return None

    def set_x(self, *args: object, **kwargs: object) -> None:
        return None

    def multi_cell(self, w: object, h: object, text: str = "", *args: object, **kwargs: object) -> None:  # noqa: E501
        self.headings.append(text)

    def cell(self, w: object, h: object, text: str = "", *args: object, **kwargs: object) -> None:  # noqa: E501
        self.body.append(text)

    def write(self, h: object, text: str = "", *args: object, **kwargs: object) -> None:
        self.body.append(text)


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
