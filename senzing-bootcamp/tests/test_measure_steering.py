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

    def test_check_mode_no_modification_with_phases(self):
        """--check leaves the YAML byte-identical even when validating phases.

        Builds an index that has a phases block (so check_phase_counts runs) and
        confirms the new phase-validation path is read-only — both for an
        in-tolerance phase and a drifted phase.

        **Validates: Requirements 2.2, 3.1**
        """
        mod = _load_measure_steering()

        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = 500
            measured = round(len(content) / 4)

            # Drifted phase so check_phase_counts has a mismatch to report.
            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=2 * measured, phase_cat=mod.classify_size(2 * measured),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            content_before = index_path.read_text(encoding="utf-8")
            exit_code, _out = _run_check_cli(steering_dir, index_path)
            content_after = index_path.read_text(encoding="utf-8")

            assert content_before == content_after, "--check modified the YAML file"
            assert exit_code != 0  # drifted phase => non-zero, but still no write
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

        real_index_path = steering_dir / "steering-index.yaml"
        assert real_index_path.exists(), "steering-index.yaml not found"

        # Scan the real steering directory
        metadata = mod.scan_steering_files(steering_dir)
        assert len(metadata) > 0, "No .md files found in steering directory"

        total = sum(m["token_count"] for m in metadata.values())

        # Operate on a temp COPY of the real index so the test never mutates the
        # tracked steering-index.yaml. update_index now reconciles phase counts
        # too, so writing the real file in-place could dirty the working tree.
        td = tempfile.mkdtemp()
        try:
            index_path = Path(td) / "steering-index.yaml"
            index_path.write_text(
                real_index_path.read_text(encoding="utf-8"), encoding="utf-8"
            )

            # Update the (temp) index
            mod.update_index(index_path, metadata, total, steering_dir)

            # Now --check should pass (no mismatches) for both file_metadata
            # and the phases map.
            mismatches = mod.check_counts(index_path, metadata)
            assert mismatches == [], f"Unexpected mismatches after update: {mismatches}"

            phase_mismatches = mod.check_phase_counts(index_path, steering_dir)
            assert phase_mismatches == [], (
                f"Unexpected phase mismatches after update: {phase_mismatches}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Phase token-count code paths — check_phase_counts / rewrite_phase_counts
# (steering-index-token-count-sync bugfix)
# ---------------------------------------------------------------------------

# Strategies (st_-prefixed per python-conventions.md)


def st_measured():
    """Generate a positive measured token count (1..10000)."""
    return st.integers(min_value=1, max_value=10_000)


def st_drift_factor():
    """Generate a drift multiplier straddling the 10% tolerance boundary."""
    return st.floats(
        min_value=0.0, max_value=3.0, allow_nan=False, allow_infinity=False
    )


def _run_check_cli(steering_dir, index_path):
    """Run measure_steering.main() in --check mode, return (exit_code, stdout)."""
    mod = _load_measure_steering()
    buf = io.StringIO()
    argv = [
        "measure_steering.py",
        "--check",
        "--steering-dir",
        str(steering_dir),
        "--index-path",
        str(index_path),
    ]
    with patch.object(sys, "argv", argv):
        with patch("sys.stdout", buf):
            try:
                mod.main()
            except SystemExit as exc:
                code = exc.code
                return (int(code) if code is not None else 0, buf.getvalue())
    return (0, buf.getvalue())


def _build_phase_index(
    steering_dir, index_path, fname, content, phase_count, phase_cat, fm_count, fm_cat
):
    """Write a temp steering file + index (one module/phase + file_metadata).

    The phases block sits above file_metadata (mirroring the real index layout),
    so phase entries are parsed/validated independently of file_metadata.
    """
    (Path(steering_dir) / fname).write_text(content, encoding="utf-8")
    index_text = (
        "modules:\n"
        "  1:\n"
        f"    root: {fname}\n"
        "    phases:\n"
        "      phase1:\n"
        f"        file: {fname}\n"
        f"        token_count: {phase_count}\n"
        f"        size_category: {phase_cat}\n"
        "        step_range: [1, 9]\n"
        "\n"
        "file_metadata:\n"
        f"  {fname}:\n"
        f"    token_count: {fm_count}\n"
        f"    size_category: {fm_cat}\n"
        "\n"
        "budget:\n"
        f"  total_tokens: {fm_count}\n"
        "  reference_window: 200000\n"
        "  warn_threshold_pct: 60\n"
        "  critical_threshold_pct: 80\n"
    )
    Path(index_path).write_text(index_text, encoding="utf-8")


class TestCheckPhaseCountsDetectsDrift:
    """check_phase_counts + --check detect drifted phase entries.

    Complements the file_metadata-only cases (TestProperty7 / TestProperty8) by
    validating the phases map: a drifted phase is reported and makes --check exit
    non-zero, while an in-tolerance phase is not flagged and --check exits 0.

    **Validates: Requirements 2.2, 2.6**
    """

    def test_check_phase_counts_flags_drifted_phase(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = round(2000 / 4) = 500
            measured = round(len(content) / 4)
            phase_count = 2 * measured  # 100% drift, far beyond 10%

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=phase_count, phase_cat=mod.classify_size(phase_count),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            mismatches = mod.check_phase_counts(index_path, steering_dir)
            assert any(m[0] == fname for m in mismatches), (
                f"expected drifted phase {fname} flagged, got {mismatches}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_check_phase_counts_ignores_in_tolerance_phase(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = 500
            measured = round(len(content) / 4)

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=measured, phase_cat=mod.classify_size(measured),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            mismatches = mod.check_phase_counts(index_path, steering_dir)
            assert mismatches == [], f"in-tolerance phase flagged: {mismatches}"
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_check_cli_exits_nonzero_on_drifted_phase(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = 500
            measured = round(len(content) / 4)
            phase_count = 2 * measured

            # file_metadata kept in sync so ONLY the phase is out of tolerance —
            # this isolates the new phase-validation path from check_counts.
            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=phase_count, phase_cat=mod.classify_size(phase_count),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            exit_code, out = _run_check_cli(steering_dir, index_path)
            assert exit_code != 0, f"--check exited {exit_code}; output: {out!r}"
            assert "Phase token count mismatches" in out, (
                f"expected phase mismatch report in output: {out!r}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_check_cli_exits_zero_when_phase_in_tolerance(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = 500
            measured = round(len(content) / 4)

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=measured, phase_cat=mod.classify_size(measured),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            exit_code, out = _run_check_cli(steering_dir, index_path)
            assert exit_code == 0, f"--check exited {exit_code}; output: {out!r}"
            assert "within 10% tolerance" in out
        finally:
            shutil.rmtree(td, ignore_errors=True)

    @given(measured=st_measured(), factor=st_drift_factor())
    @settings(max_examples=20)
    def test_check_phase_counts_flags_exactly_out_of_tolerance(self, measured, factor):
        mod = _load_measure_steering()
        stored = round(measured * factor)
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * (4 * measured)  # round(len / 4) == measured

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=stored, phase_cat=mod.classify_size(stored),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            mismatches = mod.check_phase_counts(index_path, steering_dir)
            flagged = any(m[0] == fname for m in mismatches)
            drift = abs(stored - measured) / max(measured, 1)
            if drift > 0.10:
                assert flagged, (
                    f"expected flag for stored={stored}, measured={measured} "
                    f"(drift={drift:.2%})"
                )
            else:
                assert not flagged, (
                    f"unexpected flag for stored={stored}, measured={measured} "
                    f"(drift={drift:.2%})"
                )
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestRewritePhaseCounts:
    """rewrite_phase_counts corrects drift, preserves in-tolerance, fixes category.

    Covers the three behaviors called out in the design: a drifted phase is
    reconciled to the measured count (and back within tolerance), an in-tolerance
    phase is left byte-identical, and a corrected count crossing the 2000 boundary
    recomputes size_category medium -> large.

    **Validates: Requirements 2.1, 2.3, 2.5**
    """

    def test_drifted_phase_corrected(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = 500
            measured = round(len(content) / 4)
            drifted = 4 * measured  # 300% drift

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=drifted, phase_cat=mod.classify_size(drifted),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            original = index_path.read_text(encoding="utf-8")
            rewritten = mod.rewrite_phase_counts(original, steering_dir)

            entries = mod._parse_phase_entries(rewritten)
            phase = next((e for e in entries if e.filename == fname), None)
            assert phase is not None, "phase entry vanished after rewrite"
            assert phase.token_count == measured, (
                f"expected reconciled token_count={measured}, got {phase.token_count}"
            )
            assert phase.size_category == mod.classify_size(measured)
            # Reconciled value is now within tolerance.
            assert abs(phase.token_count - measured) / max(measured, 1) <= 0.10
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_in_tolerance_phase_byte_identical(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = 500
            measured = round(len(content) / 4)

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=measured, phase_cat=mod.classify_size(measured),
                fm_count=measured, fm_cat=mod.classify_size(measured),
            )

            original = index_path.read_text(encoding="utf-8")
            rewritten = mod.rewrite_phase_counts(original, steering_dir)
            assert rewritten == original, "in-tolerance phase was not byte-identical"
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_size_category_recomputed_across_2000_boundary(self):
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 12000  # measured = 3000 -> large (over the 2000 boundary)
            measured = round(len(content) / 4)
            drifted = 1894  # medium, below the 2000 boundary (mirrors module-05)

            assert mod.classify_size(drifted) == "medium"
            assert mod.classify_size(measured) == "large"

            _build_phase_index(
                steering_dir, index_path, fname, content,
                phase_count=drifted, phase_cat=mod.classify_size(drifted),
                fm_count=drifted, fm_cat=mod.classify_size(drifted),
            )

            original = index_path.read_text(encoding="utf-8")
            rewritten = mod.rewrite_phase_counts(original, steering_dir)

            entries = mod._parse_phase_entries(rewritten)
            phase = next((e for e in entries if e.filename == fname), None)
            assert phase is not None
            assert phase.token_count == measured
            assert phase.size_category == "large", (
                f"expected medium -> large reclassification, got {phase.size_category}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)
