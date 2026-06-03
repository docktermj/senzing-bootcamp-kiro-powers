"""Unit tests for preferences schema CI validation script.

Covers:
- Task 5.2: CI script exit code tests (validate_preferences_ci.py)
  - Test exit code 0 with valid file
  - Test exit code 1 with invalid file
  - Test fallback to built-in sample when file missing
  - Test self-consistency check
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_preferences_ci import _check_schema_consistency, main

# ═══════════════════════════════════════════════════════════════════════════
# Task 5.2 — CI script unit tests
# Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
# ═══════════════════════════════════════════════════════════════════════════


class TestValidatePreferencesCi:
    """Verify validate_preferences_ci.py exit codes and behavior."""

    def test_exit_code_0_with_valid_file(self, tmp_path):
        """CI script exits 0 when given a valid preferences YAML file.

        Validates: Req 5.2, 5.5
        """
        valid_file = tmp_path / "prefs.yaml"
        valid_file.write_text("database_type: sqlite\n", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            main([str(valid_file)])
        assert exc_info.value.code == 0

    def test_exit_code_1_with_invalid_file(self, tmp_path):
        """CI script exits 1 when given a file with unknown keys.

        Validates: Req 5.2, 5.6
        """
        invalid_file = tmp_path / "prefs.yaml"
        invalid_file.write_text(
            "unknown_key: value\ndatabase_type: sqlite\n", encoding="utf-8"
        )
        with pytest.raises(SystemExit) as exc_info:
            main([str(invalid_file)])
        assert exc_info.value.code == 1

    def test_fallback_to_builtin_sample_when_file_missing(self):
        """CI script exits 0 when file does not exist (validates built-in sample).

        Validates: Req 5.3
        """
        with pytest.raises(SystemExit) as exc_info:
            main(["/nonexistent/path/to/file.yaml"])
        assert exc_info.value.code == 0

    def test_self_consistency_check(self):
        """Schema self-consistency check returns no errors.

        Validates: Req 5.4
        """
        errors = _check_schema_consistency()
        assert errors == []
