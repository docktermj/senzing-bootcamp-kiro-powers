"""Tests for senzing-bootcamp/scripts/preflight.py.

Note: This file was previously named test_preflight_check.py but tests
the current preflight.py script (preflight_check.py was deprecated and removed).
"""

import importlib
import io
import os
import sys
from collections import namedtuple
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_preflight():
    """Import / reload preflight module, resetting globals."""
    import preflight
    importlib.reload(preflight)
    return preflight


# ---------------------------------------------------------------------------
# Example-based tests  (Task 8.1)
# ---------------------------------------------------------------------------


class TestAllRuntimesMissing:
    """Requirement 8.1 — all runtimes missing → error."""

    def test_no_runtimes_reports_error(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            # Block all language runtimes and tools
            return None

        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=50 * 1024**3, used=20 * 1024**3, free=30 * 1024**3)

        with patch("preflight.shutil.which", side_effect=fake_which):
            with patch("preflight.shutil.disk_usage", return_value=fake_disk):
                exit_code = mod.main([])

        assert exit_code == 1


class TestDiskSpaceBelowThreshold:
    """Requirement 8.2 — disk < 10GB → warning."""

    def test_low_disk_warning(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("python3",):
                return "/usr/bin/python3"
            if cmd == "git":
                return "/usr/bin/git"
            if cmd == "curl":
                return "/usr/bin/curl"
            return None

        # 5GB free
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=20 * 1024**3, used=15 * 1024**3, free=5 * 1024**3)

        with patch("preflight.shutil.which", side_effect=fake_which):
            with patch("preflight.shutil.disk_usage", return_value=fake_disk):
                mod.main([])

        out = capsys.readouterr().out
        assert "5" in out or "⚠" in out


class TestDiskSpaceAboveThreshold:
    """Requirement 8.3 — disk >= 10GB → pass."""

    def test_sufficient_disk_passes(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("python3",):
                return "/usr/bin/python3"
            if cmd == "git":
                return "/usr/bin/git"
            if cmd == "curl":
                return "/usr/bin/curl"
            return None

        # 20GB free
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=50 * 1024**3, used=30 * 1024**3, free=20 * 1024**3)

        with patch("preflight.shutil.which", side_effect=fake_which):
            with patch("preflight.shutil.disk_usage", return_value=fake_disk):
                mod.main([])

        out = capsys.readouterr().out
        assert "20" in out


class TestGetTotalMemoryGb:
    """Requirement 8.4 — check_disk_space returns a CheckResult."""

    def test_disk_check_returns_results(self, project_root):
        mod = _load_preflight()
        results = mod.check_disk_space()
        assert len(results) >= 1
        assert results[0].status in ("pass", "warn")


class TestWritePermissionCheck:
    """Requirement 8.5 — write-permission check creates/removes temp dir."""

    def test_write_permission_creates_and_removes(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("python3",):
                return "/usr/bin/python3"
            if cmd == "git":
                return "/usr/bin/git"
            if cmd == "curl":
                return "/usr/bin/curl"
            return None

        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        fake_disk = DiskUsage(total=50 * 1024**3, used=30 * 1024**3, free=20 * 1024**3)

        with patch("preflight.shutil.which", side_effect=fake_which):
            with patch("preflight.shutil.disk_usage", return_value=fake_disk):
                mod.main([])

        out = capsys.readouterr().out
        assert "Write permissions OK" in out
        # The temp dir should have been cleaned up
        test_dir = project_root / "_preflight_write_test"
        assert not test_dir.exists()
