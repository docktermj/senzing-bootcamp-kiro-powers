"""Tests for senzing-bootcamp/scripts/measure_steering.py.

Property-based tests (Hypothesis) for Properties 1–8 and example-based
unit / integration tests for the context-budget-tracking feature.
"""

import importlib
import io
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given, settings, assume
import hypothesis.strategies as st


# ---------------------------------------------------------------------------
# Helper: import (or reload) measure_steering
# ---------------------------------------------------------------------------

def _load_measure_steering():
    import measure_steering
    importlib.reload(measure_steering)
    return measure_steering


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Filenames: 1-20 lowercase chars + ".md"
_filename_st = st.from_regex(r"[a-z][a-z0-9\-]{0,19}\.md", fullmatch=True)

# File content: arbitrary text (including unicode and empty)
_content_st = st.text(min_size=0, max_size=4000)

# Non-negative token counts
_token_count_st = st.integers(min_value=0, max_value=500_000)

# Sets of unique filenames (1-10 files)
_filename_set_st = st.lists(
    _filename_st, min_size=1, max_size=10, unique=True
)


# ---------------------------------------------------------------------------
# Property-Based Tests — Task 8.1
# ---------------------------------------------------------------------------


class TestProperty1ScanCompletenessAndStructure:
    """Property 1: Scan produces complete, correctly-structured metadata.

    For any set of .md files in a steering directory, scan returns
    file_metadata with matching keys, each having integer token_count
    and valid size_category.

    **Validates: Requirements 1.1, 1.2, 2.4, 2.5**
    """

    # Feature: context-budget-tracking, Property 1: Scan produces complete, correctly-structured metadata

    @given(
        filenames=_filename_set_st,
        contents=st.lists(_content_st, min_size=1, max_size=10),
    )
    @settings(max_examples=10)
    def test_scan_completeness_and_structure(self, filenames, contents):
        # Pad contents to match filenames length
        while len(contents) < len(filenames):
            contents.append("")

        td = tempfile.mkdtemp()
        try:
            for fname, content in zip(filenames, contents):
                (Path(td) / fname).write_text(content, encoding="utf-8")

            mod = _load_measure_steering()
            metadata = mod.scan_steering_files(td)

            # Keys match exactly
            assert set(metadata.keys()) == set(filenames)

            for fname in filenames:
                entry = metadata[fname]
                # token_count is an integer
                assert isinstance(entry["token_count"], int)
                # size_category is valid
                assert entry["size_category"] in {"small", "medium", "large"}
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestProperty2SizeClassificationThresholds:
    """Property 2: Size classification follows threshold rules.

    For any non-negative integer, classify_size returns small (<500),
    medium (500-2000), large (>2000).

    **Validates: Requirements 1.3**
    """

    # Feature: context-budget-tracking, Property 2: Size classification follows threshold rules

    @given(token_count=_token_count_st)
    @settings(max_examples=10)
    def test_classify_size_thresholds(self, token_count):
        mod = _load_measure_steering()
        result = mod.classify_size(token_count)

        if token_count < 500:
            assert result == "small"
        elif token_count <= 2000:
            assert result == "medium"
        else:
            assert result == "large"


