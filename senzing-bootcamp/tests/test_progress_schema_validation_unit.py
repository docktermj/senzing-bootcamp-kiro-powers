"""Unit tests for progress file schema validation.

Covers:
- Task 6.1: Error message format tests for each validator error type
- Task 6.2: Legacy file format tests (backward compatibility)
- Task 6.3: CI script exit code tests (validate_progress_ci.py)
- Task 6.4: Repair tool validation gate tests (repair_progress.py)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import validate_progress_schema
from validate_progress_ci import main as ci_main


# ═══════════════════════════════════════════════════════════════════════════
# Task 6.1 — Error message format tests
# Requirements: 2.2, 2.3, 2.4, 2.5, 2.6
# ═══════════════════════════════════════════════════════════════════════════


class TestErrorMessageFormats:
    """Verify each error message format from the validator."""

    def test_current_module_wrong_type(self):
        """current_module with wrong type produces correct error message."""
        errors = validate_progress_schema({"current_module": "five"})
        assert any("current_module must be an int" in e for e in errors)

    def test_current_module_out_of_range(self):
        """current_module out of range produces correct error message."""
        errors = validate_progress_schema({"current_module": 99})
        assert any("current_module value" in e and "out of range" in e for e in errors)

    def test_modules_completed_wrong_type(self):
        """modules_completed with wrong type produces correct error message."""
        errors = validate_progress_schema({"modules_completed": "not a list"})
        assert any("modules_completed must be a list" in e for e in errors)

    def test_modules_completed_element_out_of_range(self):
        """modules_completed element out of range produces correct error message."""
        errors = validate_progress_schema({"modules_completed": [1, 2, 99]})
        assert any(
            "modules_completed contains value" in e and "out of range" in e
            for e in errors
        )

    def test_track_invalid_value(self):
        """track with invalid value produces correct error message."""
        errors = validate_progress_schema({"track": "invalid_track"})
        assert any("track must be one of" in e for e in errors)

    def test_preferences_wrong_type(self):
        """preferences with wrong type produces correct error message."""
        errors = validate_progress_schema({"preferences": "not a dict"})
        assert any("preferences must be a dict" in e for e in errors)

    def test_preferences_bad_key_type(self):
        """preferences with non-string key produces correct error message."""
        errors = validate_progress_schema({"preferences": {123: "value"}})
        assert any(
            "preferences key" in e and "must be a string" in e for e in errors
        )

    def test_preferences_bad_value_type(self):
        """preferences with invalid value type produces correct error message."""
        errors = validate_progress_schema({"preferences": {"key": 42}})
        assert any(
            "preferences value for key" in e and "must be str or bool" in e
            for e in errors
        )

    def test_session_id_wrong_type(self):
        """session_id with wrong type produces correct error message."""
        errors = validate_progress_schema({"session_id": 12345})
        assert any("session_id must be a non-empty string" in e for e in errors)

    def test_session_id_empty_string(self):
        """session_id as empty string produces correct error message."""
        errors = validate_progress_schema({"session_id": ""})
        assert any("session_id must be a non-empty string" in e for e in errors)

    def test_started_at_wrong_type(self):
        """started_at with wrong type produces correct error message."""
        errors = validate_progress_schema({"started_at": 12345})
        assert any("started_at must be a string" in e for e in errors)

    def test_started_at_invalid_iso(self):
        """started_at with invalid ISO 8601 produces correct error message."""
        errors = validate_progress_schema({"started_at": "not-a-date"})
        assert any("started_at is not valid ISO 8601" in e for e in errors)

    def test_last_activity_wrong_type(self):
        """last_activity with wrong type produces correct error message."""
        errors = validate_progress_schema({"last_activity": 99999})
        assert any("last_activity must be a string" in e for e in errors)

    def test_last_activity_invalid_iso(self):
        """last_activity with invalid ISO 8601 produces correct error message."""
        errors = validate_progress_schema({"last_activity": "yesterday"})
        assert any("last_activity is not valid ISO 8601" in e for e in errors)

    def test_data_sources_wrong_type(self):
        """data_sources with wrong type produces correct error message."""
        errors = validate_progress_schema({"data_sources": "not a list"})
        assert any("data_sources must be a list" in e for e in errors)

    def test_data_sources_non_string_element(self):
        """data_sources with non-string element produces correct error message."""
        errors = validate_progress_schema({"data_sources": ["valid", 123]})
        assert any("data_sources contains non-string element" in e for e in errors)

    def test_database_type_wrong_type(self):
        """database_type with wrong type produces correct error message."""
        errors = validate_progress_schema({"database_type": 42})
        assert any("database_type must be a string" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════════════
# Task 6.2 — Legacy file format tests
# Requirements: 3.1, 3.2, 3.3
# ═══════════════════════════════════════════════════════════════════════════


class TestLegacyFileFormats:
    """Verify backward compatibility with legacy progress file formats."""

    def test_minimal_dict_with_four_required_fields(self):
        """Minimal dict with current_module, modules_completed, data_sources, database_type."""
        data = {
            "current_module": 3,
            "modules_completed": [1, 2],
            "data_sources": ["customers.csv"],
            "database_type": "sqlite",
        }
        errors = validate_progress_schema(data)
        assert errors == []

    def test_dict_with_only_current_module_and_modules_completed(self):
        """Dict with only modules_completed and current_module validates cleanly."""
        data = {
            "current_module": 1,
            "modules_completed": [],
        }
        errors = validate_progress_schema(data)
        assert errors == []

    def test_empty_dict_validates_cleanly(self):
        """Empty dict validates cleanly since all fields are optional in validation."""
        errors = validate_progress_schema({})
        assert errors == []


# ═══════════════════════════════════════════════════════════════════════════
# Task 6.3 — CI script exit code tests
# Requirements: 4.1, 4.2, 4.3, 4.4
# ═══════════════════════════════════════════════════════════════════════════


class TestCIScriptExitCodes:
    """Verify validate_progress_ci.py exit codes for success and failure paths."""

    def test_main_with_valid_progress_file(self, tmp_path):
        """CI script exits 0 when given a valid progress file."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({
                "current_module": 1,
                "modules_completed": [],
                "data_sources": [],
                "database_type": "sqlite",
            }),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as exc_info:
            ci_main([str(progress_file)])
        assert exc_info.value.code == 0

    def test_main_with_invalid_progress_file(self, tmp_path):
        """CI script exits 1 when given an invalid progress file."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({"current_module": "not_an_int"}),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as exc_info:
            ci_main([str(progress_file)])
        assert exc_info.value.code == 1

    def test_main_with_no_file_default_path(self, tmp_path, monkeypatch):
        """CI script exits 0 when default path doesn't exist (validates sample)."""
        # Use a non-existent path so the script falls back to built-in sample
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            ci_main([str(tmp_path / "nonexistent.json")])
        assert exc_info.value.code == 0


