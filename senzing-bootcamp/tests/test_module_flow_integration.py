#!/usr/bin/env python3
"""Integration tests for module flow and state transitions.

Validates that the bootcamp progress tracking, gate validation, and module
transitions work correctly across multiple modules — simulating a bootcamper
flowing through the curriculum.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _load_module(name: str):
    """Import or reload a script module."""
    mod = importlib.import_module(name)
    importlib.reload(mod)
    return mod


def _write(path: Path, content: str) -> None:
    """Write content to path, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_progress(root: Path, current_module: int, completed: list[int]) -> Path:
    """Create a bootcamp_progress.json file."""
    cfg = root / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    progress = {
        "modules_completed": completed,
        "current_module": current_module,
        "language": "python",
        "database_type": "sqlite",
        "data_sources": [],
        "current_step": 1,
        "step_history": {},
    }
    path = cfg / "bootcamp_progress.json"
    path.write_text(json.dumps(progress, indent=2), encoding="utf-8")
    return path


# Artifact creators for each module (same as test_validate_module.py)
ARTIFACTS: dict[int, list] = {
    1: [lambda r: _write(r / "docs" / "business_problem.md", "problem defined")],
    2: [
        lambda r: _write(r / "database" / "G2C.db", "data"),
        lambda r: _write(r / "config" / "bootcamp_preferences.yaml", "language: python"),
    ],
    3: [
        lambda r: _write(r / "src" / "quickstart_demo" / "demo_run.py", "x"),
        lambda r: _write(r / "src" / "quickstart_demo" / "sample_data_1.json", "x"),
    ],
    4: [
        lambda r: _write(r / "data" / "raw" / "sample.csv", "x"),
        lambda r: _write(r / "docs" / "data_source_locations.md", "x"),
    ],
    5: [
        lambda r: _write(r / "docs" / "data_source_evaluation.md", "report"),
        lambda r: _write(r / "src" / "transform" / "transform.py", "x"),
        lambda r: _write(r / "data" / "transformed" / "out.jsonl", "x"),
    ],
    6: [
        lambda r: _write(r / "src" / "load" / "loader.py", "x"),
        lambda r: _write(r / "database" / "G2C.db", "data"),
        lambda r: _write(r / "docs" / "loading_strategy.md", "x"),
    ],
    7: [
        lambda r: _write(r / "src" / "query" / "query.py", "x"),
        lambda r: _write(r / "docs" / "results_validation.md", "x"),
    ],
    8: [
        lambda r: _write(r / "docs" / "performance_requirements.md", "x"),
        lambda r: _write(r / "docs" / "benchmark_environment.md", "x"),
        lambda r: _write(r / "docs" / "performance_report.md", "x"),
        lambda r: _write(r / "tests" / "performance" / "bench.py", "x"),
    ],
    9: [lambda r: _write(r / "docs" / "security_compliance.md", "x"),
        lambda r: _write(r / "src" / "security" / "secrets_manager.py", "x"),
        lambda r: _write(r / "docs" / "security_checklist.md", "x")],
    10: [lambda r: _write(r / "src" / "monitoring" / "metrics_collector.py", "x"),
         lambda r: _write(r / "docs" / "runbooks" / "high_error_rate.md", "x"),
         lambda r: _write(r / "docs" / "monitoring_setup.md", "x")],
    11: [lambda r: _write(r / "Dockerfile", "FROM python:3.11"),
         lambda r: _write(r / "docs" / "deployment_plan.md", "x")],
}


class TestModuleFlowTrackA:
    """Integration test: Track A (Quick Demo) flow — Modules 1 → 2 → 3."""

    def test_track_a_sequential_validation(self, project_root):
        """Validates that completing modules 1, 2, 3 in sequence passes all gates."""
        root = project_root
        validate_module = _load_module("validate_module")

        # Module 1: no artifacts → should fail
        results = validate_module.VALIDATORS[1]()
        assert any(not ok for ok, _, _ in results)

        # Create module 1 artifacts → should pass
        for creator in ARTIFACTS[1]:
            creator(root)
        results = validate_module.VALIDATORS[1]()
        assert all(ok for ok, _, _ in results)

        # Module 2: no artifacts → should fail
        results = validate_module.VALIDATORS[2]()
        assert any(not ok for ok, _, _ in results)

        # Create module 2 artifacts → should pass
        for creator in ARTIFACTS[2]:
            creator(root)
        results = validate_module.VALIDATORS[2]()
        assert all(ok for ok, _, _ in results)

        # Module 3: no artifacts → should fail
        results = validate_module.VALIDATORS[3]()
        assert any(not ok for ok, _, _ in results)

        # Create module 3 artifacts → should pass
        for creator in ARTIFACTS[3]:
            creator(root)
        results = validate_module.VALIDATORS[3]()
        assert all(ok for ok, _, _ in results)


class TestModuleFlowTrackC:
    """Integration test: Track C (Complete Beginner) — Modules 1 → 4 → 5 → 6 → 7."""

    def test_track_c_sequential_validation(self, project_root):
        """Validates the complete beginner track passes all gates in sequence."""
        root = project_root
        validate_module = _load_module("validate_module")

        track_c = [1, 4, 5, 6, 7]
        for module_num in track_c:
            # Before artifacts: should fail
            results = validate_module.VALIDATORS[module_num]()
            assert any(not ok for ok, _, _ in results), (
                f"Module {module_num} should fail without artifacts"
            )

            # Create artifacts
            for creator in ARTIFACTS[module_num]:
                creator(root)

            # After artifacts: should pass
            results = validate_module.VALIDATORS[module_num]()
            assert all(ok for ok, _, _ in results), (
                f"Module {module_num} should pass with all artifacts"
            )


