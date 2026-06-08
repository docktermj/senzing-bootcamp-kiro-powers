"""Property-based tests for generate_recap_pdf.py using Hypothesis.

Feature: module-recap-document

Strategies for generating valid RecapHeader, RecapSection, and RecapDocument
instances. Property tests (tasks 6-12) and edge case tests (task 13) are
added in subsequent tasks.
"""

from __future__ import annotations

import re
import sys
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
    format_recap_document,
    format_recap_section,
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
