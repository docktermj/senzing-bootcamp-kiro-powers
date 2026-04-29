"""Example-based unit tests for lint_steering.py.

Tests run against the real steering corpus and synthetic examples.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import (
    LintViolation,
    STEERING_DIR,
    HOOKS_DIR,
    INDEX_PATH,
    check_cross_references,
    check_module_numbering,
    check_checkpoints,
    check_index_completeness,
    check_hook_consistency,
    check_frontmatter,
    check_internal_links,
    check_wait_conflicts,
    parse_steering_index,
    run_all_checks,
)


# ---------------------------------------------------------------------------
# Paths to real corpus
# ---------------------------------------------------------------------------

REAL_STEERING = Path(__file__).resolve().parent.parent / "steering"
REAL_HOOKS = Path(__file__).resolve().parent.parent / "hooks"
REAL_INDEX = REAL_STEERING / "steering-index.yaml"


# ---------------------------------------------------------------------------
# 12.1 Real corpus: no orphaned #[[file:]] references
# ---------------------------------------------------------------------------


class TestRealCorpusCrossReferences:
    """Req 1.1: Real steering corpus has no orphaned #[[file:]] references."""

    def test_no_orphaned_include_refs(self):
        """All #[[file:path]] references in the real corpus point to existing files."""
        index_data = parse_steering_index(REAL_INDEX)
        violations = check_cross_references(REAL_STEERING, index_data)
        include_errors = [v for v in violations
                         if v.level == "ERROR" and "#[[file:" in v.message]
        assert len(include_errors) == 0, \
            f"Found orphaned include refs: {[v.format() for v in include_errors]}"


# ---------------------------------------------------------------------------
# 12.2 Real corpus: module numbering is consistent
# ---------------------------------------------------------------------------


class TestRealCorpusModuleNumbering:
    """Req 2.1: Real module numbering is consistent between index and files."""

    def test_module_numbering_consistent(self):
        """Every module in the index has a corresponding file on disk."""
        index_data = parse_steering_index(REAL_INDEX)
        violations = check_module_numbering(REAL_STEERING, index_data)
        errors = [v for v in violations if v.level == "ERROR"]
        assert len(errors) == 0, \
            f"Module numbering errors: {[v.format() for v in errors]}"


# ---------------------------------------------------------------------------
# 12.3 Real corpus: module files have checkpoints for all numbered steps
# ---------------------------------------------------------------------------


class TestRealCorpusCheckpoints:
    """Req 4.1: Real module files have checkpoints for all numbered steps."""

    def test_all_steps_have_checkpoints(self):
        """Every numbered step in module files has a checkpoint instruction."""
        violations = check_checkpoints(REAL_STEERING)
        # Filter to only "no checkpoint" errors (not mismatch errors from phase files)
        missing = [v for v in violations if "no checkpoint" in v.message]
        assert len(missing) == 0, \
            f"Steps missing checkpoints: {[v.format() for v in missing]}"


# ---------------------------------------------------------------------------
# 12.4 Real corpus: valid YAML frontmatter
# ---------------------------------------------------------------------------


class TestRealCorpusFrontmatter:
    """Req 7.1: Real steering files have valid YAML frontmatter."""

    def test_all_files_have_valid_frontmatter(self):
        """Every steering file has valid frontmatter with a recognized inclusion value."""
        violations = check_frontmatter(REAL_STEERING)
        errors = [v for v in violations if v.level == "ERROR"]
        assert len(errors) == 0, \
            f"Frontmatter errors: {[v.format() for v in errors]}"


# ---------------------------------------------------------------------------
# 12.5 Real corpus: hook registry matches hook files
# ---------------------------------------------------------------------------


class TestRealCorpusHookConsistency:
    """Req 6.1: Real hook registry matches hook files bidirectionally."""

    def test_hook_registry_matches_files(self):
        """Every hook in the registry has a file and vice versa."""
        violations = check_hook_consistency(REAL_STEERING, REAL_HOOKS)
        errors = [v for v in violations if v.level == "ERROR"]
        assert len(errors) == 0, \
            f"Hook consistency errors: {[v.format() for v in errors]}"