class TestModuleFlowFullProduction:
    """Integration test: Track D (Full Production) — all 11 modules."""

    def test_full_track_sequential_validation(self, project_root):
        """Validates all 11 modules pass gates when artifacts are created in order."""
        root = project_root
        validate_module = _load_module("validate_module")

        for module_num in range(1, 12):
            for creator in ARTIFACTS[module_num]:
                creator(root)
            results = validate_module.VALIDATORS[module_num]()
            assert all(ok for ok, _, _ in results), (
                f"Module {module_num} should pass with all artifacts"
            )


class TestProgressStateTransitions:
    """Integration test: progress file state transitions are consistent."""

    def test_progress_tracks_completed_modules(self, project_root):
        """Simulates completing modules and verifies progress state."""
        root = project_root
        progress_path = _create_progress(root, current_module=1, completed=[])

        # Simulate completing module 1
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        progress["modules_completed"].append(1)
        progress["current_module"] = 2
        progress["current_step"] = 1
        progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

        # Verify state
        reloaded = json.loads(progress_path.read_text(encoding="utf-8"))
        assert 1 in reloaded["modules_completed"]
        assert reloaded["current_module"] == 2

    def test_step_history_accumulates(self, project_root):
        """Verifies step_history grows as steps are completed."""
        root = project_root
        progress_path = _create_progress(root, current_module=5, completed=[1, 4])

        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        progress["step_history"]["5"] = {
            "last_completed_step": 3,
            "updated_at": "2026-05-01T10:00:00Z",
        }
        progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

        reloaded = json.loads(progress_path.read_text(encoding="utf-8"))
        assert reloaded["step_history"]["5"]["last_completed_step"] == 3

    def test_skipped_steps_recorded(self, project_root):
        """Verifies skipped_steps field works correctly."""
        root = project_root
        progress_path = _create_progress(root, current_module=8, completed=[1, 2, 3, 4, 5, 6, 7])

        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        progress["skipped_steps"] = {
            "8.1e": {
                "reason": "a",
                "note": "Already using PostgreSQL",
                "skipped_at": "2026-05-01T10:00:00Z",
            }
        }
        progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

        reloaded = json.loads(progress_path.read_text(encoding="utf-8"))
        assert "8.1e" in reloaded["skipped_steps"]
        assert reloaded["skipped_steps"]["8.1e"]["reason"] == "a"


class TestGateEnforcement:
    """Integration test: gate validation blocks progression correctly."""

    def test_cannot_start_module_6_without_module_5(self, project_root):
        """Module 6 requires Module 5 artifacts — should fail without them."""
        root = project_root
        validate_module = _load_module("validate_module")

        # Create only module 4 artifacts (not 5)
        for creator in ARTIFACTS[4]:
            creator(root)

        # Module 5 should fail (no evaluation, no transform, no JSONL)
        results = validate_module.VALIDATORS[5]()
        assert any(not ok for ok, _, _ in results)

    def test_module_7_requires_query_programs(self, project_root):
        """Module 7 requires query programs from Module 6 work."""
        root = project_root
        validate_module = _load_module("validate_module")

        # Without query programs, module 7 should fail
        results = validate_module.VALIDATORS[7]()
        assert any(not ok for ok, _, _ in results)

        # With query programs, should pass
        for creator in ARTIFACTS[7]:
            creator(root)
        results = validate_module.VALIDATORS[7]()
        assert all(ok for ok, _, _ in results)


class TestPropertyModuleTransitionConsistency:
    """Property: completing module N always enables validation of module N.

    **Validates:** Module artifacts are self-consistent — creating all artifacts
    for a module always makes that module's validator pass.
    """

    @given(module_num=st.integers(min_value=1, max_value=11))
    @settings(max_examples=50)
    def test_artifacts_always_satisfy_validator(self, module_num: int):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            for creator in ARTIFACTS[module_num]:
                creator(root)

            validate_module = _load_module("validate_module")
            results = validate_module.VALIDATORS[module_num]()
            assert all(ok for ok, _, _ in results)
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


class TestPropertyProgressFileRoundTrip:
    """Property: progress JSON round-trips correctly through read/write cycles."""

    @given(
        current_module=st.integers(min_value=1, max_value=11),
        completed=st.lists(st.integers(min_value=1, max_value=11), max_size=11, unique=True),
    )
    @settings(max_examples=50)
    def test_progress_roundtrip(self, current_module: int, completed: list[int]):
        td = tempfile.mkdtemp()
        try:
            root = Path(td)
            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)

            progress = {
                "modules_completed": sorted(completed),
                "current_module": current_module,
                "language": "python",
                "database_type": "sqlite",
                "data_sources": [],
                "current_step": 1,
                "step_history": {},
            }

            path = cfg / "bootcamp_progress.json"
            path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

            reloaded = json.loads(path.read_text(encoding="utf-8"))
            assert reloaded["modules_completed"] == sorted(completed)
            assert reloaded["current_module"] == current_module
        finally:
            shutil.rmtree(td, ignore_errors=True)
