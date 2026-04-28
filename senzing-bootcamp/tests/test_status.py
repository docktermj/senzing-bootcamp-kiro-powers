"""Tests for senzing-bootcamp/scripts/status.py."""

import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helper: import (or reload) status inside the isolated project_root
# ---------------------------------------------------------------------------

def _load_status():
    """Import / reload status module so it picks up the current cwd."""
    import status
    importlib.reload(status)
    return status


# ---------------------------------------------------------------------------
# Example-based tests  (Task 2.1)
# ---------------------------------------------------------------------------


class TestStatusNoProgressFile:
    """Requirement 2.2 — no progress file → 'Not Started'."""

    def test_no_progress_file_reports_not_started(self, project_root, capsys):
        status = _load_status()
        with patch.object(sys, "argv", ["status.py"]):
            with patch("status.Path") as MockPath:
                # We need to run main() but it does os.chdir based on __file__
                # Instead, test the logic directly: when no file exists the
                # default status is "Not Started".
                pass

        # Simpler approach: just invoke main() with patched __file__
        status_mod = _load_status()
        # Patch __file__ resolution so main() chdir's to our tmp dir
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir()
        fake_init = fake_scripts / "status.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(status_mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["status.py"]):
                status_mod.main()

        out = capsys.readouterr().out
        assert "Not Started" in out or "No progress data found" in out


class TestStatusCorruptedJSON:
    """Requirement 2.3 — corrupted JSON → graceful handling."""

    def test_corrupted_json_no_crash(self, project_root, capsys):
        cfg = project_root / "config"
        cfg.mkdir(parents=True)
        (cfg / "bootcamp_progress.json").write_text("{bad json!!", encoding="utf-8")

        status_mod = _load_status()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "status.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(status_mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["status.py"]):
                status_mod.main()

        out = capsys.readouterr().out
        # Should not crash — just show default status
        assert "Status" in out or "Not Started" in out or "Module" in out


class TestStatusAllComplete:
    """Requirement 2.5 — all 12 modules complete → 'Bootcamp Complete'."""

    def test_all_12_complete(self, project_root, write_progress_file, capsys, sample_progress_data):
        data = sample_progress_data(
            modules_completed=list(range(1, 13)),
            current_module=12,
        )
        write_progress_file(data)

        status_mod = _load_status()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "status.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(status_mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["status.py"]):
                status_mod.main()

        out = capsys.readouterr().out
        assert "Bootcamp Complete" in out


class TestStatusSync:
    """Requirement 2.4 — --sync writes PROGRESS_TRACKER.md."""

    def test_sync_writes_tracker(self, project_root, write_progress_file, sample_progress_data, capsys):
        data = sample_progress_data(modules_completed=[1, 2], current_module=3)
        write_progress_file(data)

        status_mod = _load_status()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "status.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(status_mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["status.py", "--sync"]):
                status_mod.main()

        tracker = project_root / "docs" / "guides" / "PROGRESS_TRACKER.md"
        assert tracker.exists()
        content = tracker.read_text(encoding="utf-8")
        assert "✅" in content  # completed modules
        assert "🔄" in content  # current module


class TestStatusEmptyCompleted:
    """Requirement 11.1 — empty modules_completed → not started."""

    def test_empty_modules_completed(self, project_root, write_progress_file, sample_progress_data, capsys):
        data = sample_progress_data(modules_completed=[], current_module=1)
        write_progress_file(data)

        status_mod = _load_status()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "status.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(status_mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["status.py"]):
                status_mod.main()

        out = capsys.readouterr().out
        # With empty completed list, percentage should be 0
        assert "0%" in out or "0/12" in out


class TestStatusNoColor:
    """Requirement 11.4 — NO_COLOR disables colour output."""

    def test_no_color_disables_ansi(self, project_root, mock_no_color, capsys):
        status_mod = _load_status()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "status.py"
        fake_init.write_text("", encoding="utf-8")

        # Reload so color_supported() picks up NO_COLOR
        importlib.reload(status_mod)

        with patch.object(status_mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["status.py"]):
                status_mod.main()

        out = capsys.readouterr().out
        # ANSI escape codes should be absent
        assert "\033[" not in out


# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 2.2 & 2.3)
# ---------------------------------------------------------------------------

import tempfile
import shutil

from hypothesis import given, settings
import hypothesis.strategies as st


# Strategy: any subset of {1..12}
module_subsets = st.lists(
    st.integers(min_value=1, max_value=12), unique=True, max_size=12
).map(sorted)


class TestProperty1StatusComputation:
    """Property 1: Status computation correctness.

    **Validates: Requirements 2.1**

    For any subset of {1..12} as completed modules, verify
    percentage = len(completed)*100//12 and correct status label.
    """

    # Feature: script-test-suite, Property 1: Status computation correctness

    @given(completed=module_subsets)
    @settings(max_examples=100)
    def test_percentage_and_label(self, completed):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)

            # Write progress file
            cfg = Path(td) / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            current = min(max(completed) + 1, 12) if completed else 1
            data = {
                "modules_completed": completed,
                "current_module": current,
                "language": "python",
                "database_type": "sqlite",
                "data_sources": [],
            }
            (cfg / "bootcamp_progress.json").write_text(
                json.dumps(data), encoding="utf-8"
            )

            status_mod = _load_status()
            fake_scripts = Path(td) / "scripts"
            fake_scripts.mkdir(exist_ok=True)
            (fake_scripts / "status.py").write_text("", encoding="utf-8")

            import io
            captured = io.StringIO()
            with patch.object(status_mod, "__file__", str(fake_scripts / "status.py")):
                with patch.object(sys, "argv", ["status.py"]):
                    with patch("sys.stdout", captured):
                        status_mod.main()

            out = captured.getvalue()
            expected_pct = len(completed) * 100 // 12

            # Verify percentage appears in output
            assert f"{expected_pct}%" in out

            # Verify status label
            if len(completed) == 0:
                assert "0/12" in out
            elif len(completed) == 12:
                assert "Bootcamp Complete" in out
            else:
                assert f"{len(completed)}/12" in out
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


class TestProperty2SyncTrackerReflectsProgress:
    """Property 2: Sync tracker reflects progress data.

    **Validates: Requirements 2.4**

    For any valid completed set and current module,
    sync_progress_tracker produces correct ✅/🔄/⬜ markers.
    """

    # Feature: script-test-suite, Property 2: Sync tracker reflects progress data

    @given(
        completed=module_subsets,
        current=st.integers(min_value=1, max_value=12),
    )
    @settings(max_examples=100)
    def test_sync_markers(self, completed, current):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)

            status_mod = _load_status()
            status_mod.sync_progress_tracker(completed, current, "python")

            tracker = Path(td) / "docs" / "guides" / "PROGRESS_TRACKER.md"
            assert tracker.exists()
            content = tracker.read_text(encoding="utf-8")

            for m in range(1, 13):
                if m in completed:
                    assert f"✅ Module {m}:" in content, f"Module {m} should be ✅"
                elif m == current:
                    assert f"🔄 Module {m}:" in content, f"Module {m} should be 🔄"
                else:
                    assert f"⬜ Module {m}:" in content, f"Module {m} should be ⬜"
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)
