"""Unit tests for step detection and repair output in repair_progress.py.

Tests detect_steps() with various artifact combinations, main --fix populates
step data, and main --fix omits step when undetermined.
"""

import importlib
import json
import sys
from io import StringIO
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_repair_module(tmp_path, monkeypatch):
    """Import (or reload) repair_progress with cwd set to tmp_path."""
    scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
    monkeypatch.syspath_prepend(scripts_dir)
    monkeypatch.chdir(tmp_path)

    import repair_progress
    importlib.reload(repair_progress)

    # Patch PROGRESS / PREFS to live under tmp_path
    monkeypatch.setattr(repair_progress, "PROGRESS",
                        tmp_path / "config" / "bootcamp_progress.json")
    monkeypatch.setattr(repair_progress, "PREFS",
                        tmp_path / "config" / "bootcamp_preferences.yaml")
    return repair_progress


def _create_artifact(tmp_path, rel_path, content="x"):
    """Create a file at tmp_path / rel_path with some content."""
    p = tmp_path / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# detect_steps() tests
# ---------------------------------------------------------------------------


class TestDetectSteps:
    """Verify detect_steps maps artifacts to correct step numbers."""

    def test_empty_project_returns_empty(self, tmp_path, monkeypatch):
        """No artifacts → empty dict."""
        rp = _get_repair_module(tmp_path, monkeypatch)
        assert rp.detect_steps() == {}

    def test_module1_business_problem(self, tmp_path, monkeypatch):
        """docs/business_problem.md → module 1 step 10."""
        _create_artifact(tmp_path, "docs/business_problem.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[1] == 10

    def test_module2_database(self, tmp_path, monkeypatch):
        """database/G2C.db → module 2 step 6."""
        _create_artifact(tmp_path, "database/G2C.db")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[2] == 6

    def test_module3_quickstart(self, tmp_path, monkeypatch):
        """src/quickstart_demo/ with files → module 3 step 4."""
        _create_artifact(tmp_path, "src/quickstart_demo/demo.py")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[3] == 4

    def test_module4_raw_data(self, tmp_path, monkeypatch):
        """data/raw/ with data files → module 4 step 3."""
        _create_artifact(tmp_path, "data/raw/sample.csv")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[4] == 3

    def test_module5_evaluation_only(self, tmp_path, monkeypatch):
        """docs/data_source_evaluation.md only → module 5 step 7."""
        _create_artifact(tmp_path, "docs/data_source_evaluation.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[5] == 7

    def test_module5_transform_files(self, tmp_path, monkeypatch):
        """src/transform/ has files → module 5 step 11."""
        _create_artifact(tmp_path, "src/transform/mapper.py")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[5] == 11

    def test_module5_transformed_jsonl(self, tmp_path, monkeypatch):
        """data/transformed/*.jsonl → module 5 step 12 (highest)."""
        _create_artifact(tmp_path, "data/transformed/output.jsonl")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[5] == 12

    def test_module5_all_artifacts_picks_highest(self, tmp_path, monkeypatch):
        """All module 5 artifacts present → picks step 12 (most complete)."""
        _create_artifact(tmp_path, "docs/data_source_evaluation.md")
        _create_artifact(tmp_path, "src/transform/mapper.py")
        _create_artifact(tmp_path, "data/transformed/output.jsonl")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[5] == 12

    def test_module6_load(self, tmp_path, monkeypatch):
        """src/load/ has files → module 6 step 5."""
        _create_artifact(tmp_path, "src/load/loader.py")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[6] == 5

    def test_module8_query_only(self, tmp_path, monkeypatch):
        """src/query/ has files → module 8 step 4."""
        _create_artifact(tmp_path, "src/query/search.py")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[8] == 4

    def test_module8_results_validation(self, tmp_path, monkeypatch):
        """docs/results_validation.md → module 8 step 7 (higher priority)."""
        _create_artifact(tmp_path, "src/query/search.py")
        _create_artifact(tmp_path, "docs/results_validation.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[8] == 7

    def test_module9_performance(self, tmp_path, monkeypatch):
        """docs/performance_report.md → module 9 step 6."""
        _create_artifact(tmp_path, "docs/performance_report.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[9] == 6

    def test_module10_security(self, tmp_path, monkeypatch):
        """docs/security_checklist.md → module 10 step 6."""
        _create_artifact(tmp_path, "docs/security_checklist.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[10] == 6

    def test_module11_dockerfile(self, tmp_path, monkeypatch):
        """Dockerfile → module 11 step 5."""
        _create_artifact(tmp_path, "Dockerfile")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[11] == 5

    def test_module11_docker_compose(self, tmp_path, monkeypatch):
        """docker-compose.yml → module 11 step 5."""
        _create_artifact(tmp_path, "docker-compose.yml")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps[11] == 5

    def test_multiple_modules_detected(self, tmp_path, monkeypatch):
        """Multiple artifacts → multiple modules in result."""
        _create_artifact(tmp_path, "docs/business_problem.md")
        _create_artifact(tmp_path, "database/G2C.db")
        _create_artifact(tmp_path, "src/load/loader.py")
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert steps == {1: 10, 2: 6, 6: 5}

    def test_module_without_step_artifacts_omitted(self, tmp_path, monkeypatch):
        """Module 7 and 11 have no step-level artifact mapping → omitted."""
        # Module 11 detection uses monitoring/ dir, but detect_steps has no mapping
        (tmp_path / "monitoring").mkdir()
        rp = _get_repair_module(tmp_path, monkeypatch)
        steps = rp.detect_steps()
        assert 7 not in steps
        assert 11 not in steps


# ---------------------------------------------------------------------------
# main() --fix step integration tests
# ---------------------------------------------------------------------------


class TestMainFixStepData:
    """Verify main --fix populates step data in the progress file."""

    def test_fix_populates_step_history(self, tmp_path, monkeypatch):
        """--fix writes step_history for modules with detected steps."""
        _create_artifact(tmp_path, "docs/business_problem.md")
        _create_artifact(tmp_path, "database/G2C.db")
        rp = _get_repair_module(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["repair_progress.py", "--fix"])
        monkeypatch.setattr(sys, "stdout", StringIO())

        rp.main()

        prog = json.loads(
            (tmp_path / "config" / "bootcamp_progress.json").read_text()
        )
        assert "step_history" in prog
        assert prog["step_history"]["1"]["last_completed_step"] == 10
        assert prog["step_history"]["2"]["last_completed_step"] == 6
        assert "updated_at" in prog["step_history"]["1"]

    def test_fix_sets_current_step_when_determinable(self, tmp_path, monkeypatch):
        """--fix sets current_step when current module has a detected step."""
        # Modules 1,2 completed → current_module = 3
        _create_artifact(tmp_path, "docs/business_problem.md")
        _create_artifact(tmp_path, "database/G2C.db")
        _create_artifact(tmp_path, "src/quickstart_demo/demo.py")
        rp = _get_repair_module(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["repair_progress.py", "--fix"])
        monkeypatch.setattr(sys, "stdout", StringIO())

        rp.main()

        prog = json.loads(
            (tmp_path / "config" / "bootcamp_progress.json").read_text()
        )
        # current_module should be 4 (max completed=3, so 3+1=4)
        # Module 4 has no artifacts → current_step omitted
        # But module 3 has step 4 in step_history
        assert prog["step_history"]["3"]["last_completed_step"] == 4

    def test_fix_omits_current_step_when_undetermined(self, tmp_path, monkeypatch):
        """--fix omits current_step when current module has no step artifacts."""
        # Only module 1 artifact → current_module = 2
        _create_artifact(tmp_path, "docs/business_problem.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["repair_progress.py", "--fix"])
        monkeypatch.setattr(sys, "stdout", StringIO())

        rp.main()

        prog = json.loads(
            (tmp_path / "config" / "bootcamp_progress.json").read_text()
        )
        # current_module = 2, but no module 2 step artifacts
        assert "current_step" not in prog

    def test_fix_sets_current_step_for_current_module(self, tmp_path, monkeypatch):
        """--fix sets current_step when current module has step artifacts."""
        # Modules 1-4 completed, module 5 has evaluation doc
        _create_artifact(tmp_path, "docs/business_problem.md")
        _create_artifact(tmp_path, "database/G2C.db")
        _create_artifact(tmp_path, "src/quickstart_demo/demo.py")
        _create_artifact(tmp_path, "data/raw/sample.csv")
        _create_artifact(tmp_path, "docs/data_source_evaluation.md")
        rp = _get_repair_module(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["repair_progress.py", "--fix"])
        monkeypatch.setattr(sys, "stdout", StringIO())

        rp.main()

        prog = json.loads(
            (tmp_path / "config" / "bootcamp_progress.json").read_text()
        )
        # current_module = 5 (modules 1-4 detected, but module 5 also detected
        # so current = min(5+1, 11) = 6)
        # Module 5 has step 7 in step_map, and module 6 has no artifacts
        # So current_module = 6, current_step should be omitted
        # Actually: det = {1,2,3,4,5}, max=5, cur=6
        assert prog["current_module"] == 6
        assert "current_step" not in prog
        # But step_history should have module 5
        assert prog["step_history"]["5"]["last_completed_step"] == 7


# ---------------------------------------------------------------------------
# main() scan report (no --fix) step display tests
# ---------------------------------------------------------------------------


class TestMainScanStepDisplay:
    """Verify scan report includes step info when detected."""

    def test_scan_shows_step_for_detected_modules(self, tmp_path, monkeypatch):
        """Scan report shows '(Step ~N)' for modules with detected steps."""
        _create_artifact(tmp_path, "docs/business_problem.md")
        _create_artifact(tmp_path, "database/G2C.db")
        rp = _get_repair_module(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["repair_progress.py"])

        buf = StringIO()
        monkeypatch.setattr(sys, "stdout", buf)
        rp.main()
        output = buf.getvalue()

        assert "(Step ~10)" in output  # Module 1
        assert "(Step ~6)" in output   # Module 2

    def test_scan_no_step_for_undetected_modules(self, tmp_path, monkeypatch):
        """Scan report does not show step info for modules without artifacts."""
        rp = _get_repair_module(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["repair_progress.py"])

        buf = StringIO()
        monkeypatch.setattr(sys, "stdout", buf)
        rp.main()
        output = buf.getvalue()

        assert "Step ~" not in output
