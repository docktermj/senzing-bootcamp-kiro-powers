"""Integration tests for module completion process.

End-to-end scenarios validating journal and recap creation, sequential
module completions, graduation recap recovery, and CLI validation.

Feature: module-completion-process
Requirements: 1.1, 1.2, 3.1, 3.3, 5.1, 5.2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import pytest  # noqa: E402

from validate_completion_artifacts import (  # noqa: E402
    count_recap_sections,
    format_journal_entry,
    format_journal_header,
    main,
    parse_journal,
    parse_recap_header,
    validate_journal_consistency,
    validate_recap_consistency,
)


# ---------------------------------------------------------------------------
# Tests: Module 1 Completion Flow (Requirements 1.1, 1.2, 3.1)
# ---------------------------------------------------------------------------


class TestModule1CompletionFlow:
    """Verify both journal and recap are created from scratch on first module.

    Requirements: 1.1, 1.2, 3.1
    """

    def test_first_module_creates_journal_from_scratch(self, tmp_path: Path) -> None:
        """Use format_journal_header + format_journal_entry to create a journal,
        then parse it back and verify structure."""
        journal_path = tmp_path / "docs" / "bootcamp_journal.md"
        journal_path.parent.mkdir(parents=True, exist_ok=True)

        # Create journal with header + first entry
        header = format_journal_header("Alice", "2026-05-14")
        entry = format_journal_entry(
            module_number=1,
            module_name="Business Problem",
            date="2026-05-14T10:30:00-05:00",
            summary="Defined the business problem and identified data sources",
            artifacts=["docs/business_problem.md", "config/data_sources.yaml"],
            why_it_matters="Establishes the foundation for all subsequent modules",
            takeaway="N/A",
        )
        journal_path.write_text(header + entry, encoding="utf-8")

        # Parse back and verify structure
        content = journal_path.read_text(encoding="utf-8")
        doc = parse_journal(content)

        assert doc.bootcamper_name == "Alice"
        assert doc.start_date == "2026-05-14"
        assert len(doc.entries) == 1
        assert doc.entries[0].module_number == 1
        assert doc.entries[0].module_name == "Business Problem"
        assert doc.entries[0].completion_date == "2026-05-14T10:30:00-05:00"
        assert doc.entries[0].summary == "Defined the business problem and identified data sources"
        assert doc.entries[0].artifacts == [
            "docs/business_problem.md",
            "config/data_sources.yaml",
        ]
        assert doc.entries[0].why_it_matters == (
            "Establishes the foundation for all subsequent modules"
        )

    def test_first_module_creates_recap_from_scratch(self, tmp_path: Path) -> None:
        """Create a recap file with header + one section, parse header and count sections."""
        recap_path = tmp_path / "docs" / "bootcamp_recap.md"
        recap_path.parent.mkdir(parents=True, exist_ok=True)

        # Create recap with header + one module section
        recap_content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2026-05-14T09:00:00-05:00\n"
            "**Total Duration:** 1 hour, 30 minutes\n"
            "\n"
            "---\n"
            "\n"
            "## Module 1: Business Problem — 2026-05-14T10:30:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- Discussed entity resolution concepts\n"
            "\n"
            "### Questions Asked\n"
            "1. What data sources do we have?\n"
            "\n"
            "### Answers Given\n"
            "1. We have customer and vendor data\n"
            "\n"
            "### Actions Taken\n"
            "- Created business_problem.md\n"
            "\n"
            "### Duration\n"
            "1 hour, 30 minutes\n"
            "\n"
            "---\n"
        )
        recap_path.write_text(recap_content, encoding="utf-8")

        # Parse header and count sections
        content = recap_path.read_text(encoding="utf-8")
        header = parse_recap_header(content)
        sections = count_recap_sections(content)

        assert header.bootcamper == "Alice"
        assert header.started == "2026-05-14T09:00:00-05:00"
        assert header.total_duration == "1 hour, 30 minutes"
        assert len(sections) == 1
        assert sections == [1]


# ---------------------------------------------------------------------------
# Tests: Sequential Module Completions (Requirements 1.2, 3.3)
# ---------------------------------------------------------------------------


class TestSequentialModuleCompletions:
    """Verify cumulative artifacts after completing modules 1, 2, 3.

    Requirements: 1.2, 3.3
    """

    def test_three_modules_produce_cumulative_journal(self, tmp_path: Path) -> None:
        """Create journal with header + 3 entries, parse back, verify 3 entries
        with correct module numbers."""
        journal_path = tmp_path / "docs" / "bootcamp_journal.md"
        journal_path.parent.mkdir(parents=True, exist_ok=True)

        header = format_journal_header("Bob", "2026-06-01")
        entries = [
            format_journal_entry(
                module_number=1,
                module_name="Business Problem",
                date="2026-06-01T10:00:00-05:00",
                summary="Defined the business problem",
                artifacts=["docs/business_problem.md"],
                why_it_matters="Foundation for all modules",
                takeaway="Clear problem statement",
            ),
            format_journal_entry(
                module_number=2,
                module_name="SDK Setup",
                date="2026-06-02T14:00:00-05:00",
                summary="Set up the Senzing SDK",
                artifacts=["config/sdk_config.yaml"],
                why_it_matters="Enables all subsequent modules",
                takeaway="Straightforward setup",
            ),
            format_journal_entry(
                module_number=3,
                module_name="System Verification",
                date="2026-06-03T09:00:00-05:00",
                summary="Verified system configuration",
                artifacts=["docs/verification_report.md"],
                why_it_matters="Confirms environment is ready",
                takeaway="All checks passed",
            ),
        ]
        journal_path.write_text(header + "".join(entries), encoding="utf-8")

        # Parse and verify
        content = journal_path.read_text(encoding="utf-8")
        doc = parse_journal(content)

        assert doc.bootcamper_name == "Bob"
        assert len(doc.entries) == 3
        assert [e.module_number for e in doc.entries] == [1, 2, 3]
        assert doc.entries[0].module_name == "Business Problem"
        assert doc.entries[1].module_name == "SDK Setup"
        assert doc.entries[2].module_name == "System Verification"

    def test_three_modules_produce_cumulative_recap(self, tmp_path: Path) -> None:
        """Create recap with header + 3 module sections, count sections, verify [1, 2, 3]."""
        recap_path = tmp_path / "docs" / "bootcamp_recap.md"
        recap_path.parent.mkdir(parents=True, exist_ok=True)

        recap_content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Bob\n"
            "**Started:** 2026-06-01T09:00:00-05:00\n"
            "**Total Duration:** 6 hours\n"
            "\n"
            "---\n"
            "\n"
            "## Module 1: Business Problem — 2026-06-01T10:00:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- Entity resolution overview\n"
            "\n"
            "### Duration\n"
            "2 hours\n"
            "\n"
            "---\n"
            "\n"
            "## Module 2: SDK Setup — 2026-06-02T14:00:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- SDK installation steps\n"
            "\n"
            "### Duration\n"
            "2 hours\n"
            "\n"
            "---\n"
            "\n"
            "## Module 3: System Verification — 2026-06-03T09:00:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- Verification procedures\n"
            "\n"
            "### Duration\n"
            "2 hours\n"
            "\n"
            "---\n"
        )
        recap_path.write_text(recap_content, encoding="utf-8")

        # Count sections and verify
        content = recap_path.read_text(encoding="utf-8")
        sections = count_recap_sections(content)

        assert sections == [1, 2, 3]
        assert len(sections) == 3


# ---------------------------------------------------------------------------
# Tests: Graduation Recap Recovery (Requirements 5.1, 5.2)
# ---------------------------------------------------------------------------


class TestGraduationRecapRecovery:
    """Verify recap consistency validation for graduation recovery scenarios.

    Requirements: 5.1, 5.2
    """

    def test_graduation_recovery_detects_missing_recap(self) -> None:
        """validate_recap_consistency with empty recap_modules and non-empty
        progress_modules reports errors for each missing module."""
        recap_modules: list[int] = []
        progress_modules = [1, 2, 3, 4, 5]

        errors = validate_recap_consistency(recap_modules, progress_modules)

        assert len(errors) == 5
        for mod in progress_modules:
            assert any(f"Module {mod}" in err for err in errors)

    def test_graduation_recovery_passes_with_valid_recap(self) -> None:
        """validate_recap_consistency with matching modules returns no errors."""
        recap_modules = [1, 2, 3, 4, 5]
        progress_modules = [1, 2, 3, 4, 5]

        errors = validate_recap_consistency(recap_modules, progress_modules)

        assert errors == []


# ---------------------------------------------------------------------------
# Tests: Validation Script CLI (Requirements 5.1, 5.2)
# ---------------------------------------------------------------------------


class TestValidationScriptCLI:
    """End-to-end CLI validation with sample files.

    Requirements: 5.1, 5.2
    """

    def test_cli_passes_with_valid_files(self, tmp_path: Path) -> None:
        """Create valid progress.json, journal.md, and recap.md, run main(),
        verify exit code 0."""
        # Create progress file
        progress_path = tmp_path / "progress.json"
        progress_path.write_text(
            json.dumps({"modules_completed": [1, 2]}),
            encoding="utf-8",
        )

        # Create journal file
        journal_path = tmp_path / "journal.md"
        header = format_journal_header("Alice", "2026-05-14")
        entry1 = format_journal_entry(
            module_number=1,
            module_name="Business Problem",
            date="2026-05-14T10:30:00-05:00",
            summary="Defined the business problem",
            artifacts=["docs/business_problem.md"],
            why_it_matters="Foundation",
            takeaway="N/A",
        )
        entry2 = format_journal_entry(
            module_number=2,
            module_name="SDK Setup",
            date="2026-05-15T14:00:00-05:00",
            summary="Set up the SDK",
            artifacts=["config/sdk.yaml"],
            why_it_matters="Enables modules",
            takeaway="Easy",
        )
        journal_path.write_text(header + entry1 + entry2, encoding="utf-8")

        # Create recap file
        recap_path = tmp_path / "recap.md"
        recap_content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2026-05-14T09:00:00-05:00\n"
            "**Total Duration:** 4 hours\n"
            "\n"
            "---\n"
            "\n"
            "## Module 1: Business Problem — 2026-05-14T10:30:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- Overview\n"
            "\n"
            "---\n"
            "\n"
            "## Module 2: SDK Setup — 2026-05-15T14:00:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- SDK steps\n"
            "\n"
            "---\n"
        )
        recap_path.write_text(recap_content, encoding="utf-8")

        # Run main() and verify exit code 0
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--progress", str(progress_path),
                "--journal", str(journal_path),
                "--recap", str(recap_path),
            ])
        assert exc_info.value.code == 0

    def test_cli_fails_with_missing_progress(self, tmp_path: Path) -> None:
        """Run main() with non-existent progress file, verify exit code 1."""
        journal_path = tmp_path / "journal.md"
        journal_path.write_text(
            format_journal_header("Alice", "2026-05-14"),
            encoding="utf-8",
        )
        recap_path = tmp_path / "recap.md"
        recap_path.write_text(
            "# Senzing Bootcamp Recap\n\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2026-05-14T09:00:00-05:00\n"
            "**Total Duration:** 0 minutes\n\n---\n",
            encoding="utf-8",
        )

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--progress", str(tmp_path / "nonexistent_progress.json"),
                "--journal", str(journal_path),
                "--recap", str(recap_path),
            ])
        assert exc_info.value.code == 1

    def test_cli_fails_with_inconsistent_files(self, tmp_path: Path) -> None:
        """Create progress with modules [1,2,3] but journal with only module 1,
        verify exit code 1."""
        # Progress has 3 modules
        progress_path = tmp_path / "progress.json"
        progress_path.write_text(
            json.dumps({"modules_completed": [1, 2, 3]}),
            encoding="utf-8",
        )

        # Journal only has module 1
        journal_path = tmp_path / "journal.md"
        header = format_journal_header("Alice", "2026-05-14")
        entry1 = format_journal_entry(
            module_number=1,
            module_name="Business Problem",
            date="2026-05-14T10:30:00-05:00",
            summary="Defined the business problem",
            artifacts=["docs/business_problem.md"],
            why_it_matters="Foundation",
            takeaway="N/A",
        )
        journal_path.write_text(header + entry1, encoding="utf-8")

        # Recap has all 3 modules
        recap_path = tmp_path / "recap.md"
        recap_content = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2026-05-14T09:00:00-05:00\n"
            "**Total Duration:** 6 hours\n"
            "\n"
            "---\n"
            "\n"
            "## Module 1: Business Problem — 2026-05-14T10:30:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- Overview\n"
            "\n"
            "---\n"
            "\n"
            "## Module 2: SDK Setup — 2026-05-15T14:00:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- SDK steps\n"
            "\n"
            "---\n"
            "\n"
            "## Module 3: System Verification — 2026-06-01T09:00:00-05:00\n"
            "\n"
            "### Information Shared\n"
            "- Verification\n"
            "\n"
            "---\n"
        )
        recap_path.write_text(recap_content, encoding="utf-8")

        # Run main() — should fail because journal is missing modules 2 and 3
        with pytest.raises(SystemExit) as exc_info:
            main([
                "--progress", str(progress_path),
                "--journal", str(journal_path),
                "--recap", str(recap_path),
            ])
        assert exc_info.value.code == 1