# ═══════════════════════════════════════════════════════════════════════════
# Task 6.4 — Repair tool validation gate tests
# Requirements: 7.1, 7.2
# ═══════════════════════════════════════════════════════════════════════════


class TestRepairToolValidationGate:
    """Verify repair tool validates output before writing."""

    def test_repair_fix_on_clean_workspace_produces_valid_output(self, tmp_path, monkeypatch):
        """Repair tool with --fix on a clean workspace produces valid output."""
        monkeypatch.chdir(tmp_path)
        # Create minimal directory structure so detect() finds nothing
        (tmp_path / "config").mkdir()

        import repair_progress

        monkeypatch.setattr(sys, "argv", ["repair_progress.py", "--fix"])
        # The repair tool should produce a valid dict and write it
        # Since no artifacts exist, it will create a minimal valid progress file
        repair_progress.main()
        progress_file = tmp_path / "config" / "bootcamp_progress.json"
        assert progress_file.exists()
        data = json.loads(progress_file.read_text(encoding="utf-8"))
        errors = validate_progress_schema(data)
        assert errors == []

    def test_repair_exits_1_when_validation_fails(self, tmp_path, monkeypatch):
        """Repair tool exits 1 without writing when validate_progress_schema returns errors."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config").mkdir()

        import repair_progress

        monkeypatch.setattr(sys, "argv", ["repair_progress.py", "--fix"])

        # Mock validate_progress_schema to return errors
        with patch(
            "repair_progress.validate_progress_schema",
            return_value=["current_module must be an int, got str"],
        ):
            with pytest.raises(SystemExit) as exc_info:
                repair_progress.main()
            assert exc_info.value.code == 1

        # Verify the file was NOT written
        progress_file = tmp_path / "config" / "bootcamp_progress.json"
        assert not progress_file.exists()
