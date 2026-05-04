"""Unit tests for progress_utils: write_checkpoint, clear_step, validate_progress_schema."""

import json

import pytest

from progress_utils import (
    clear_step,
    parse_parent_step,
    validate_progress_schema,
    write_checkpoint,
)


# ---------------------------------------------------------------------------
# write_checkpoint
# ---------------------------------------------------------------------------


class TestWriteCheckpoint:
    """Tests for write_checkpoint."""

    def test_creates_file_when_missing(self, tmp_path):
        """write_checkpoint creates the progress file if it does not exist."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=3, step=2, progress_path=path)

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

        write_checkpoint(module_number=5, step=4, progress_path=path)

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
        write_checkpoint(module_number=7, step=1, progress_path=path)
        write_checkpoint(module_number=7, step=3, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] == 3
        assert data["step_history"]["7"]["last_completed_step"] == 3

    def test_timestamp_is_valid_iso8601(self, tmp_path):
        """The updated_at value must be a parseable ISO 8601 string."""
        import datetime

        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=1, step=5, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        ts = data["step_history"]["1"]["updated_at"]
        # Should not raise
        datetime.datetime.fromisoformat(ts)

    def test_dotted_sub_step_string(self, tmp_path):
        """write_checkpoint with a dotted sub-step string stores it correctly."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=5, step="5.3", progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] == "5.3"
        assert isinstance(data["current_step"], str)
        assert data["step_history"]["5"]["last_completed_step"] == "5.3"
        assert isinstance(data["step_history"]["5"]["last_completed_step"], str)

    def test_lettered_sub_step_string(self, tmp_path):
        """write_checkpoint with a lettered sub-step string stores it correctly."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=7, step="7a", progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] == "7a"
        assert isinstance(data["current_step"], str)
        assert data["step_history"]["7"]["last_completed_step"] == "7a"
        assert isinstance(data["step_history"]["7"]["last_completed_step"], str)

    def test_integer_step_writes_as_json_integer(self, tmp_path):
        """Integer steps are written as JSON integers, not strings."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=3, step=4, progress_path=path)

        raw = (tmp_path / "progress.json").read_text()
        data = json.loads(raw)
        # Verify the Python type after JSON parsing is int (not str)
        assert isinstance(data["current_step"], int)
        assert data["current_step"] == 4
        assert isinstance(data["step_history"]["3"]["last_completed_step"], int)
        assert data["step_history"]["3"]["last_completed_step"] == 4
        # Verify the raw JSON contains an unquoted integer for current_step
        assert '"current_step": 4' in raw

    def test_string_step_writes_as_json_string(self, tmp_path):
        """String steps are written as JSON strings (quoted)."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=5, step="5.3", progress_path=path)

        raw = (tmp_path / "progress.json").read_text()
        data = json.loads(raw)
        # Verify the Python type after JSON parsing is str
        assert isinstance(data["current_step"], str)
        assert data["current_step"] == "5.3"
        assert isinstance(data["step_history"]["5"]["last_completed_step"], str)
        assert data["step_history"]["5"]["last_completed_step"] == "5.3"
        # Verify the raw JSON contains a quoted string for current_step
        assert '"current_step": "5.3"' in raw


# ---------------------------------------------------------------------------
# clear_step
# ---------------------------------------------------------------------------


class TestClearStep:
    """Tests for clear_step."""

    def test_sets_current_step_to_none(self, tmp_path):
        """clear_step sets current_step to None."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=4, step=6, progress_path=path)
        clear_step(progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] is None

    def test_retains_step_history(self, tmp_path):
        """clear_step keeps the step_history intact."""
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=4, step=6, progress_path=path)
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

    # --- Sub-step identifier validation (Requirements 2.1–2.5) ---

    def test_valid_dotted_sub_step_current_step(self):
        """Dotted sub-step strings like '5.3' and '12.1' pass as current_step."""
        for value in ("5.3", "12.1"):
            assert validate_progress_schema({"current_step": value}) == []

    def test_valid_lettered_sub_step_current_step(self):
        """Lettered sub-step strings like '7a' and '3B' pass as current_step."""
        for value in ("7a", "3B"):
            assert validate_progress_schema({"current_step": value}) == []

    def test_invalid_empty_string_current_step(self):
        """An empty string current_step fails with a descriptive error."""
        errors = validate_progress_schema({"current_step": ""})
        assert len(errors) == 1
        assert "does not match any recognized sub-step format" in errors[0]

    def test_invalid_no_digits_string_current_step(self):
        """A string with no digits like 'abc' fails validation."""
        errors = validate_progress_schema({"current_step": "abc"})
        assert len(errors) == 1
        assert "does not match any recognized sub-step format" in errors[0]

    def test_invalid_nested_dotted_current_step(self):
        """A nested dotted string like '5.3.1' fails (too many dots)."""
        errors = validate_progress_schema({"current_step": "5.3.1"})
        assert len(errors) == 1
        assert "does not match any recognized sub-step format" in errors[0]

    def test_invalid_multi_letter_suffix_current_step(self):
        """A multi-letter suffix like '7ab' fails validation."""
        errors = validate_progress_schema({"current_step": "7ab"})
        assert len(errors) == 1
        assert "does not match any recognized sub-step format" in errors[0]

    def test_integer_current_step_backward_compat(self):
        """Integer current_step values still pass (backward compatibility)."""
        for value in (0, 1, 5, 26):
            assert validate_progress_schema({"current_step": value}) == []

    def test_valid_sub_step_in_step_history(self):
        """A dotted sub-step string as last_completed_step in step_history passes."""
        data = {
            "step_history": {
                "5": {
                    "last_completed_step": "5.3",
                    "updated_at": "2026-06-15T14:30:00+00:00",
                }
            }
        }
        assert validate_progress_schema(data) == []

    def test_invalid_sub_step_in_step_history(self):
        """An invalid string as last_completed_step in step_history fails."""
        data = {
            "step_history": {
                "5": {
                    "last_completed_step": "abc",
                    "updated_at": "2026-06-15T14:30:00+00:00",
                }
            }
        }
        errors = validate_progress_schema(data)
        assert len(errors) == 1
        assert "does not match any recognized sub-step format" in errors[0]

    def test_full_progress_with_sub_steps_valid(self):
        """A complete progress dict with sub-step strings passes validation."""
        data = {
            "modules_completed": [1, 2, 3, 4],
            "current_module": 5,
            "current_step": "5.3",
            "step_history": {
                "5": {
                    "last_completed_step": "5.3",
                    "updated_at": "2026-06-15T14:30:00+00:00",
                },
                "4": {
                    "last_completed_step": 10,
                    "updated_at": "2026-06-14T10:00:00+00:00",
                },
            },
            "data_sources": ["CUSTOMERS"],
            "database_type": "sqlite",
        }
        assert validate_progress_schema(data) == []


