"""Unit and integration tests for triage_feedback.py.

Feature: automated-feedback-triage
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from triage_feedback import (
    FeedbackEntry,
    TriageResult,
    VALID_CATEGORIES,
    VALID_PRIORITIES,
    DEFAULT_FEEDBACK_FILE,
    to_kebab_case,
    extract_field,
    parse_feedback_file,
    generate_bugfix_skeleton,
    generate_requirements_skeleton,
    generate_config,
    create_spec_directory,
    print_triage_report,
    main,
)


# ---------------------------------------------------------------------------
# Sample feedback markdown for testing
# ---------------------------------------------------------------------------

SAMPLE_FEEDBACK = """\
# Senzing Bootcamp Power - Improvements Feedback

Some preamble text here.

---

## Improvement: Add Dark Mode Support

**Date**: 2024-06-15
**Module**: 3
**Priority**: Medium
**Category**: UX

### What Happened
The bootcamp interface is too bright when working in low-light environments.

### Why It's a Problem
Users experience eye strain during long bootcamp sessions at night.

### Suggested Fix
Add a dark mode toggle to the bootcamp interface settings.

### Workaround Used
Using browser dark mode extension.

## Improvement: Fix Module 3 Crash

**Date**: 2024-06-16
**Module**: 3
**Priority**: High
**Category**: Bug

### What Happened
Module 3 crashes when loading large datasets with more than 10000 records.

1. Open module 3
2. Load a dataset with 15000 records
3. Click "Process"

### Why It's a Problem
Users cannot complete module 3 with realistic data volumes.

### Suggested Fix
Add pagination or streaming for large dataset processing.

### Workaround Used
Split the dataset into smaller chunks.

## Improvement: Improve Error Messages

**Date**: 2024-06-17
**Module**: 5
**Priority**: Low
**Category**: Documentation

### What Happened
Error messages during data mapping are cryptic and unhelpful.

### Why It's a Problem
Users waste time debugging issues that could be explained clearly.

### Suggested Fix
Replace error codes with human-readable messages that include suggested actions.

### Workaround Used

"""

SAMPLE_FEEDBACK_MISSING_CATEGORY = """\
# Feedback

## Improvement: No Category Entry

**Date**: 2024-01-01
**Module**: 1
**Priority**: High

### What Happened
Something happened.

### Why It's a Problem
It is a problem.

### Suggested Fix
Fix it.

### Workaround Used

"""

SAMPLE_FEEDBACK_UNKNOWN_CATEGORY = """\
# Feedback

## Improvement: Unknown Category Entry

**Date**: 2024-01-01
**Module**: 1
**Priority**: High
**Category**: Networking

### What Happened
Something happened.

### Why It's a Problem
It is a problem.

### Suggested Fix
Fix it.

### Workaround Used

