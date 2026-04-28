"""Tests for senzing-bootcamp/scripts/preflight_check.py."""

import importlib
import io
import os
import sys
from collections import namedtuple
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_preflight():
    """Import / reload preflight_check module, resetting globals."""
    import preflight_check
    importlib.reload(preflight_check)
    return preflight_check


# ---------------------------------------------------------------------------
# Example-based tests  (Task 8.1)
# ---------------------------------------------------------------------------


class TestAllRuntimesMissing:
    """Requirement 8.1 — all runtimes missing → error."""

    def test_no_runtimes_reports_error(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            # Block all language runtimes
            if cmd in ("python3", "python", "java", "dotnet", "rustc", "node", "git", "psql"):
                return None
            return None

        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=50 * 1024**3, used=20 * 1024**3, free=30 * 1024**3)

        with patch("preflight_check.shutil.which", side_effect=fake_which):
            with patch("preflight_check.shutil.disk_usage", return_value=fake_disk):
                with patch("preflight_check.get_version", return_value="1.0"):
                    with pytest.raises(SystemExit) as exc_info:
                        mod.main()

        assert exc_info.value.code == 1
        assert mod.ERRORS > 0


class TestDiskSpaceBelowThreshold:
    """Requirement 8.2 — disk < 10GB → warning."""

    def test_low_disk_warning(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("python3",):
                return "/usr/bin/python3"
            if cmd == "git":
                return "/usr/bin/git"
            return None

        # 5GB free
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=20 * 1024**3, used=15 * 1024**3, free=5 * 1024**3)

        with patch("preflight_check.shutil.which", side_effect=fake_which):
            with patch("preflight_check.shutil.disk_usage", return_value=fake_disk):
                with patch("preflight_check.get_version", return_value="3.11"):
                    with patch("preflight_check._get_total_memory_gb", return_value=16.0):
                        try:
                            mod.main()
                        except SystemExit:
                            pass

        out = capsys.readouterr().out
        assert "5" in out or "⚠" in out
        assert mod.WARNINGS > 0


class TestDiskSpaceAboveThreshold:
    """Requirement 8.3 — disk >= 10GB → pass."""

    def test_sufficient_disk_passes(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("python3",):
                return "/usr/bin/python3"
            if cmd == "git":
                return "/usr/bin/git"
            return None

        # 20GB free
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=50 * 1024**3, used=30 * 1024**3, free=20 * 1024**3)

        with patch("preflight_check.shutil.which", side_effect=fake_which):
            with patch("preflight_check.shutil.disk_usage", return_value=fake_disk):
                with patch("preflight_check.get_version", return_value="3.11"):
                    with patch("preflight_check._get_total_memory_gb", return_value=16.0):
                        try:
                            mod.main()
                        except SystemExit:
                            pass

        out = capsys.readouterr().out
        assert "20GB available" in out or "20" in out


class TestGetTotalMemoryGb:
    """Requirement 8.4 — _get_total_memory_gb returns numeric or None."""

    def test_returns_numeric_or_none(self, project_root):
        mod = _load_preflight()
        result = mod._get_total_memory_gb()
        assert result is None or isinstance(result, (int, float))


class TestWritePermissionCheck:
    """Requirement 8.5 — write-permission check creates/removes temp dir."""

    def test_write_permission_creates_and_removes(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("python3",):
                return "/usr/bin/python3"
            return None

        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=50 * 1024**3, used=30 * 1024**3, free=20 * 1024**3)

        with patch("preflight_check.shutil.which", side_effect=fake_which):
            with patch("preflight_check.shutil.disk_usage", return_value=fake_disk):
                with patch("preflight_check.get_version", return_value="3.11"):
                    with patch("preflight_check._get_total_memory_gb", return_value=16.0):
                        try:
                            mod.main()
                        except SystemExit:
                            pass

        out = capsys.readouterr().out
        assert "Write permissions OK" in out
        # The temp dir should have been cleaned up
        test_dir = project_root / "_preflight_test"
        assert not test_dir.exists()