# ---------------------------------------------------------------------------
# parse_parent_step
# ---------------------------------------------------------------------------


class TestParseParentStep:
    """Tests for parse_parent_step."""

    def test_none_returns_none(self):
        """parse_parent_step(None) returns None."""
        assert parse_parent_step(None) is None

    def test_integer_returns_same(self):
        """parse_parent_step(5) returns 5."""
        assert parse_parent_step(5) == 5

    def test_dotted_string_returns_parent(self):
        """parse_parent_step('5.3') returns 5."""
        assert parse_parent_step("5.3") == 5

    def test_lettered_string_returns_parent(self):
        """parse_parent_step('7a') returns 7."""
        assert parse_parent_step("7a") == 7

    def test_multi_digit_dotted(self):
        """parse_parent_step('12.1') returns 12."""
        assert parse_parent_step("12.1") == 12

    def test_multi_digit_lettered(self):
        """parse_parent_step('11c') returns 11."""
        assert parse_parent_step("11c") == 11


# ---------------------------------------------------------------------------
# Integration: sub-step checkpoint flow & backward compatibility
# (Tasks 14.1 and 14.2)
# ---------------------------------------------------------------------------


class TestIntegrationSubStepCheckpoint:
    """End-to-end integration tests for sub-step checkpoint flow and backward compatibility.

    Validates Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 5.1, 5.2, 6.1, 7.1,
    8.1, 8.2, 8.3, 8.4.
    """

    def test_integer_checkpoint_validates_clean(self, tmp_path):
        """write_checkpoint with an integer step produces a file that validates with zero errors.

        Validates: Requirements 8.1, 8.3
        """
        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=3, step=5, progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        errors = validate_progress_schema(data)
        assert errors == [], f"Expected zero validation errors, got: {errors}"
        # Confirm the value is an integer (not coerced to string)
        assert isinstance(data["current_step"], int)
        assert data["current_step"] == 5

    def test_clear_step_after_sub_step_checkpoint(self, tmp_path):
        """clear_step after a sub-step checkpoint sets current_step to None and preserves history.

        Validates: Requirements 8.2
        """
        path = str(tmp_path / "progress.json")
        # Write a sub-step checkpoint first
        write_checkpoint(module_number=5, step="5.3", progress_path=path)

        # Verify the sub-step was written
        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] == "5.3"

        # Clear the step
        clear_step(progress_path=path)

        data = json.loads((tmp_path / "progress.json").read_text())
        assert data["current_step"] is None
        # step_history must be preserved with the sub-step value
        assert "5" in data["step_history"]
        assert data["step_history"]["5"]["last_completed_step"] == "5.3"

    def test_sub_step_checkpoint_round_trip(self, tmp_path):
        """Write dotted sub-step '5.3', validate, read back, verify type and value.

        Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2
        """
        import datetime

        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=5, step="5.3", progress_path=path)

        # Read back
        data = json.loads((tmp_path / "progress.json").read_text())

        # Validate — zero errors
        errors = validate_progress_schema(data)
        assert errors == [], f"Expected zero validation errors, got: {errors}"

        # Verify current_step type and value
        assert data["current_step"] == "5.3"
        assert isinstance(data["current_step"], str)

        # Verify step_history round-trip
        assert data["step_history"]["5"]["last_completed_step"] == "5.3"
        assert isinstance(data["step_history"]["5"]["last_completed_step"], str)

        # Verify updated_at is valid ISO 8601
        ts = data["step_history"]["5"]["updated_at"]
        datetime.datetime.fromisoformat(ts)  # raises on invalid

    def test_lettered_sub_step_checkpoint_round_trip(self, tmp_path):
        """Write lettered sub-step '7a', validate, read back, verify type and value.

        Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2
        """
        import datetime

        path = str(tmp_path / "progress.json")
        write_checkpoint(module_number=7, step="7a", progress_path=path)

        # Read back
        data = json.loads((tmp_path / "progress.json").read_text())

        # Validate — zero errors
        errors = validate_progress_schema(data)
        assert errors == [], f"Expected zero validation errors, got: {errors}"

        # Verify current_step type and value
        assert data["current_step"] == "7a"
        assert isinstance(data["current_step"], str)

        # Verify step_history round-trip
        assert data["step_history"]["7"]["last_completed_step"] == "7a"
        assert isinstance(data["step_history"]["7"]["last_completed_step"], str)

        # Verify updated_at is valid ISO 8601
        ts = data["step_history"]["7"]["updated_at"]
        datetime.datetime.fromisoformat(ts)  # raises on invalid

    def test_steering_files_contain_sub_step_docs(self):
        """Verify steering files contain expected sub-step documentation strings.

        Validates: Requirements 5.1, 5.2, 6.1, 7.1
        """
        from pathlib import Path

        steering_dir = Path(__file__).resolve().parent.parent / "steering"

        # agent-instructions.md: must reference sub-step identifiers or checkpoints
        ai_path = steering_dir / "agent-instructions.md"
        ai_content = ai_path.read_text(encoding="utf-8")
        assert "sub-step identifier" in ai_content or "sub-step checkpoint" in ai_content, (
            "agent-instructions.md should contain 'sub-step identifier' or 'sub-step checkpoint'"
        )

        # session-resume.md: must reference sub-step identifiers or parse_parent_step
        sr_path = steering_dir / "session-resume.md"
        sr_content = sr_path.read_text(encoding="utf-8")
        assert "sub-step identifier" in sr_content or "parse_parent_step" in sr_content, (
            "session-resume.md should contain 'sub-step identifier' or 'parse_parent_step'"
        )

        # module-transitions.md: must reference sub-step identifiers
        mt_path = steering_dir / "module-transitions.md"
        mt_content = mt_path.read_text(encoding="utf-8")
        assert "sub-step identifier" in mt_content, (
            "module-transitions.md should contain 'sub-step identifier'"
        )

        # phase-loading-guide.md: must reference parse_parent_step or sub-step identifiers
        plg_path = steering_dir / "phase-loading-guide.md"
        plg_content = plg_path.read_text(encoding="utf-8")
        assert "parse_parent_step" in plg_content or "sub-step identifier" in plg_content, (
            "phase-loading-guide.md should contain 'parse_parent_step' or 'sub-step identifier'"
        )

    def test_repair_progress_produces_integer_steps(self):
        """Verify repair_progress.py does not reference sub-step identifiers.

        It should continue to produce integer current_step values when
        reconstructing progress from artifacts (Requirement 8.4).
        """
        from pathlib import Path

        repair_path = (
            Path(__file__).resolve().parent.parent / "scripts" / "repair_progress.py"
        )
        assert repair_path.exists(), "repair_progress.py should exist"

        content = repair_path.read_text(encoding="utf-8")
        # repair_progress.py should NOT contain sub-step identifier references
        # because artifact scanning cannot determine sub-step positions
        assert "sub-step" not in content.lower(), (
            "repair_progress.py should not reference sub-step identifiers"
        )
        assert "parse_parent_step" not in content, (
            "repair_progress.py should not use parse_parent_step"
        )
        assert "_is_valid_sub_step_identifier" not in content, (
            "repair_progress.py should not use _is_valid_sub_step_identifier"
        )

    def test_legacy_integer_only_progress_validates(self):
        """A legacy progress file with integer-only values validates with zero errors.

        Validates: Requirements 8.1, 8.3
        """
        data = {
            "modules_completed": [1, 2, 3],
            "current_module": 4,
            "current_step": 3,
            "step_history": {
                "1": {
                    "last_completed_step": 10,
                    "updated_at": "2026-05-01T10:00:00+00:00",
                },
                "2": {
                    "last_completed_step": 6,
                    "updated_at": "2026-05-05T12:00:00+00:00",
                },
                "3": {
                    "last_completed_step": 4,
                    "updated_at": "2026-05-10T14:30:00+00:00",
                },
            },
            "data_sources": ["CUSTOMERS"],
            "database_type": "sqlite",
        }
        errors = validate_progress_schema(data)
        assert errors == [], f"Legacy integer-only progress should validate cleanly, got: {errors}"