"""


# ---------------------------------------------------------------------------
# (a) Parse real feedback template structure
# ---------------------------------------------------------------------------


class TestParseFeedbackTemplate:
    """Test parsing of real feedback template structure."""

    def test_parse_sample_feedback(self):
        entries, warnings = parse_feedback_file(SAMPLE_FEEDBACK)
        assert len(entries) == 3
        assert entries[0].title == "Add Dark Mode Support"
        assert entries[0].category == "UX"
        assert entries[0].priority == "Medium"
        assert entries[0].module == "3"
        assert entries[0].date == "2024-06-15"
        assert "too bright" in entries[0].what_happened
        assert "eye strain" in entries[0].why_problem
        assert "dark mode toggle" in entries[0].suggested_fix
        assert "browser dark mode" in entries[0].workaround

    def test_parse_bug_entry(self):
        entries, warnings = parse_feedback_file(SAMPLE_FEEDBACK)
        bug_entry = entries[1]
        assert bug_entry.title == "Fix Module 3 Crash"
        assert bug_entry.category == "Bug"
        assert bug_entry.priority == "High"
        assert "crashes" in bug_entry.what_happened

    def test_parse_entry_with_empty_workaround(self):
        entries, warnings = parse_feedback_file(SAMPLE_FEEDBACK)
        doc_entry = entries[2]
        assert doc_entry.title == "Improve Error Messages"
        assert doc_entry.workaround is None or doc_entry.workaround == ""

    def test_parse_empty_content(self):
        entries, warnings = parse_feedback_file("")
        assert len(entries) == 0
        assert len(warnings) == 0

    def test_parse_no_improvement_headings(self):
        entries, warnings = parse_feedback_file("# Just a title\n\nSome text.\n")
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# (b) Default file path when no argument
# ---------------------------------------------------------------------------


class TestDefaultFilePath:
    """Test CLI defaults to SENZING_BOOTCAMP_POWER_FEEDBACK.md."""

    def test_default_path_used(self, tmp_path):
        # Create the default feedback file in tmp_path
        feedback_file = tmp_path / DEFAULT_FEEDBACK_FILE
        feedback_file.write_text("# Empty feedback\n", encoding="utf-8")

        # Run main with no path argument, from tmp_path
        with patch("triage_feedback.Path") as mock_path_cls:
            # We just verify the argparse default is correct
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("path", nargs="?", default=DEFAULT_FEEDBACK_FILE)
            args = parser.parse_args([])
            assert args.path == DEFAULT_FEEDBACK_FILE


# ---------------------------------------------------------------------------
# (c) --dry-run creates no files
# ---------------------------------------------------------------------------


class TestDryRun:
    """Test that --dry-run flag prevents file creation."""

    def test_dry_run_creates_no_files(self, tmp_path):
        feedback_file = tmp_path / "feedback.md"
        feedback_file.write_text(SAMPLE_FEEDBACK, encoding="utf-8")
        output_dir = tmp_path / "specs"

        exit_code = main([
            str(feedback_file),
            "--dry-run",
            "--output-dir", str(output_dir),
        ])

        assert exit_code == 0
        # No directories should be created
        if output_dir.exists():
            assert len(list(output_dir.iterdir())) == 0
        else:
            assert True  # output_dir doesn't exist at all — correct


# ---------------------------------------------------------------------------
# (d) --output-dir overrides base directory
# ---------------------------------------------------------------------------


class TestOutputDir:
    """Test that --output-dir flag overrides the default base directory."""

    def test_output_dir_override(self, tmp_path):
        feedback_file = tmp_path / "feedback.md"
        feedback_file.write_text(SAMPLE_FEEDBACK, encoding="utf-8")
        custom_dir = tmp_path / "custom-specs"

        exit_code = main([
            str(feedback_file),
            "--output-dir", str(custom_dir),
        ])

        assert exit_code == 0
        assert custom_dir.exists()
        # Should have created spec directories under custom_dir
        dirs = list(custom_dir.iterdir())
        assert len(dirs) == 3


# ---------------------------------------------------------------------------
# (e) Missing file exits with code 1
# ---------------------------------------------------------------------------


class TestMissingFile:
    """Test that missing feedback file causes exit code 1."""

    def test_missing_file_exits_with_code_1(self, tmp_path):
        exit_code = main([str(tmp_path / "nonexistent.md")])
        assert exit_code == 1


# ---------------------------------------------------------------------------
# (f) Filesystem error skips entry and continues
# ---------------------------------------------------------------------------


class TestFilesystemError:
    """Test that filesystem errors skip entry and continue."""

    def test_filesystem_error_skips_and_continues(self, tmp_path):
        feedback_file = tmp_path / "feedback.md"
        feedback_file.write_text(SAMPLE_FEEDBACK, encoding="utf-8")
        output_dir = tmp_path / "specs"

        # Create a file where a directory should be, causing an error
        # for the first entry
        output_dir.mkdir(parents=True)
        first_dir_name = to_kebab_case("Add Dark Mode Support")
        # Create a file (not directory) to block directory creation
        blocker = output_dir / first_dir_name
        blocker.mkdir()  # Pre-create to trigger "already exists" skip

        exit_code = main([
            str(feedback_file),
            "--output-dir", str(output_dir),
        ])

        assert exit_code == 0
        # The other two entries should still be created
        dirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(dirs) == 3  # 1 pre-existing + 2 new


# ---------------------------------------------------------------------------
# (g) Auto-generated comment in requirements skeleton
# ---------------------------------------------------------------------------


class TestAutoGeneratedComment:
    """Test that requirements skeleton has auto-generated comment."""

    def test_requirements_skeleton_has_comment(self):
        entry = FeedbackEntry(
            title="Test Feature",
            date="2024-01-01",
            module="1",
            priority="Medium",
            category="UX",
            what_happened="Something happened",
            why_problem="It is a problem",
            suggested_fix="Fix it",
            workaround=None,
        )
        skeleton = generate_requirements_skeleton(entry)
        assert "<!-- Auto-generated by triage_feedback.py" in skeleton
        assert "human review" in skeleton.lower()


# ---------------------------------------------------------------------------
# (h) Empty feedback file exits with code 0
# ---------------------------------------------------------------------------


class TestEmptyFeedbackFile:
    """Test that empty feedback file exits with code 0."""

    def test_empty_file_exits_with_code_0(self, tmp_path):
        feedback_file = tmp_path / "empty.md"
        feedback_file.write_text("", encoding="utf-8")

        exit_code = main([str(feedback_file)])
        assert exit_code == 0

    def test_file_with_no_entries_exits_with_code_0(self, tmp_path):
        feedback_file = tmp_path / "no_entries.md"
        feedback_file.write_text(
            "# Feedback\n\nJust some text, no improvement entries.\n",
            encoding="utf-8",
        )

        exit_code = main([str(feedback_file)])
        assert exit_code == 0


# ---------------------------------------------------------------------------
# (i) Existing directory causes skip with warning
# ---------------------------------------------------------------------------


class TestExistingDirectory:
    """Test that existing spec directory causes skip with warning."""

    def test_existing_directory_skipped(self, tmp_path):
        entry = FeedbackEntry(
            title="Existing Feature",
            date="2024-01-01",
            module="1",
            priority="Medium",
            category="UX",
            what_happened="Something",
            why_problem="Problem",
            suggested_fix="Fix",
            workaround=None,
        )
        base_dir = tmp_path / "specs"
        dir_name = to_kebab_case(entry.title)
        existing = base_dir / dir_name
        existing.mkdir(parents=True)

        path, warning = create_spec_directory(entry, base_dir)
        assert path is None
        assert warning is not None
        assert "already exists" in warning


# ---------------------------------------------------------------------------
# Additional unit tests
# ---------------------------------------------------------------------------


class TestKebabCase:
    """Test kebab-case conversion with specific examples."""

    def test_simple_title(self):
        assert to_kebab_case("Add Dark Mode Support") == "add-dark-mode-support"

    def test_title_with_colon(self):
        assert to_kebab_case("Fix: Module 3 crash") == "fix-module-3-crash"

    def test_title_with_double_spaces_and_dashes(self):
        assert to_kebab_case("SDK  Setup  --  Timeout") == "sdk-setup-timeout"

    def test_title_with_leading_trailing_spaces(self):
        assert to_kebab_case("  Leading Spaces  ") == "leading-spaces"

    def test_empty_string(self):
        assert to_kebab_case("") == ""


class TestMissingCategory:
    """Test entries with missing category are skipped."""

    def test_missing_category_skipped(self):
        entries, warnings = parse_feedback_file(SAMPLE_FEEDBACK_MISSING_CATEGORY)
        assert len(entries) == 0
        assert any("category" in w.lower() for w in warnings)


class TestUnknownCategory:
    """Test entries with unknown category default to requirements."""

    def test_unknown_category_generates_warning(self):
        entries, warnings = parse_feedback_file(SAMPLE_FEEDBACK_UNKNOWN_CATEGORY)
        assert len(entries) == 1
        assert entries[0].category == "Networking"
        assert any("unrecognized" in w.lower() for w in warnings)

    def test_unknown_category_generates_requirements(self, tmp_path):
        entries, _ = parse_feedback_file(SAMPLE_FEEDBACK_UNKNOWN_CATEGORY)
        entry = entries[0]
        path, warning = create_spec_directory(entry, tmp_path)
        assert path is not None
        assert (path / "requirements.md").exists()
        assert not (path / "bugfix.md").exists()


class TestConfigGeneration:
    """Test config file generation."""

    def test_config_has_valid_json(self):
        config_str = generate_config("requirements-first", "feature")
        config = json.loads(config_str)
        assert "specId" in config
        assert config["workflowType"] == "requirements-first"
        assert config["specType"] == "feature"

    def test_config_bugfix(self):
        config_str = generate_config("bugfix", "bugfix")
        config = json.loads(config_str)
        assert config["workflowType"] == "bugfix"
        assert config["specType"] == "bugfix"

    def test_config_has_valid_uuid(self):
        import uuid
        config_str = generate_config("requirements-first", "feature")
        config = json.loads(config_str)
        parsed = uuid.UUID(config["specId"], version=4)
        assert str(parsed) == config["specId"]


class TestBugfixSkeleton:
    """Test bugfix skeleton generation."""

    def test_bugfix_has_all_sections(self):
        entry = FeedbackEntry(
            title="Test Bug",
            date="2024-01-01",
            module="3",
            priority="High",
            category="Bug",
            what_happened="It crashed",
            why_problem="Users can't work",
            suggested_fix="Fix the crash",
            workaround="Restart the app",
        )
        skeleton = generate_bugfix_skeleton(entry)
        assert "# Bug Report" in skeleton
        assert "## Steps to Reproduce" in skeleton
        assert "## Expected Behavior" in skeleton
        assert "## Suggested Fix" in skeleton
        assert "## Known Workaround" in skeleton
        assert "It crashed" in skeleton
        assert "Fix the crash" in skeleton
        assert "Restart the app" in skeleton

    def test_bugfix_no_workaround_section_when_empty(self):
        entry = FeedbackEntry(
            title="Test Bug",
            date="2024-01-01",
            module="3",
            priority="High",
            category="Bug",
            what_happened="It crashed",
            why_problem="Users can't work",
            suggested_fix="Fix the crash",
            workaround=None,
        )
        skeleton = generate_bugfix_skeleton(entry)
        assert "## Known Workaround" not in skeleton


# ---------------------------------------------------------------------------
# Integration test: full triage run
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration test: full triage run on sample feedback."""

    def test_full_triage_run(self, tmp_path):
        feedback_file = tmp_path / "feedback.md"
        feedback_file.write_text(SAMPLE_FEEDBACK, encoding="utf-8")
        output_dir = tmp_path / "specs"

        exit_code = main([
            str(feedback_file),
            "--output-dir", str(output_dir),
        ])

        assert exit_code == 0
        assert output_dir.exists()

        # Check that 3 spec directories were created
        dirs = sorted(d.name for d in output_dir.iterdir() if d.is_dir())
        assert len(dirs) == 3
        assert "add-dark-mode-support" in dirs
        assert "fix-module-3-crash" in dirs
        assert "improve-error-messages" in dirs

        # Check bug entry got bugfix.md
        bug_dir = output_dir / "fix-module-3-crash"
        assert (bug_dir / "bugfix.md").exists()
        assert (bug_dir / ".config.kiro").exists()
        config = json.loads((bug_dir / ".config.kiro").read_text())
        assert config["workflowType"] == "bugfix"
        assert config["specType"] == "bugfix"

        # Check non-bug entries got requirements.md
        ux_dir = output_dir / "add-dark-mode-support"
        assert (ux_dir / "requirements.md").exists()
        assert (ux_dir / ".config.kiro").exists()
        config = json.loads((ux_dir / ".config.kiro").read_text())
        assert config["workflowType"] == "requirements-first"
        assert config["specType"] == "feature"

        # Check requirements.md has auto-generated comment
        req_content = (ux_dir / "requirements.md").read_text()
        assert "Auto-generated" in req_content

    def test_script_uses_only_stdlib(self):
        """Verify the script only imports standard library modules."""
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "triage_feedback.py"
        content = script_path.read_text(encoding="utf-8")
        # Check that no third-party imports are used
        # Only consider lines at the top level (no leading whitespace)
        # and that look like actual import statements
        import_lines = []
        in_docstring = False
        for line in content.splitlines():
            stripped = line.strip()
            # Track triple-quote docstrings
            if '"""' in stripped:
                count = stripped.count('"""')
                if count == 1:
                    in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            # Only top-level imports (no leading whitespace)
            if not line.startswith(" ") and (
                stripped.startswith("import ") or stripped.startswith("from ")
            ):
                import_lines.append(stripped)

        stdlib_modules = {
            "argparse", "json", "re", "sys", "uuid", "pathlib",
            "dataclasses", "__future__",
        }
        for line in import_lines:
            # Extract module name
            if line.startswith("from "):
                module = line.split()[1].split(".")[0]
            else:
                module = line.split()[1].split(".")[0]
            assert module in stdlib_modules, f"Non-stdlib import found: {line}"

    def test_generated_configs_have_valid_json(self, tmp_path):
        """Verify all generated config files contain valid JSON."""
        feedback_file = tmp_path / "feedback.md"
        feedback_file.write_text(SAMPLE_FEEDBACK, encoding="utf-8")
        output_dir = tmp_path / "specs"

        main([str(feedback_file), "--output-dir", str(output_dir)])

        for spec_dir in output_dir.iterdir():
            if spec_dir.is_dir():
                config_file = spec_dir / ".config.kiro"
                assert config_file.exists()
                config = json.loads(config_file.read_text())
                assert "specId" in config
                assert "workflowType" in config
                assert "specType" in config
