"""Tests for senzing-bootcamp/scripts/validate_module.py."""

import importlib
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helper: import (or reload) validate_module inside the isolated project_root
# ---------------------------------------------------------------------------

def _load_validate_module():
    """Import / reload validate_module so it picks up the current cwd."""
    import validate_module
    importlib.reload(validate_module)
    return validate_module


# ---------------------------------------------------------------------------
# Artifact creators — create the on-disk artifacts each validator expects
# ---------------------------------------------------------------------------

# Mapping: module number → list of callables that create required artifacts
ARTIFACT_CREATORS = {
    1: [
        lambda r: _write(r / "docs" / "business_problem.md", "problem"),
    ],
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
    9: [
        lambda r: _write(r / "docs" / "security_compliance.md", "x"),
        lambda r: _write(r / "src" / "security" / "secrets_manager.py", "x"),
        lambda r: _write(r / "docs" / "security_checklist.md", "x"),
    ],
    10: [
        lambda r: _write(r / "src" / "monitoring" / "metrics_collector.py", "x"),
        lambda r: _write(r / "docs" / "runbooks" / "high_error_rate.md", "x"),
        lambda r: _write(r / "docs" / "monitoring_setup.md", "x"),
    ],
    11: [
        lambda r: _write(r / "Dockerfile", "FROM python:3.11"),
        lambda r: _write(r / "docs" / "deployment_plan.md", "x"),
    ],
}


def _write(path: Path, content: str):
    """Write content to path, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_all_artifacts(root, module_num):
    """Create all required artifacts for a module."""
    for creator in ARTIFACT_CREATORS[module_num]:
        creator(root)


# ---------------------------------------------------------------------------
# Example-based tests  (Task 4.1)
# ---------------------------------------------------------------------------


class TestValidatorsDict:
    """Requirement 4.5 — VALIDATORS has keys 1-11."""

    def test_validators_has_all_11_keys(self, project_root):
        mod = _load_validate_module()
        assert set(mod.VALIDATORS.keys()) == set(range(1, 12))


class TestCheckFileNotEmpty:
    """Requirement 4.6 — check_file_not_empty fails on empty file."""

    def test_empty_file_fails(self, project_root):
        empty = project_root / "empty.txt"
        empty.write_text("", encoding="utf-8")
        mod = _load_validate_module()
        ok, desc, detail = mod.check_file_not_empty(str(empty), "test")
        assert ok is False
        assert "empty" in detail

    def test_nonempty_file_passes(self, project_root):
        f = project_root / "nonempty.txt"
        f.write_text("content", encoding="utf-8")
        mod = _load_validate_module()
        ok, desc, detail = mod.check_file_not_empty(str(f), "test")
        assert ok is True

    def test_missing_file_fails(self, project_root):
        mod = _load_validate_module()
        ok, desc, detail = mod.check_file_not_empty("nonexistent.txt", "test")
        assert ok is False
        assert "not found" in detail


class TestCheckDirHasFiles:
    """Requirement 11.3 — check_dir_has_files fails on empty dir."""

    def test_empty_dir_fails(self, project_root):
        d = project_root / "emptydir"
        d.mkdir()
        mod = _load_validate_module()
        ok, desc, detail = mod.check_dir_has_files(str(d), "*.txt", "test")
        assert ok is False
        assert "No" in detail

    def test_dir_with_matching_files_passes(self, project_root):
        d = project_root / "filedir"
        d.mkdir()
        (d / "a.txt").write_text("x", encoding="utf-8")
        mod = _load_validate_module()
        ok, desc, detail = mod.check_dir_has_files(str(d), "*.txt", "test")
        assert ok is True

    def test_missing_dir_fails(self, project_root):
        mod = _load_validate_module()
        ok, desc, detail = mod.check_dir_has_files("no_such_dir", "*.*", "test")
        assert ok is False


class TestNextOne:
    """Requirement 4.4 — --next 1 reports no prerequisites."""

    def test_next_1_no_prerequisites(self, project_root, capsys):
        mod = _load_validate_module()
        with patch.object(sys, "argv", ["validate_module.py", "--next", "1"]):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "no prerequisites" in out.lower() or "start anytime" in out.lower()


class TestNextNValidatesPrevious:
    """Requirement 4.3 — --next N validates module N-1."""

    def test_next_3_validates_module_2(self, project_root, capsys):
        # Create module 2 artifacts so validation passes
        _create_all_artifacts(project_root, 2)
        mod = _load_validate_module()
        with patch.object(sys, "argv", ["validate_module.py", "--next", "3"]):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()
        assert exc_info.value.code == 0



# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 4.2 & 4.3)
# ---------------------------------------------------------------------------

from hypothesis import given, settings
import hypothesis.strategies as st


class TestProperty5ValidatorPassesOnCompleteArtifacts:
    """Property 5: Module validator passes on complete artifacts.

    **Validates: Requirements 4.1**

    For any module 1-11 with all artifacts present,
    all results have ok=True.
    """

    # Feature: script-test-suite, Property 5: Module validator passes on complete artifacts

    @given(module_num=st.integers(min_value=1, max_value=11))
    @settings(max_examples=100)
    def test_all_pass_when_artifacts_present(self, module_num):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            _create_all_artifacts(root, module_num)

            mod = _load_validate_module()
            results = mod.VALIDATORS[module_num]()

            for ok, desc, detail in results:
                assert ok is True, (
                    f"Module {module_num}: '{desc}' failed with detail='{detail}'"
                )
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


class TestProperty6ValidatorFailsOnMissingArtifacts:
    """Property 6: Module validator fails on missing artifacts.

    **Validates: Requirements 4.2**

    For any module 1-11 with artifacts absent,
    at least one result has ok=False.
    """

    # Feature: script-test-suite, Property 6: Module validator fails on missing artifacts

    @given(module_num=st.integers(min_value=1, max_value=11))
    @settings(max_examples=100)
    def test_at_least_one_fails_when_artifacts_absent(self, module_num):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)

            mod = _load_validate_module()
            results = mod.VALIDATORS[module_num]()

            has_failure = any(not ok for ok, desc, detail in results)
            assert has_failure, (
                f"Module {module_num}: expected at least one failure "
                f"when no artifacts exist, but all passed"
            )
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)