class TestProperty3TokenCountFormula:
    """Property 3: Token count equals rounded character-count-over-four.

    For any string, calculate_token_count returns round(len(content)/4).

    **Validates: Requirements 2.1**
    """

    # Feature: context-budget-tracking, Property 3: Token count equals rounded character-count-over-four

    @given(content=st.text(min_size=0, max_size=5000))
    @settings(max_examples=10)
    def test_token_count_formula(self, content):
        td = tempfile.mkdtemp()
        try:
            filepath = Path(td) / "test.md"
            filepath.write_text(content, encoding="utf-8")

            mod = _load_measure_steering()
            result = mod.calculate_token_count(filepath)
            # read_text in text mode normalizes \r\n to \n on write,
            # so use the actual file content length for the expected value
            actual_content = filepath.read_text(encoding="utf-8")
            expected = round(len(actual_content) / 4)
            assert result == expected
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestProperty4TotalTokensSumInvariant:
    """Property 4: Total tokens equals sum of individual counts.

    For any file_metadata dict, budget.total_tokens equals sum of all
    token_counts.

    **Validates: Requirements 1.4**
    """

    # Feature: context-budget-tracking, Property 4: Total tokens equals sum of individual counts

    @given(
        filenames=_filename_set_st,
        counts=st.lists(st.integers(min_value=0, max_value=100_000), min_size=1, max_size=10),
    )
    @settings(max_examples=10)
    def test_total_tokens_sum_invariant(self, filenames, counts):
        while len(counts) < len(filenames):
            counts.append(0)

        file_metadata = {}
        for fname, count in zip(filenames, counts):
            file_metadata[fname] = {
                "token_count": count,
                "size_category": "small",
            }

        total = sum(m["token_count"] for m in file_metadata.values())

        td = tempfile.mkdtemp()
        try:
            index_path = Path(td) / "steering-index.yaml"
            mod = _load_measure_steering()
            mod.update_index(index_path, file_metadata, total)

            content = index_path.read_text(encoding="utf-8")
            match = re.search(r"total_tokens:\s*(\d+)", content)
            assert match is not None
            assert int(match.group(1)) == total
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestProperty5UpdatePreservesExistingYAML:
    """Property 5: Update preserves existing YAML content.

    For any valid steering-index.yaml with existing sections, update
    preserves them.

    **Validates: Requirements 1.5, 2.2**
    """

    # Feature: context-budget-tracking, Property 5: Update preserves existing YAML content

    @given(
        filenames=_filename_set_st,
        counts=st.lists(st.integers(min_value=0, max_value=50_000), min_size=1, max_size=5),
    )
    @settings(max_examples=10)
    def test_update_preserves_existing_yaml(self, filenames, counts):
        while len(counts) < len(filenames):
            counts.append(0)

        existing_yaml = (
            "modules:\n"
            "  1: module-01.md\n"
            "  2: module-02.md\n"
            "\n"
            "keywords:\n"
            "  error: common-pitfalls.md\n"
            "\n"
            "languages:\n"
            "  python: lang-python.md\n"
            "\n"
            "deployment:\n"
            "  aws: deployment-aws.md\n"
            "\n"
            "references:\n"
            "  api: api-reference.md\n"
        )

        file_metadata = {}
        for fname, count in zip(filenames, counts):
            file_metadata[fname] = {
                "token_count": count,
                "size_category": "small",
            }
        total = sum(m["token_count"] for m in file_metadata.values())

        td = tempfile.mkdtemp()
        try:
            index_path = Path(td) / "steering-index.yaml"
            index_path.write_text(existing_yaml, encoding="utf-8")

            mod = _load_measure_steering()
            mod.update_index(index_path, file_metadata, total)

            updated = index_path.read_text(encoding="utf-8")

            # All existing sections must be preserved
            for section in ["modules:", "keywords:", "languages:", "deployment:", "references:"]:
                assert section in updated, f"Section '{section}' was not preserved"

            # Specific content must be preserved
            assert "1: module-01.md" in updated
            assert "error: common-pitfalls.md" in updated
            assert "python: lang-python.md" in updated
            assert "aws: deployment-aws.md" in updated
            assert "api: api-reference.md" in updated
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestProperty6SummaryContainsAllInfo:
    """Property 6: Summary output contains all file information.

    For any non-empty file_metadata, printed summary contains every
    filename, token count, size category, and total.

    **Validates: Requirements 2.6**
    """

    # Feature: context-budget-tracking, Property 6: Summary output contains all file information

    @given(
        filenames=_filename_set_st,
        counts=st.lists(st.integers(min_value=0, max_value=50_000), min_size=1, max_size=10),
    )
    @settings(max_examples=10)
    def test_summary_contains_all_info(self, filenames, counts):
        while len(counts) < len(filenames):
            counts.append(0)

        mod = _load_measure_steering()

        file_metadata = {}
        for fname, count in zip(filenames, counts):
            cat = mod.classify_size(count)
            file_metadata[fname] = {
                "token_count": count,
                "size_category": cat,
            }
        total = sum(m["token_count"] for m in file_metadata.values())

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            mod.print_summary(file_metadata, total)
        output = buf.getvalue()

        for fname in filenames:
            assert fname in output, f"Filename '{fname}' not in summary"
        for fname, meta in file_metadata.items():
            assert str(meta["token_count"]) in output
            assert meta["size_category"] in output
        assert str(total) in output


