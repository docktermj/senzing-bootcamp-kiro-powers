"""Tests for senzing-bootcamp/scripts/restore_project.py."""

import importlib
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_restore():
    """Import / reload restore_project module."""
    import restore_project
    importlib.reload(restore_project)
    return restore_project


def _make_zip(directory: Path, zip_path: Path, files: dict[str, str]):
    """Create a ZIP file at *zip_path* containing *files* (name→content)."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


# ---------------------------------------------------------------------------
# Example-based tests  (Task 6.1)
# ---------------------------------------------------------------------------


class TestRestoreValidZip:
    """Requirement 6.1 — valid ZIP extracts all files."""

    def test_valid_zip_extracts_files(self, project_root, capsys):
        # Create a valid ZIP
        zip_path = project_root / "backups" / "test_backup.zip"
        _make_zip(project_root, zip_path, {
            "docs/readme.md": "hello",
            "src/main.py": "print('hi')",
        })

        restore_dir = project_root / "restored"
        restore_dir.mkdir()

        mod = _load_restore()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "restore_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", [
                "restore_project.py", str(zip_path), str(restore_dir)
            ]):
                # Patch input() to avoid interactive prompt
                with patch("builtins.input", return_value="y"):
                    mod.main()

        assert (restore_dir / "docs" / "readme.md").exists()
        assert (restore_dir / "src" / "main.py").exists()
        assert (restore_dir / "docs" / "readme.md").read_text(encoding="utf-8") == "hello"


class TestRestoreMissingFile:
    """Requirement 6.2 — missing file → exit 1."""

    def test_missing_file_exits_1(self, project_root, capsys):
        mod = _load_restore()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "restore_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", [
                "restore_project.py", "/nonexistent/backup.zip"
            ]):
                with pytest.raises(SystemExit) as exc_info:
                    mod.main()
        assert exc_info.value.code == 1


class TestRestoreNonZip:
    """Requirement 6.3 — non-ZIP file → exit 1."""

    def test_non_zip_exits_1(self, project_root, capsys):
        # Create a non-ZIP file
        bad_file = project_root / "not_a_zip.zip"
        bad_file.write_text("this is not a zip", encoding="utf-8")

        mod = _load_restore()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "restore_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", [
                "restore_project.py", str(bad_file)
            ]):
                with pytest.raises(SystemExit) as exc_info:
                    mod.main()
        assert exc_info.value.code == 1


class TestRestoreNoArgs:
    """Requirement 6.4 — no arguments → usage + exit 1."""

    def test_no_args_prints_usage_and_exits(self, project_root, capsys):
        mod = _load_restore()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "restore_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            with patch.object(sys, "argv", ["restore_project.py"]):
                with pytest.raises(SystemExit) as exc_info:
                    mod.main()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "Usage" in out or "usage" in out
