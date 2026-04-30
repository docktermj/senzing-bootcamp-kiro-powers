"""Unit tests for status.py step-level display.

Tests that status.py correctly shows step info when current_step is present,
omits it when absent or null, and that sync_progress_tracker writes step info
to PROGRESS_TRACKER.md appropriately.
"""

import json
import sys
from io import StringIO
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_progress(tmp_path, data):
    """Write a progress JSON file under tmp_path/config/."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "bootcamp_progress.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def _capture_status_main(tmp_path, monkeypatch):
    """Run status.py main() with cwd set to tmp_path and capture stdout."""
    # Ensure the scripts directory is on sys.path so status can be imported
    scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
    monkeypatch.syspath_prepend(scripts_dir)

    # status.py's main() calls os.chdir(project_root) where project_root is
    # relative to __file__.  We override __file__ inside the module so that
    # project_root resolves to tmp_path.
    import importlib
    import status

    importlib.reload(status)

    # Patch __file__ so Path(__file__).resolve().parent.parent == tmp_path
    fake_script = str(tmp_path / "scripts" / "status.py")
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(status, "__file__", fake_script)

    # Disable colour so assertions are simpler
    monkeypatch.setattr(status, "USE_COLOR", False)

    # Remove --sync from argv to avoid writing tracker during main tests
    monkeypatch.setattr(sys, "argv", ["status.py"])

    buf = StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    status.main()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# main() display tests
# ---------------------------------------------------------------------------


class TestStatusMainStepDisplay:
    """Verify main() output includes/excludes step info based on progress data."""

    def test_displays_step_when_current_step_present(self, tmp_path, monkeypatch):
        """With current_step=3 and current_module=5, output contains 'Step 3'."""
        _write_progress(tmp_path, {
            "modules_completed": [1, 2, 3, 4],
            "current_module": 5,
            "current_step": 3,
            "step_history": {
                "5": {"last_completed_step": 3, "updated_at": "2026-05-12T09:15:00Z"}
            },
            "data_sources": [],
            "database_type": "sqlite",
        })

        output = _capture_status_main(tmp_path, monkeypatch)
        # The "Current Module:" line should contain step info
        current_line = [l for l in output.splitlines() if "Current Module:" in l][0]
        assert "Module 5, Step 3" in current_line

    def test_no_step_when_current_step_absent(self, tmp_path, monkeypatch):
        """Without current_step field, output shows module only — no 'Step'."""
        _write_progress(tmp_path, {
            "modules_completed": [1, 2],
            "current_module": 3,
            "data_sources": [],
            "database_type": "sqlite",
        })

        output = _capture_status_main(tmp_path, monkeypatch)
        current_line = [l for l in output.splitlines() if "Current Module:" in l][0]
        assert "Module 3" in current_line
        assert "Step" not in current_line

    def test_no_step_when_current_step_is_none(self, tmp_path, monkeypatch):
        """With current_step=None, output shows module only — no 'Step'."""
        _write_progress(tmp_path, {
            "modules_completed": [1, 2, 3],
            "current_module": 4,
            "current_step": None,
            "data_sources": [],
            "database_type": "sqlite",
        })

        output = _capture_status_main(tmp_path, monkeypatch)
        current_line = [l for l in output.splitlines() if "Current Module:" in l][0]
        assert "Module 4" in current_line
        assert "Step" not in current_line


    def test_no_step_when_module_completed(self, tmp_path, monkeypatch):
        """When current_module is in modules_completed, step is not shown."""
        _write_progress(tmp_path, {
            "modules_completed": [1, 2, 3, 4, 5],
            "current_module": 5,
            "current_step": 13,
            "data_sources": [],
            "database_type": "sqlite",
        })

        output = _capture_status_main(tmp_path, monkeypatch)
        # current_module is in completed list, so step should NOT display
        current_line = [l for l in output.splitlines() if "Current Module:" in l][0]
        assert "Step" not in current_line


# ---------------------------------------------------------------------------
# sync_progress_tracker() tests
# ---------------------------------------------------------------------------


class TestSyncProgressTracker:
    """Verify sync_progress_tracker writes step info to PROGRESS_TRACKER.md."""

    def test_tracker_contains_step_when_set(self, tmp_path, monkeypatch):
        """sync_progress_tracker with current_step writes step info to tracker."""
        scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
        monkeypatch.syspath_prepend(scripts_dir)

        import importlib
        import status

        importlib.reload(status)
        monkeypatch.setattr(status, "USE_COLOR", False)

        # chdir to tmp_path so the tracker is written there
        monkeypatch.chdir(tmp_path)

        status.sync_progress_tracker(
            completed=[1, 2, 3, 4],
            current=5,
            language="python",
            current_step=3,
        )

        tracker = (tmp_path / "docs" / "guides" / "PROGRESS_TRACKER.md").read_text(
            encoding="utf-8"
        )
        assert "(Step 3)" in tracker

    def test_tracker_no_step_when_not_set(self, tmp_path, monkeypatch):
        """sync_progress_tracker without current_step writes no step info."""
        scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
        monkeypatch.syspath_prepend(scripts_dir)

        import importlib
        import status

        importlib.reload(status)
        monkeypatch.setattr(status, "USE_COLOR", False)

        monkeypatch.chdir(tmp_path)

        status.sync_progress_tracker(
            completed=[1, 2],
            current=3,
            language="python",
        )

        tracker = (tmp_path / "docs" / "guides" / "PROGRESS_TRACKER.md").read_text(
            encoding="utf-8"
        )
        assert "Step" not in tracker