class TestProperty7CheckModeThresholdDetection:
    """Property 7: Check mode detects mismatches exceeding 10% tolerance.

    For any (stored, calculated) pair where abs difference > 10%,
    check reports mismatch.

    **Validates: Requirements 2.7**
    """

    # Feature: context-budget-tracking, Property 7: Check mode detects mismatches exceeding 10% tolerance

    @given(
        stored=st.integers(min_value=0, max_value=100_000),
        calculated=st.integers(min_value=1, max_value=100_000),
    )
    @settings(max_examples=10)
    def test_check_mode_threshold_detection(self, stored, calculated):
        mod = _load_measure_steering()

        fname = "test-file.md"
        denominator = max(calculated, 1)
        diff_pct = abs(stored - calculated) / denominator

        # Build a YAML with stored count
        yaml_content = (
            f"file_metadata:\n"
            f"  {fname}:\n"
            f"    token_count: {stored}\n"
            f"    size_category: medium\n"
            f"\n"
            f"budget:\n"
            f"  total_tokens: {stored}\n"
            f"  reference_window: 200000\n"
            f"  warn_threshold_pct: 60\n"
            f"  critical_threshold_pct: 80\n"
        )

        td = tempfile.mkdtemp()
        try:
            index_path = Path(td) / "steering-index.yaml"
            index_path.write_text(yaml_content, encoding="utf-8")

            calc_metadata = {
                fname: {"token_count": calculated, "size_category": "medium"}
            }

            mismatches = mod.check_counts(index_path, calc_metadata)

            if diff_pct > 0.10:
                assert len(mismatches) > 0, (
                    f"Expected mismatch for stored={stored}, calc={calculated} "
                    f"(diff={diff_pct:.2%})"
                )
            else:
                assert len(mismatches) == 0, (
                    f"Unexpected mismatch for stored={stored}, calc={calculated} "
                    f"(diff={diff_pct:.2%})"
                )
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestProperty8ValidatorDetectsMalformedMetadata:
    """Property 8: Validator detects missing or malformed metadata entries.

    For any file set + malformed metadata, validation reports errors.

    **Validates: Requirements 5.2, 5.3**
    """

    # Feature: context-budget-tracking, Property 8: Validator detects missing or malformed metadata entries

    @given(
        filenames=_filename_set_st,
        missing_idx=st.integers(min_value=0, max_value=9),
    )
    @settings(max_examples=10)
    def test_validator_detects_malformed_metadata(self, filenames, missing_idx):
        """Create a steering dir with .md files but omit one from file_metadata."""
        mod = _load_measure_steering()

        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()

            # Create .md files
            for fname in filenames:
                (steering_dir / fname).write_text("content", encoding="utf-8")

            # Build file_metadata with one entry missing
            skip_idx = missing_idx % len(filenames)
            skipped_file = filenames[skip_idx]

            lines = ["file_metadata:"]
            for i, fname in enumerate(sorted(filenames)):
                if fname == skipped_file:
                    continue
                count = mod.calculate_token_count(steering_dir / fname)
                cat = mod.classify_size(count)
                lines.append(f"  {fname}:")
                lines.append(f"    token_count: {count}")
                lines.append(f"    size_category: {cat}")

            total = sum(
                mod.calculate_token_count(steering_dir / f)
                for f in filenames if f != skipped_file
            )
            lines.extend([
                "",
                "budget:",
                f"  total_tokens: {total}",
                "  reference_window: 200000",
                "  warn_threshold_pct: 60",
                "  critical_threshold_pct: 80",
            ])

            index_path = steering_dir / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # Now scan and check — the missing file should cause a mismatch
            calculated = mod.scan_steering_files(steering_dir)
            mismatches = mod.check_counts(index_path, calculated)

            # The skipped file should appear as a mismatch (missing from stored)
            mismatch_files = [m[0] for m in mismatches]
            assert skipped_file in mismatch_files, (
                f"Expected '{skipped_file}' to be reported as mismatch "
                f"but got: {mismatch_files}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Example-Based Unit Tests — Task 8.2
# ---------------------------------------------------------------------------


class TestCheckModeDoesNotModifyYAML:
    """--check mode does not modify the YAML file.

    **Validates: Requirements 2.7**
    """

    def test_check_mode_no_modification(self):
        mod = _load_measure_steering()

        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            (steering_dir / "example.md").write_text("Hello world", encoding="utf-8")

            # Run update first to create valid YAML
            metadata = mod.scan_steering_files(steering_dir)
            total = sum(m["token_count"] for m in metadata.values())
            index_path = steering_dir / "steering-index.yaml"
            mod.update_index(index_path, metadata, total)

            # Record content before check
            content_before = index_path.read_text(encoding="utf-8")
            mtime_before = index_path.stat().st_mtime

            # Run check
            mismatches = mod.check_counts(index_path, metadata)

            # File must be unchanged
            content_after = index_path.read_text(encoding="utf-8")
            assert content_before == content_after
            assert mismatches == []
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestAgentInstructionsContextBudget:
    """agent-instructions.md contains 'Context Budget' section.

    **Validates: Requirements 3.1**
    """

    def test_agent_instructions_has_context_budget(self):
        ai_path = Path("senzing-bootcamp/steering/agent-instructions.md")
        assert ai_path.exists(), "agent-instructions.md not found"
        content = ai_path.read_text(encoding="utf-8")
        assert "## Context Budget" in content


class TestCIWorkflowTokenValidation:
    """CI workflow has 'Validate steering token counts' step.

    **Validates: Requirements 4.1, 4.3**
    """

    def test_ci_workflow_has_token_validation_step(self):
        workflow_path = Path(".github/workflows/validate-power.yml")
        assert workflow_path.exists(), "validate-power.yml not found"
        content = workflow_path.read_text(encoding="utf-8")
        assert "Validate steering token counts" in content
        assert "measure_steering.py --check" in content


class TestPowerMdMeasureSteering:
    """POWER.md contains measure_steering.py in Useful Commands.

    **Validates: Requirements 6.2**
    """

    def test_power_md_has_measure_steering(self):
        power_path = Path("senzing-bootcamp/POWER.md")
        assert power_path.exists(), "POWER.md not found"
        content = power_path.read_text(encoding="utf-8")
        assert "measure_steering.py" in content


# ---------------------------------------------------------------------------
# Integration Test — Task 8.3
# ---------------------------------------------------------------------------


class TestIntegrationRealSteering:
    """Run measure_steering.py against the real steering directory,
    then verify --check passes.

    **Validates: Requirements 2.1, 2.7**
    """

    def test_update_then_check_passes(self):
        mod = _load_measure_steering()

        steering_dir = Path("senzing-bootcamp/steering")
        assert steering_dir.is_dir(), "Real steering directory not found"

        index_path = steering_dir / "steering-index.yaml"
        assert index_path.exists(), "steering-index.yaml not found"

        # Scan the real steering directory
        metadata = mod.scan_steering_files(steering_dir)
        assert len(metadata) > 0, "No .md files found in steering directory"

        total = sum(m["token_count"] for m in metadata.values())

        # Update the index
        mod.update_index(index_path, metadata, total)

        # Now --check should pass (no mismatches)
        mismatches = mod.check_counts(index_path, metadata)
        assert mismatches == [], f"Unexpected mismatches after update: {mismatches}"
