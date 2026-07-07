"""Unit tests for the ``first_visualization`` progress schema extension.

Feature: module3-first-visualization-guarantee

Covers Task 1.2 — unit tests for the schema extension added to
``validate_progress_schema`` in ``scripts/progress_utils.py``:

- A valid ``first_visualization`` marker (owed and satisfied) passes validation.
- Malformed markers are rejected: bad ``status``, non-ISO ``owed_at`` /
  ``satisfied_at`` timestamps, empty ``satisfied_by``, and a ``satisfied``
  status missing its required ``satisfied_by`` / ``satisfied_at`` fields.
- Legacy progress files without the marker still validate (backward compatible).

Requirements: 1.1, 2.3, 4.3
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import validate_progress_schema


def _legacy_progress() -> dict:
    """Return a minimal, valid legacy progress dict (no first_visualization)."""
    return {
        "current_module": 3,
        "modules_completed": [1, 2],
        "data_sources": ["customers.csv"],
        "database_type": "sqlite",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Valid markers pass
# Requirements: 1.1, 2.3
# ═══════════════════════════════════════════════════════════════════════════


class TestFirstVisualizationValid:
    """Valid first_visualization markers validate cleanly."""

    def test_owed_marker_passes(self):
        """A well-formed owed marker validates with no errors."""
        data = {
            "first_visualization": {
                "status": "owed",
                "reason": "module_3_opt_out",
                "owed_at": "2025-07-15T10:30:00Z",
                "satisfied_by": None,
                "satisfied_at": None,
            }
        }
        assert validate_progress_schema(data) == []

    def test_satisfied_marker_passes(self):
        """A well-formed satisfied marker (non-null satisfied_by/at) validates."""
        data = {
            "first_visualization": {
                "status": "satisfied",
                "reason": "module_3_opt_out",
                "owed_at": "2025-07-15T10:30:00Z",
                "satisfied_by": "standalone_demo",
                "satisfied_at": "2025-07-15T10:45:00Z",
            }
        }
        assert validate_progress_schema(data) == []

    def test_owed_marker_with_null_timestamps_passes(self):
        """owed_at/satisfied_at may be null (only checked when non-null)."""
        data = {
            "first_visualization": {
                "status": "owed",
                "owed_at": None,
                "satisfied_at": None,
                "satisfied_by": None,
            }
        }
        assert validate_progress_schema(data) == []

    def test_empty_marker_dict_passes(self):
        """An empty first_visualization dict is valid (all fields optional)."""
        assert validate_progress_schema({"first_visualization": {}}) == []

    def test_marker_alongside_full_progress_passes(self):
        """A satisfied marker combined with a full legacy progress dict validates."""
        data = _legacy_progress()
        data["first_visualization"] = {
            "status": "satisfied",
            "reason": "module_3_opt_out",
            "owed_at": "2025-07-15T10:30:00Z",
            "satisfied_by": "module_7_deferred",
            "satisfied_at": "2025-07-16T09:00:00Z",
        }
        assert validate_progress_schema(data) == []


# ═══════════════════════════════════════════════════════════════════════════
# Malformed markers are rejected
# Requirements: 1.1, 2.3
# ═══════════════════════════════════════════════════════════════════════════


class TestFirstVisualizationRejected:
    """Malformed first_visualization markers produce validation errors."""

    def test_non_dict_marker_rejected(self):
        """first_visualization must be a dict."""
        errors = validate_progress_schema({"first_visualization": "owed"})
        assert any("first_visualization must be a dict" in e for e in errors)

    def test_bad_status_rejected(self):
        """An unrecognized status value is rejected."""
        errors = validate_progress_schema(
            {"first_visualization": {"status": "pending"}}
        )
        assert any("first_visualization.status must be one of" in e for e in errors)

    def test_non_iso_owed_at_rejected(self):
        """A non-ISO owed_at timestamp is rejected."""
        errors = validate_progress_schema(
            {"first_visualization": {"status": "owed", "owed_at": "yesterday"}}
        )
        assert any(
            "first_visualization.owed_at is not valid ISO 8601" in e for e in errors
        )

    def test_non_iso_satisfied_at_rejected(self):
        """A non-ISO satisfied_at timestamp is rejected."""
        errors = validate_progress_schema(
            {
                "first_visualization": {
                    "status": "satisfied",
                    "satisfied_by": "standalone_demo",
                    "satisfied_at": "not-a-date",
                }
            }
        )
        assert any(
            "first_visualization.satisfied_at is not valid ISO 8601" in e
            for e in errors
        )

    def test_empty_satisfied_by_rejected(self):
        """An empty-string satisfied_by is rejected."""
        errors = validate_progress_schema(
            {"first_visualization": {"satisfied_by": ""}}
        )
        assert any(
            "first_visualization.satisfied_by must be a non-empty string" in e
            for e in errors
        )

    def test_non_string_satisfied_by_rejected(self):
        """A non-string, non-null satisfied_by is rejected."""
        errors = validate_progress_schema(
            {"first_visualization": {"satisfied_by": 123}}
        )
        assert any(
            "first_visualization.satisfied_by must be a non-empty string" in e
            for e in errors
        )

    def test_non_string_timestamp_rejected(self):
        """A non-string, non-null owed_at is rejected."""
        errors = validate_progress_schema(
            {"first_visualization": {"status": "owed", "owed_at": 12345}}
        )
        assert any(
            "first_visualization.owed_at must be a string or null" in e
            for e in errors
        )

    def test_satisfied_missing_satisfied_by_rejected(self):
        """status == satisfied requires a non-null satisfied_by."""
        errors = validate_progress_schema(
            {
                "first_visualization": {
                    "status": "satisfied",
                    "satisfied_at": "2025-07-15T10:45:00Z",
                }
            }
        )
        assert any(
            "first_visualization.satisfied_by must be non-null when status is "
            "'satisfied'" in e
            for e in errors
        )

    def test_satisfied_missing_satisfied_at_rejected(self):
        """status == satisfied requires a non-null satisfied_at."""
        errors = validate_progress_schema(
            {
                "first_visualization": {
                    "status": "satisfied",
                    "satisfied_by": "standalone_demo",
                }
            }
        )
        assert any(
            "first_visualization.satisfied_at must be non-null when status is "
            "'satisfied'" in e
            for e in errors
        )


# ═══════════════════════════════════════════════════════════════════════════
# Backward compatibility — legacy files without the marker still validate
# Requirements: 1.1, 4.3
# ═══════════════════════════════════════════════════════════════════════════


class TestFirstVisualizationBackwardCompat:
    """Legacy progress files without first_visualization validate cleanly."""

    def test_legacy_progress_without_marker_validates(self):
        """A full legacy progress dict (no marker) validates with no errors."""
        assert validate_progress_schema(_legacy_progress()) == []

    def test_empty_dict_validates(self):
        """An empty dict (no marker) validates cleanly."""
        assert validate_progress_schema({}) == []

    def test_minimal_legacy_dict_validates(self):
        """A minimal legacy dict with only core fields validates cleanly."""
        data = {"current_module": 1, "modules_completed": []}
        assert validate_progress_schema(data) == []