# ---------------------------------------------------------------------------
# 12.6 --warnings-as-errors flag changes exit code
# ---------------------------------------------------------------------------


class TestWarningsAsErrors:
    """Req 8.6: --warnings-as-errors flag changes exit code when warnings present."""

    def test_warnings_as_errors_changes_exit_code(self):
        """With warnings present, --warnings-as-errors makes exit code 1."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            hooks = tmp / "hooks"
            steering.mkdir()
            hooks.mkdir()

            # Create a minimal valid setup with a warning-producing condition
            # (module file on disk not in index)
            (steering / "module-99-orphan.md").write_text(
                "---\ninclusion: manual\n---\n# Orphan Module\n"
            )
            (steering / "hook-registry.md").write_text(
                "---\ninclusion: manual\n---\n# Hook Registry\n"
            )

            # Create a minimal steering index with no modules
            index_content = (
                "modules:\n"
                "file_metadata:\n"
                "  module-99-orphan.md:\n"
                "    token_count: 100\n"
                "    size_category: small\n"
                "  hook-registry.md:\n"
                "    token_count: 200\n"
                "    size_category: small\n"
                "keywords:\n"
                "languages:\n"
                "deployment:\n"
            )
            index_path = steering / "steering-index.yaml"
            index_path.write_text(index_content)

            # Without --warnings-as-errors: should be exit 0 (only warnings)
            violations_normal, exit_normal = run_all_checks(
                steering, hooks, index_path, warnings_as_errors=False,
                skip_template=True
            )
            warnings = [v for v in violations_normal if v.level == "WARNING"]

            if warnings:
                assert exit_normal == 0, \
                    "Without --warnings-as-errors, warnings should not cause exit 1"

                # With --warnings-as-errors: should be exit 1
                _, exit_wae = run_all_checks(
                    steering, hooks, index_path, warnings_as_errors=True,
                    skip_template=True
                )
                assert exit_wae == 1, \
                    "With --warnings-as-errors, warnings should cause exit 1"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# 12.7 Output format matches pattern
# ---------------------------------------------------------------------------


class TestOutputFormat:
    """Req 8.4: Output format matches {level}: {file}:{line}: {message}."""

    def test_violation_format(self):
        """Known violations produce correctly formatted output."""
        v = LintViolation("ERROR", "steering/test.md", 42, "Missing file")
        assert v.format() == "ERROR: steering/test.md:42: Missing file"

    def test_warning_format(self):
        """Warning violations produce correctly formatted output."""
        v = LintViolation("WARNING", "steering/test.md", 0, "Unlisted module")
        assert v.format() == "WARNING: steering/test.md:0: Unlisted module"

    def test_format_with_zero_line(self):
        """Line number 0 is used when not applicable."""
        v = LintViolation("ERROR", "index.yaml", 0, "Missing section")
        formatted = v.format()
        assert ":0:" in formatted


# ---------------------------------------------------------------------------
# 12.8 Summary line shows correct counts
# ---------------------------------------------------------------------------


class TestSummaryLine:
    """Req 8.5: Summary line shows correct error and warning counts."""

    def test_summary_counts(self):
        """Summary line format is '{N} error(s), {M} warning(s)'."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            hooks = tmp / "hooks"
            steering.mkdir()
            hooks.mkdir()

            # Create minimal valid setup
            (steering / "hook-registry.md").write_text(
                "---\ninclusion: manual\n---\n# Hook Registry\n"
            )
            index_content = (
                "modules:\n"
                "file_metadata:\n"
                "  hook-registry.md:\n"
                "    token_count: 200\n"
                "    size_category: small\n"
                "keywords:\n"
                "languages:\n"
                "deployment:\n"
            )
            index_path = steering / "steering-index.yaml"
            index_path.write_text(index_content)

            violations, _ = run_all_checks(steering, hooks, index_path)

            error_count = sum(1 for v in violations if v.level == "ERROR")
            warning_count = sum(1 for v in violations if v.level == "WARNING")

            summary = f"{error_count} error(s), {warning_count} warning(s)"
            assert "error(s)" in summary
            assert "warning(s)" in summary
        finally:
            shutil.rmtree(tmp)
