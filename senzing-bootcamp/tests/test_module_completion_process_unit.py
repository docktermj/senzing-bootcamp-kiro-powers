"""Unit tests for module completion process: journal and recap creation.

Validates journal file creation, recap header parsing, and journal entry
formatting with specific known values.

Feature: module-completion-process
Requirements: 1.1, 2.1, 3.1
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import pytest  # noqa: E402

from validate_completion_artifacts import (  # noqa: E402
    COMPLETION_STEPS,
    JournalDocument,
    JournalEntry,
    RecapHeader,
    count_recap_sections,
    format_journal_entry,
    format_journal_header,
    parse_journal,
    parse_recap_header,
    validate_journal_consistency,
    validate_journal_structure,
    validate_recap_consistency,
)

# ---------------------------------------------------------------------------
# Tests: Journal Creation (Requirement 1.1)
# ---------------------------------------------------------------------------


class TestJournalCreation:
    """Validate journal header formatting.

    Requirements: 1.1
    """

    def test_format_journal_header_creates_valid_markdown(self) -> None:
        """format_journal_header produces markdown with heading, name, date, and separator."""
        header = format_journal_header("Alice", "2026-05-14")
        assert "# Bootcamp Journal" in header
        assert "**Bootcamper:** Alice" in header
        assert "**Started:** 2026-05-14" in header
        assert "---" in header

    def test_format_journal_header_with_special_characters(self) -> None:
        """format_journal_header handles names with special characters."""
        header = format_journal_header("José O'Brien-Smith", "2026-01-01")
        assert "**Bootcamper:** José O'Brien-Smith" in header
        assert "# Bootcamp Journal" in header
        assert "**Started:** 2026-01-01" in header
        assert "---" in header


# ---------------------------------------------------------------------------
# Tests: Recap Creation (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestRecapCreation:
    """Validate recap header parsing.

    Requirements: 3.1
    """

    def test_parse_recap_header_with_known_values(self) -> None:
        """parse_recap_header extracts correct fields from a well-formed header."""
        content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2026-05-14T09:00:00-05:00\n"
            "**Total Duration:** 2 hours, 15 minutes\n"
            "\n"
            "---\n"
        )
        header = parse_recap_header(content)
        assert isinstance(header, RecapHeader)
        assert header.bootcamper == "Alice"
        assert header.started == "2026-05-14T09:00:00-05:00"
        assert header.total_duration == "2 hours, 15 minutes"

    def test_parse_recap_header_raises_on_empty(self) -> None:
        """parse_recap_header raises ValueError on empty content."""
        with pytest.raises(ValueError, match="empty"):
            parse_recap_header("")

    def test_parse_recap_header_raises_on_missing_fields(self) -> None:
        """parse_recap_header raises ValueError when required fields are missing."""
        # Content with only a heading but no bold fields
        content = "# Senzing Bootcamp Recap\n\nSome text without fields.\n"
        with pytest.raises(ValueError, match="missing"):
            parse_recap_header(content)


# ---------------------------------------------------------------------------
# Tests: Journal Entry Formatting (Requirement 2.1)
# ---------------------------------------------------------------------------


class TestJournalEntryFormatting:
    """Validate journal entry formatting and round-trip parsing.

    Requirements: 2.1
    """

    def test_format_journal_entry_with_known_inputs(self) -> None:
        """format_journal_entry produces expected markdown for known inputs."""
        entry = format_journal_entry(
            module_number=1,
            module_name="Business Problem",
            date="2026-05-14T10:30:00-05:00",
            summary="Defined the business problem",
            artifacts=["docs/business_problem.md", "config/data_sources.yaml"],
            why_it_matters="Establishes the foundation",
            takeaway="N/A",
        )
        assert "## Module 1: Business Problem" in entry
        assert "Completed 2026-05-14T10:30:00-05:00" in entry
        assert "**What we did:** Defined the business problem" in entry
        assert "docs/business_problem.md, config/data_sources.yaml" in entry
        assert "**Why it matters:** Establishes the foundation" in entry
        assert "**Bootcamper's takeaway:** N/A" in entry
        assert "---" in entry

    def test_format_journal_entry_empty_artifacts(self) -> None:
        """format_journal_entry handles an empty artifacts list."""
        entry = format_journal_entry(
            module_number=2,
            module_name="SDK Setup",
            date="2026-05-15T14:00:00-05:00",
            summary="Set up the Senzing SDK",
            artifacts=[],
            why_it_matters="Enables all subsequent modules",
            takeaway="Straightforward setup",
        )
        assert "## Module 2: SDK Setup" in entry
        assert "**What was produced:** " in entry
        # Empty artifacts should produce an empty string after the label
        produced_line = [
            line for line in entry.splitlines() if "**What was produced:**" in line
        ][0]
        assert produced_line.strip() == "**What was produced:**"

    def test_parse_journal_roundtrip(self) -> None:
        """Formatting a header + entry then parsing back recovers the original fields."""
        header = format_journal_header("Bob", "2026-03-01")
        entry_text = format_journal_entry(
            module_number=1,
            module_name="Business Problem",
            date="2026-03-01T09:00:00-06:00",
            summary="Identified the core problem",
            artifacts=["docs/problem.md"],
            why_it_matters="Sets direction for the bootcamp",
            takeaway="Clear problem statement is key",
        )
        full_content = header + entry_text

        doc = parse_journal(full_content)
        assert isinstance(doc, JournalDocument)
        assert doc.bootcamper_name == "Bob"
        assert doc.start_date == "2026-03-01"
        assert len(doc.entries) == 1

        entry = doc.entries[0]
        assert isinstance(entry, JournalEntry)
        assert entry.module_number == 1
        assert entry.module_name == "Business Problem"
        assert entry.completion_date == "2026-03-01T09:00:00-06:00"
        assert entry.summary == "Identified the core problem"
        assert entry.artifacts == ["docs/problem.md"]
        assert entry.why_it_matters == "Sets direction for the bootcamp"
        assert entry.takeaway == "Clear problem statement is key"


# ---------------------------------------------------------------------------
# Tests: Graduation Recovery (Requirements 5.1, 5.2, 5.5)
# ---------------------------------------------------------------------------


class TestGraduationRecovery:
    """Validate graduation recovery scenarios using validation functions.

    Requirements: 5.1, 5.2, 5.5
    """

    def test_recap_validation_passes_when_sections_match_progress(self) -> None:
        """validate_recap_consistency returns no errors when recap modules match progress."""
        errors = validate_recap_consistency([1, 2], [1, 2])
        assert errors == []

    def test_recap_validation_fails_when_progress_has_modules_but_recap_missing(self) -> None:
        """validate_recap_consistency reports errors for modules in progress but missing from recap."""
        errors = validate_recap_consistency([], [1, 2, 3])
        assert len(errors) == 3
        assert any("1" in err for err in errors)
        assert any("2" in err for err in errors)
        assert any("3" in err for err in errors)

    def test_recap_validation_passes_when_progress_empty(self) -> None:
        """validate_recap_consistency returns no errors when both lists are empty."""
        errors = validate_recap_consistency([], [])
        assert errors == []

    def test_count_recap_sections_with_valid_content(self) -> None:
        """count_recap_sections extracts module numbers from recap headings."""
        content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2026-05-14T09:00:00-05:00\n"
            "**Total Duration:** 3 hours\n"
            "\n"
            "---\n"
            "\n"
            "## Module 1: Business Problem\n"
            "\n"
            "Some content here.\n"
            "\n"
            "---\n"
            "\n"
            "## Module 3: System Verification\n"
            "\n"
            "More content here.\n"
            "\n"
            "---\n"
        )
        result = count_recap_sections(content)
        assert result == [1, 3]

    def test_count_recap_sections_empty_content(self) -> None:
        """count_recap_sections returns empty list for empty content."""
        result = count_recap_sections("")
        assert result == []


# ---------------------------------------------------------------------------
# Tests: Error Handling and Edge Cases (Requirements 6.1, 6.2, 3.2, 5.4)
# ---------------------------------------------------------------------------


class TestErrorHandlingAndEdgeCases:
    """Validate error handling, default fallbacks, and validation edge cases.

    Requirements: 6.1, 6.2, 3.2, 5.4
    """

    def test_default_name_fallback_in_journal_header(self) -> None:
        """format_journal_header with 'Bootcamper' produces the default name pattern."""
        header = format_journal_header("Bootcamper", "2026-01-01")
        assert "**Bootcamper:** Bootcamper" in header

    def test_default_name_fallback_in_recap_header_parsing(self) -> None:
        """parse_recap_header extracts 'Bootcamper' as the default name."""
        content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Bootcamper\n"
            "**Started:** 2026-01-01T00:00:00-06:00\n"
            "**Total Duration:** 0 minutes\n"
            "\n"
            "---\n"
        )
        header = parse_recap_header(content)
        assert header.bootcamper == "Bootcamper"

    def test_validate_journal_structure_detects_missing_summary(self) -> None:
        """validate_journal_structure reports error for entry with empty summary."""
        entry = JournalEntry(
            module_number=1,
            module_name="Business Problem",
            completion_date="2026-01-01T10:00:00-06:00",
            summary="",
            artifacts=[],
            why_it_matters="Foundation",
            takeaway="N/A",
        )
        journal = JournalDocument(
            bootcamper_name="Alice",
            start_date="2026-01-01",
            entries=[entry],
        )
        errors = validate_journal_structure(journal)
        assert any("missing summary" in e for e in errors)

    def test_validate_journal_structure_detects_missing_module_name(self) -> None:
        """validate_journal_structure reports error for entry with empty module_name."""
        entry = JournalEntry(
            module_number=2,
            module_name="",
            completion_date="2026-01-02T10:00:00-06:00",
            summary="Did something",
            artifacts=[],
            why_it_matters="Important",
            takeaway="N/A",
        )
        journal = JournalDocument(
            bootcamper_name="Bob",
            start_date="2026-01-01",
            entries=[entry],
        )
        errors = validate_journal_structure(journal)
        assert any("missing module_name" in e for e in errors)

    def test_validate_recap_consistency_detects_missing_sections(self) -> None:
        """validate_recap_consistency reports modules in progress but missing from recap."""
        errors = validate_recap_consistency([1], [1, 2, 3])
        assert any("Module 2" in e for e in errors)
        assert any("Module 3" in e for e in errors)

    def test_validate_journal_consistency_detects_missing_entries(self) -> None:
        """validate_journal_consistency reports modules in progress but missing from journal."""
        errors = validate_journal_consistency([1], [1, 2])
        assert any("Module 2" in e for e in errors)

    def test_completion_steps_constant_has_correct_order(self) -> None:
        """COMPLETION_STEPS contains the five steps in the defined order."""

        assert COMPLETION_STEPS == [
            "progress_update",
            "recap_append",
            "journal_entry",
            "completion_certificate",
            "next_step_options",
        ]
