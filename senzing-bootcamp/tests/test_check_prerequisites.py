"""Tests for senzing-bootcamp/scripts/preflight.py (formerly check_prerequisites.py)."""

import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _load_preflight():
    """Import / reload preflight module, resetting globals."""
    import preflight
    importlib.reload(preflight)
    return preflight


# ---------------------------------------------------------------------------
# Example-based tests  (Task 7.1)
# ---------------------------------------------------------------------------


class TestNoLanguageRuntimes:
    """Requirement 7.3 — no language runtimes → failure."""

    def test_no_runtimes_reports_failure(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            # Block all language runtimes and tools
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            exit_code = mod.main([])

        assert exit_code == 1


class TestNoColorDisablesColor:
    """Requirement 11.4 — NO_COLOR disables colour output."""

    def test_no_color_env(self, project_root, mock_no_color):
        mod = _load_preflight()
        assert mod._color_supported() is False


class TestCheckCommandPresent:
    """Requirement 7.5 — check_required_tools with present command."""

    def test_present_command_increments_passed(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd in ("git", "curl", "zip", "unzip"):
                return f"/usr/bin/{cmd}"
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = mod.check_required_tools()

        # git and curl should pass
        passed = [r for r in results if r.status == "pass"]
        assert len(passed) >= 2


class TestCheckCommandAbsentRequired:
    """Requirement 7.2 — absent required tool → fail."""

    def test_absent_required_increments_failed(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            # All tools missing
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = mod.check_required_tools()

        failed = [r for r in results if r.status == "fail"]
        assert len(failed) >= 1


class TestCheckCommandAbsentOptional:
    """check_language_runtimes with absent optional runtime → no fail for that runtime."""

    def test_absent_optional_increments_warnings(self, project_root, capsys):
        mod = _load_preflight()

        def fake_which(cmd):
            # Only python3 present, others missing
            if cmd == "python3":
                return "/usr/bin/python3"
            if cmd in ("git", "curl"):
                return f"/usr/bin/{cmd}"
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = mod.check_language_runtimes()

        # Should not have a fail for missing optional runtimes
        # (only fails if ALL runtimes are missing)
        failed = [r for r in results if r.status == "fail"]
        assert len(failed) == 0


# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 7.2 & 7.3)
# ---------------------------------------------------------------------------

from hypothesis import given, settings
import hypothesis.strategies as st

# Strategy: random command names
command_names = st.from_regex(r"[a-z][a-z0-9_-]{1,12}", fullmatch=True)

# The five language runtimes checked by preflight.py
LANGUAGE_RUNTIMES = ["python3", "java", "dotnet", "rustc", "node"]


class TestProperty8CheckCommandReflectsAvailability:
    """Property 8: check_required_tools reflects command availability.

    **Validates: Requirements 7.1, 7.2, 7.5**

    For required tools, present → pass status, absent → fail status.
    """

    @given(cmd_name=command_names, required=st.booleans())
    @settings(max_examples=100)
    def test_present_increments_passed(self, cmd_name, required):
        mod = _load_preflight()

        def fake_which(cmd):
            # All tools present
            return f"/usr/bin/{cmd}"

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = mod.check_required_tools()

        passed = [r for r in results if r.status == "pass"]
        assert len(passed) >= 1

    @given(cmd_name=command_names)
    @settings(max_examples=100)
    def test_absent_required_increments_failed(self, cmd_name):
        mod = _load_preflight()

        def fake_which(cmd):
            # All tools missing
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = mod.check_required_tools()

        failed = [r for r in results if r.status == "fail"]
        assert len(failed) >= 1


class TestProperty9LanguageRuntimeDetection:
    """Property 9: Language runtime detection prevents false failure.

    **Validates: Requirements 7.4**

    For any single runtime present while others absent,
    no language failure reported.
    """

    @given(runtime=st.sampled_from(LANGUAGE_RUNTIMES))
    @settings(max_examples=100, deadline=None)
    def test_single_runtime_no_language_failure(self, runtime):
        mod = _load_preflight()

        def fake_which(cmd):
            if cmd == runtime:
                return f"/usr/bin/{cmd}"
            if cmd in ("git", "curl", "zip", "unzip", "pip3", "pip"):
                return f"/usr/bin/{cmd}"
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = mod.check_language_runtimes()

        # Should NOT have a "fail" result about no runtimes
        failed = [r for r in results if r.status == "fail"]
        assert len(failed) == 0
