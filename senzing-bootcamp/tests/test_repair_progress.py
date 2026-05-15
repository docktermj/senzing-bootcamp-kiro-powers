"""Tests for senzing-bootcamp/scripts/repair_progress.py."""

import importlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_repair():
    """Import / reload repair_progress module."""
    import repair_progress
    importlib.reload(repair_progress)
    return repair_progress


# ---------------------------------------------------------------------------
# Artifact helpers — create the on-disk artifacts that detect() looks for
# ---------------------------------------------------------------------------

# Mapping: module number → callable(root) that creates the artifact
ARTIFACT_CREATORS = {
    1: lambda r: (r / "docs" / "business_problem.md").write_text("x", encoding="utf-8"),
    2: lambda r: (r / "database" / "G2C.db").write_text("x", encoding="utf-8"),
    3: lambda r: (r / "src" / "quickstart_demo" / "demo.py").write_text("x", encoding="utf-8"),
    4: lambda r: (r / "data" / "raw" / "sample.csv").write_text("x", encoding="utf-8"),
    5: lambda r: (r / "docs" / "data_quality_report.md").write_text("x", encoding="utf-8"),
    6: lambda r: (r / "src" / "load" / "loader.py").write_text("x", encoding="utf-8"),
    # Module 7 requires multi-source in progress JSON — skip for artifact-only tests
    8: lambda r: (r / "src" / "query" / "query.py").write_text("x", encoding="utf-8"),
    9: lambda r: (r / "docs" / "performance_report.md").write_text("x", encoding="utf-8"),
    10: lambda r: (r / "docs" / "security_checklist.md").write_text("x", encoding="utf-8"),
    11: lambda r: (r / "monitoring").mkdir(parents=True, exist_ok=True),
}


def _create_artifact(root, module_num):
    """Create the on-disk artifact for *module_num* under *root*."""
    creator = ARTIFACT_CREATORS.get(module_num)
    if creator is None:
        return
    # Ensure parent dirs exist
    p = root  # just for reference
    creator_needs_dirs = {
        1: ["docs"], 2: ["database"], 3: ["src", "quickstart_demo"],
        4: ["data", "raw"], 5: ["docs"], 6: ["src", "load"],
        8: ["src", "query"], 9: ["docs"], 10: ["docs"],
    }
    parts = creator_needs_dirs.get(module_num)
    if parts:
        (root / os.path.join(*parts)).mkdir(parents=True, exist_ok=True)
    creator(root)


# ---------------------------------------------------------------------------
# Example-based tests  (Task 3.1)
# ---------------------------------------------------------------------------


class TestDetectNoArtifacts:
    """Requirement 3.2 — no artifacts → detect() returns empty set."""

    def test_empty_project(self, project_root):
        mod = _load_repair()
        result = mod.detect()
        assert result == set()


class TestFixWritesValidJSON:
    """Requirement 3.3 — --fix writes valid JSON with correct fields."""

    def test_fix_writes_progress(self, project_root, capsys):
        # Create artifacts for modules 1 and 2
        _create_artifact(project_root, 1)
        _create_artifact(project_root, 2)

        mod = _load_repair()
        with patch.object(sys, "argv", ["repair_progress.py", "--fix"]):
            mod.main()

        progress_file = project_root / "config" / "bootcamp_progress.json"
        assert progress_file.exists()
        data = json.loads(progress_file.read_text(encoding="utf-8"))
        assert 1 in data["modules_completed"]
        assert 2 in data["modules_completed"]
        assert "current_module" in data


class TestDiscrepancyReporting:
    """Requirement 3.4 — discrepancy reporting for unrecorded modules."""

    def test_unrecorded_modules_reported(self, project_root, write_progress_file, capsys):
        # Write progress that says only module 1 is done
        write_progress_file({
            "modules_completed": [1],
            "current_module": 2,
            "language": "python",
            "data_sources": [],
        })
        # But create artifacts for modules 1 AND 2
        _create_artifact(project_root, 1)
        _create_artifact(project_root, 2)

        mod = _load_repair()
        with patch.object(sys, "argv", ["repair_progress.py"]):
            mod.main()

        out = capsys.readouterr().out
        assert "Unrecorded" in out or "2" in out


# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 3.2 & 3.3)
# ---------------------------------------------------------------------------

from hypothesis import given, settings
import hypothesis.strategies as st

# Modules we can create artifacts for (excluding 7 which needs JSON state)
TESTABLE_MODULES = sorted(ARTIFACT_CREATORS.keys())

module_artifact_subsets = st.lists(
    st.sampled_from(TESTABLE_MODULES), unique=True, max_size=len(TESTABLE_MODULES)
).map(set)


class TestProperty3ArtifactDetection:
    """Property 3: Artifact detection correctness.

    **Validates: Requirements 3.1**

    For any subset of module artifacts created on disk,
    detect() returns exactly those module numbers.
    """

    # Feature: script-test-suite, Property 3: Artifact detection correctness

    @given(modules=module_artifact_subsets)
    @settings(max_examples=10)
    def test_detect_matches_artifacts(self, modules):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            for m in modules:
                _create_artifact(root, m)

            mod = _load_repair()
            detected = mod.detect()

            # detect() should find exactly the modules whose artifacts we created
            assert detected == modules, (
                f"Expected {modules}, got {detected}. "
                f"Extra: {detected - modules}, Missing: {modules - detected}"
            )
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


class TestProperty4RepairRoundTrip:
    """Property 4: Repair progress round-trip.

    **Validates: Requirements 3.5**

    For any artifact set, detect → fix → re-detect produces
    the same completed set.
    """

    # Feature: script-test-suite, Property 4: Repair progress round-trip

    @given(modules=module_artifact_subsets)
    @settings(max_examples=10)
    def test_round_trip(self, modules):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            for m in modules:
                _create_artifact(root, m)

            mod = _load_repair()

            # First detect
            first_detect = mod.detect()

            # Fix (writes progress JSON)
            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py", "--fix"]):
                with patch("sys.stdout", captured):
                    mod.main()

            # Re-detect — should produce the same set
            second_detect = mod.detect()
            assert first_detect == second_detect
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)
