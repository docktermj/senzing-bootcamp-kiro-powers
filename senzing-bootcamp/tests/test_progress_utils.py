"""Unit tests for progress_utils: write_checkpoint, clear_step, validate_progress_schema."""

import json

import pytest

from progress_utils import clear_step, validate_progress_schema, write_checkpoint


# ---------------------------------------------------------------------------
# write_checkpoint
# ---------------------------------------------------------------------------


class TestWriteCheckpoint:
    """Tests for write_checkpoint."""

    def test_creates_file_when_missing(self, tmp_path):
        """write_checkpoint creates the progress file if it does not exist."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=3, step_number=2, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] == 2
        assert data["step_history"]["3"]["last_completed_step"] == 2
        assert "updated_at" in data["step_history"]["3"]

    def test_updates_existing_file(self, tmp_path):
        """write_checkpoint preserves existing fields and updates step data."""
        path = str(tmp_path / "progress.json")
        initial = {
            "modules_completed": [1, 2],
            "current_module": 5,
            "data_sources": [],
            "database_type": "sqlite",
        }
        (tmp_path / "progress.json").write_text(json.dumps(initial))

        write_checkpoint(module_number=5, step_number=4, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        # Existing fields retained
        assert data["modules_completed"] == [1, 2]
        assert data["current_module"] == 5
        # Step fields written
        assert data["current_step"] == 4
        assert data["step_history"]["5"]["last_completed_step"] == 4

    def test_overwrites_previous_step(self, tmp_path):
        """A second checkpoint overwrites current_step and the history entry."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=7, step_number=1, progress_path=path)
        write_checkpoint(module_number=7, step_number=3, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] == 3
        assert data["step_history"]["7"]["last_completed_step"] == 3

    def test_timestamp_is_valid_iso8601(self, tmp_path):
        """The updated_at value must be a parseable ISO 8601 string."""
        import datetime

        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=1, step_number=5, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        ts = data["step_history"]["1"]["updated_at"]
        # Should not raise
        datetime.datetime.fromisoformat(ts)


# ---------------------------------------------------------------------------
# clear_step
# ---------------------------------------------------------------------------


class TestClearStep:
    """Tests for clear_step."""

    def test_sets_current_step_to_none(self, tmp_path):
        """clear_step sets current_step to None."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=4, step_number=6, progress_path=path)
        clear_step(progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] is None

    def test_retains_step_history(self, tmp_path):
        """clear_step keeps the step_history intact."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=4, step_number=6, progress_path=path)
        clear_step(progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert "4" in data["step_history"]
        assert data["step_history"]["4"]["last_completed_step"] == 6


# ---------------------------------------------------------------------------
# validate_progress_schema
# ---------------------------------------------------------------------------


class TestValidateProgressSchema:
    """Tests for validate_progress_schema."""

    def test_valid_data_returns_empty_list(self):
        """A fully valid progress dict produces no errors."""
        data = {
            "modules_completed": [1, 2],
            "current_module": 3,
            "current_step": 5,
            "step_history": {
                "3": {
                    "last_completed_step": 5,
                    "updated_at": "2026-05-10T14:30:00+00:00",
                }
            },
            "data_sources": [],
            "database_type": "sqlite",
        }
        assert validate_progress_schema(data) == []

    def test_legacy_data_without_step_fields(self):
        """A legacy file lacking current_step and step_history is valid."""
        data = {
            "modules_completed": [1],
            "current_module": 2,
            "data_sources": [],
            "database_type": "sqlite",
        }
        assert validate_progress_schema(data) == []

    def test_current_step_null_is_valid(self):
        """current_step set to None is valid."""
        assert validate_progress_schema({"current_step": None}) == []

    def test_invalid_current_step_type(self):
        """current_step as a string should produce an error."""
        errors = validate_progress_schema({"current_step": "three"})
        assert len(errors) == 1
        assert "current_step" in errors[0]

    def test_invalid_step_history_key(self):
        """A non-integer string key in step_history should produce an error."""
        data = {
            "step_history": {
                "abc": {
                    "last_completed_step": 1,
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            }
        }
        errors = validate_progress_schema(data)
        assert any("abc" in e for e in errors)

    def test_step_history_key_out_of_range(self):
        """A key outside 1-12 should produce an error."""
        data = {
            "step_history": {
                "13": {
                    "last_completed_step": 1,
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
            }
        }
        errors = validate_progress_schema(data)
        assert any("out of range" in e for e in errors)

    def test_missing_required_fields_in_entry(self):
        """An entry missing last_completed_step and updated_at should produce errors."""
        data = {"step_history": {"1": {}}}
        errors = validate_progress_schema(data)
        assert any("last_completed_step" in e for e in errors)
        assert any("updated_at" in e for e in errors)

    def test_invalid_iso8601_timestamp(self):
        """A malformed updated_at should produce an error."""
        data = {
            "step_history": {
                "2": {
                    "last_completed_step": 3,
                    "updated_at": "not-a-date",
                }
            }
        }
        errors = validate_progress_schema(data)
        assert any("ISO 8601" in e for e in errors)
