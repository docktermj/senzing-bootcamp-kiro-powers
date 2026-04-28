"""Tests for senzing-bootcamp/scripts/check_prerequisites.py."""

import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _load_check_prereqs():
    """Import / reload check_prerequisites module, resetting globals."""
    import check_prerequisites
    importlib.reload(check_prerequisites)
    return check_prerequisites


# ---------------------------------------------------------------------------
# Example-based tests  (Task 7.1)
# ---------------------------------------------------------------------------


class TestNoLanguageRuntimes:
    """Requirement 7.3 — no language runtimes → failure."""

    def test_no_runtimes_reports_failure(self, project_root, capsys):
        mod = _load_check_prereqs()

        def fake_which(cmd):
            # Allow core tools but block all language runtimes
            if cmd in ("git", "curl", "zip", "unzip"):
                return f"/usr/bin/{cmd}"
            return None

        with patch("check_prerequisites.shutil.which", side_effect=fake_which):
            with patch("check_prerequisites.get_version", return_value="1.0"):
                with pytest.raises(SystemExit) as exc_info:
                    mod.main()

        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "No supported language runtime" in out or mod.FAILED > 0


class TestNoColorDisablesColor:
    """Requirement 11.4 — NO_COLOR disables colour output."""

    def test_no_color_env(self, project_root, mock_no_color):
        mod = _load_check_prereqs()
        assert mod.USE_COLOR is False


class TestCheckCommandPresent:
    """Requirement 7.5 — check_command with present command."""

    def test_present_command_increments_passed(self, project_root, capsys):
        mod = _load_check_prereqs()
        mod.PASSED = 0
        mod.FAILED = 0
        mod.WARNINGS = 0

        with patch("check_prerequisites.shutil.which", return_value="/usr/bin/git"):
            with patch("check_prerequisites.get_version", return_value="2.40"):
                result = mod.check_command("git", "Git", True, "install git")

        assert result is True
        assert mod.PASSED == 1
        assert mod.FAILED == 0


class TestCheckCommandAbsentRequired:
    """Requirement 7.2 — check_command with absent required command."""

    def test_absent_required_increments_failed(self, project_root, capsys):
        mod = _load_check_prereqs()
        mod.PASSED = 0
        mod.FAILED = 0
        mod.WARNINGS = 0

        with patch("check_prerequisites.shutil.which", return_value=None):
            result = mod.check_command("missing", "Missing Tool", True, "install it")

        assert result is False
        assert mod.FAILED == 1
        assert mod.PASSED == 0


class TestCheckCommandAbsentOptional:
    """check_command with absent optional command → warning."""

    def test_absent_optional_increments_warnings(self, project_root, capsys):
        mod = _load_check_prereqs()
        mod.PASSED = 0
        mod.FAILED = 0
        mod.WARNINGS = 0

        with patch("check_prerequisites.shutil.which", return_value=None):
            result = mod.check_command("jq", "jq", False, "install jq")

        assert result is False
        assert mod.WARNINGS == 1
        assert mod.FAILED == 0



# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 7.2 & 7.3)
# ---------------------------------------------------------------------------

from hypothesis import given, settings
import hypothesis.strategies as st

# Strategy: random command names
command_names = st.from_regex(r"[a-z][a-z0-9_-]{1,12}", fullmatch=True)

# The five language runtimes checked by check_prerequisites.py
LANGUAGE_RUNTIMES = ["python3", "java", "dotnet", "rustc", "node"]


class TestProperty8CheckCommandReflectsAvailability:
    """Property 8: check_command reflects command availability.

    **Validates: Requirements 7.1, 7.2, 7.5**

    For any command name, present → PASSED incremented,
    absent + required → FAILED incremented.
    """

    # Feature: script-test-suite, Property 8: check_command reflects availability

    @given(cmd_name=command_names, required=st.booleans())
    @settings(max_examples=100)
    def test_present_increments_passed(self, cmd_name, required):
        mod = _load_check_prereqs()
        mod.PASSED = 0
        mod.FAILED = 0
        mod.WARNINGS = 0

        with patch("check_prerequisites.shutil.which", return_value=f"/usr/bin/{cmd_name}"):
            with patch("check_prerequisites.get_version", return_value="1.0"):
                mod.check_command(cmd_name, cmd_name.title(), required, "install it")

        assert mod.PASSED == 1
        assert mod.FAILED == 0

    @given(cmd_name=command_names)
    @settings(max_examples=100)
    def test_absent_required_increments_failed(self, cmd_name):
        mod = _load_check_prereqs()
        mod.PASSED = 0
        mod.FAILED = 0
        mod.WARNINGS = 0

        with patch("check_prerequisites.shutil.which", return_value=None):
            mod.check_command(cmd_name, cmd_name.title(), True, "install it")

        assert mod.FAILED == 1
        assert mod.PASSED == 0


class TestProperty9LanguageRuntimeDetection:
    """Property 9: Language runtime detection prevents false failure.

    **Validates: Requirements 7.4**

    For any single runtime present while others absent,
    no language failure reported.
    """

    # Feature: script-test-suite, Property 9: Language runtime detection

    @given(runtime=st.sampled_from(LANGUAGE_RUNTIMES))
    @settings(max_examples=100)
    def test_single_runtime_no_language_failure(self, runtime):
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)

            mod = _load_check_prereqs()

            # Build a which mock: only the chosen runtime + core tools are present
            def fake_which(cmd):
                if cmd == runtime:
                    return f"/usr/bin/{cmd}"
                # python3/python special handling
                if runtime == "python3" and cmd == "python":
                    return None
                if cmd in ("git", "curl", "zip", "unzip", "pip3", "pip"):
                    return f"/usr/bin/{cmd}"
                return None

            import io
            captured = io.StringIO()
            with patch("check_prerequisites.shutil.which", side_effect=fake_which):
                with patch("check_prerequisites.get_version", return_value="1.0"):
                    with patch("sys.stdout", captured):
                        try:
                            mod.main()
                        except SystemExit:
                            pass

            out = captured.getvalue()
            # Should NOT contain "No supported language runtime"
            assert "No supported language runtime" not in out
        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)
