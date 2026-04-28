"""Tests for senzing-bootcamp/scripts/backup_project.py."""

import importlib
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_backup():
    """Import / reload backup_project module."""
    import backup_project
    importlib.reload(backup_project)
    return backup_project


# ---------------------------------------------------------------------------
# Example-based tests  (Task 5.1)
# ---------------------------------------------------------------------------


class TestBackupCreatesValidZip:
    """Requirement 5.1 — backup creates a valid ZIP archive."""

    def test_backup_creates_zip(self, project_root, capsys):
        # Create some project files
        (project_root / "database").mkdir()
        (project_root / "database" / "G2C.db").write_text("data", encoding="utf-8")
        (project_root / "docs").mkdir()
        (project_root / "docs" / "README.md").write_text("hello", encoding="utf-8")

        mod = _load_backup()
        # Patch __file__ so project_root resolves correctly
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "backup_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            mod.main()

        backups_dir = project_root / "backups"
        zips = list(backups_dir.glob("*.zip"))
        assert len(zips) == 1
        assert zipfile.is_zipfile(zips[0])


class TestBackupMissingItemsSkipped:
    """Requirement 5.4 — missing item directories are skipped."""

    def test_missing_dirs_skipped(self, project_root, capsys):
        # Only create 'docs', skip everything else
        (project_root / "docs").mkdir()
        (project_root / "docs" / "test.md").write_text("x", encoding="utf-8")

        mod = _load_backup()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "backup_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            mod.main()

        out = capsys.readouterr().out
        assert "not found, skipping" in out

        # ZIP should still be created
        backups_dir = project_root / "backups"
        zips = list(backups_dir.glob("*.zip"))
        assert len(zips) == 1


class TestBackupContainsExpectedFiles:
    """Requirement 5.1 — backup contains expected files."""

    def test_zip_contains_files(self, project_root, capsys):
        (project_root / "src").mkdir()
        (project_root / "src" / "main.py").write_text("print('hi')", encoding="utf-8")
        (project_root / "docs").mkdir()
        (project_root / "docs" / "guide.md").write_text("guide", encoding="utf-8")

        mod = _load_backup()
        fake_scripts = project_root / "scripts"
        fake_scripts.mkdir(exist_ok=True)
        fake_init = fake_scripts / "backup_project.py"
        fake_init.write_text("", encoding="utf-8")

        with patch.object(mod, "__file__", str(fake_init)):
            mod.main()

        backups_dir = project_root / "backups"
        zips = list(backups_dir.glob("*.zip"))
        with zipfile.ZipFile(zips[0], "r") as zf:
            names = zf.namelist()
        assert "src/main.py" in names
        assert "docs/guide.md" in names


class TestIsExcluded:
    """Requirement 5.2, 5.3 — _is_excluded filter."""

    def test_pycache_excluded(self, project_root):
        mod = _load_backup()
        assert mod._is_excluded("src/__pycache__/foo.pyc") is True

    def test_git_excluded(self, project_root):
        mod = _load_backup()
        assert mod._is_excluded(".git/config") is True

    def test_env_excluded(self, project_root):
        mod = _load_backup()
        assert mod._is_excluded(".env") is True

    def test_normal_file_not_excluded(self, project_root):
        mod = _load_backup()
        assert mod._is_excluded("src/main.py") is False

    def test_docs_not_excluded(self, project_root):
        mod = _load_backup()
        assert mod._is_excluded("docs/guide.md") is False


# ---------------------------------------------------------------------------
# Property-based tests  (Task 5.2)
# ---------------------------------------------------------------------------

from hypothesis import given, settings, assume
import hypothesis.strategies as st

# Strategy: generate path components that match exclusion patterns
# Note: "data/temp" is excluded because it's a multi-component pattern
# that _is_excluded checks differently (per-part matching)
excluded_components = st.sampled_from([
    "__pycache__", ".git", "node_modules", "venv", ".venv",
    "target", "bin", "obj", "dist", ".history", "backups",
])

# Strategy: generate clean path components (no exclusion match)
clean_components = st.from_regex(r"[a-z]{2,8}", fullmatch=True).filter(
    lambda s: s not in {
        "target", "bin", "obj", "dist", "backups", "venv",
    }
)

clean_filenames = st.from_regex(r"[a-z]{2,8}\.[a-z]{2,4}", fullmatch=True).filter(
    lambda s: not s.endswith((".pyc", ".swp", ".swo", ".env"))
    and "~" not in s
    and s != ".DS_Store"
)


class TestProperty7ExclusionFilterCorrectness:
    """Property 7: Exclusion filter correctness.

    **Validates: Requirements 5.2, 5.3**

    For any path with an excluded component, _is_excluded returns True.
    For any clean path, _is_excluded returns False.
    """

    # Feature: script-test-suite, Property 7: Exclusion filter correctness

    @given(
        prefix=st.lists(clean_components, min_size=0, max_size=2),
        excluded=excluded_components,
        suffix=clean_filenames,
    )
    @settings(max_examples=100)
    def test_excluded_component_detected(self, prefix, excluded, suffix):
        parts = prefix + [excluded, suffix]
        path = os.path.join(*parts) if len(parts) > 1 else parts[0]
        mod = _load_backup()
        assert mod._is_excluded(path) is True, (
            f"Expected _is_excluded('{path}') to be True"
        )

    @given(
        components=st.lists(clean_components, min_size=1, max_size=3),
        filename=clean_filenames,
    )
    @settings(max_examples=100)
    def test_clean_path_not_excluded(self, components, filename):
        path = os.path.join(*components, filename)
        mod = _load_backup()
        assert mod._is_excluded(path) is False, (
            f"Expected _is_excluded('{path}') to be False"
        )
