"""Unit tests for ``first_visualization`` marker error handling.

Feature: module3-first-visualization-guarantee

Covers Task 2.4 — error-handling and no-op paths of the marker helper in
``scripts/progress_utils.py``:

- Missing file: ``mark_first_visualization_owed`` on a non-existent path
  creates the file with an owed marker (parent dir auto-created).
- Empty file / empty dict ``{}``: treated as "no marker"; marking creates an
  owed marker.
- Invalid JSON: ``mark_first_visualization_owed`` raises
  ``json.JSONDecodeError`` and does NOT overwrite / partial-write the file.
- Monotonic no-op: marking when already ``satisfied`` leaves it satisfied;
  marking when already ``owed`` leaves ``owed_at`` unchanged.
- Never-owed clear no-op: ``clear_first_visualization_owed`` on an absent
  marker leaves no marker; on an already-satisfied marker leaves it unchanged.

Requirements: 2.3, 4.1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import (  # noqa: E402
    clear_first_visualization_owed,
    is_first_visualization_owed,
    mark_first_visualization_owed,
)


class TestMarkMissingOrEmptyFile:
    """Missing / empty progress files are treated as an empty dict."""

    def test_mark_on_missing_file_creates_owed_marker(self, tmp_path):
        # File does not exist, and neither does its parent directory.
        progress_path = tmp_path / "nested" / "config" / "bootcamp_progress.json"
        assert not progress_path.exists()

        mark_first_visualization_owed(progress_path=str(progress_path))

        assert progress_path.is_file()
        data = json.loads(progress_path.read_text(encoding="utf-8"))
        marker = data["first_visualization"]
        assert marker["status"] == "owed"
        assert marker["reason"] == "module_3_opt_out"
        assert marker["owed_at"] is not None
        assert marker["satisfied_by"] is None
        assert marker["satisfied_at"] is None
        assert is_first_visualization_owed(data) is True

    def test_mark_on_empty_dict_file_creates_owed_marker(self, tmp_path):
        # A file containing an empty JSON object is treated as "no marker".
        progress_path = tmp_path / "bootcamp_progress.json"
        progress_path.write_text("{}", encoding="utf-8")

        mark_first_visualization_owed(progress_path=str(progress_path))

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        assert data["first_visualization"]["status"] == "owed"
        assert is_first_visualization_owed(data) is True

    def test_mark_preserves_unrelated_fields(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        progress_path.write_text(
            json.dumps({"current_module": 3, "modules_completed": [1, 2]}),
            encoding="utf-8",
        )

        mark_first_visualization_owed(progress_path=str(progress_path))

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        assert data["current_module"] == 3
        assert data["modules_completed"] == [1, 2]
        assert data["first_visualization"]["status"] == "owed"


class TestInvalidJson:
    """Invalid JSON surfaces an error without a partial write."""

    def test_mark_on_invalid_json_raises_without_overwrite(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        original = "{ this is not valid json ]"
        progress_path.write_text(original, encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            mark_first_visualization_owed(progress_path=str(progress_path))

        # The file must be left exactly as it was — no partial write.
        assert progress_path.read_text(encoding="utf-8") == original

    def test_clear_on_invalid_json_raises_without_overwrite(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        original = "not json at all"
        progress_path.write_text(original, encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            clear_first_visualization_owed(
                satisfied_by="standalone_demo", progress_path=str(progress_path)
            )

        assert progress_path.read_text(encoding="utf-8") == original


class TestMonotonicNoOp:
    """Marking never regresses and never mutates an existing owed marker."""

    def test_mark_when_satisfied_is_noop(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        satisfied = {
            "first_visualization": {
                "status": "satisfied",
                "reason": "module_3_opt_out",
                "owed_at": "2025-07-15T10:30:00+00:00",
                "satisfied_by": "standalone_demo",
                "satisfied_at": "2025-07-15T11:00:00+00:00",
            }
        }
        progress_path.write_text(json.dumps(satisfied), encoding="utf-8")

        mark_first_visualization_owed(progress_path=str(progress_path))

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        assert data["first_visualization"] == satisfied["first_visualization"]
        assert is_first_visualization_owed(data) is False

    def test_mark_when_already_owed_leaves_owed_at_unchanged(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        owed = {
            "first_visualization": {
                "status": "owed",
                "reason": "module_3_opt_out",
                "owed_at": "2025-07-15T10:30:00+00:00",
                "satisfied_by": None,
                "satisfied_at": None,
            }
        }
        progress_path.write_text(json.dumps(owed), encoding="utf-8")

        mark_first_visualization_owed(progress_path=str(progress_path))

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        # The existing owed marker (and its owed_at) is left untouched.
        assert data["first_visualization"] == owed["first_visualization"]


class TestNeverOwedClearNoOp:
    """Clearing a marker that was never owed is a no-op."""

    def test_clear_on_absent_marker_leaves_no_marker(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        progress_path.write_text(
            json.dumps({"current_module": 4}), encoding="utf-8"
        )

        clear_first_visualization_owed(
            satisfied_by="module_6_deferred", progress_path=str(progress_path)
        )

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        assert "first_visualization" not in data
        assert is_first_visualization_owed(data) is False

    def test_clear_on_missing_file_creates_no_marker(self, tmp_path):
        # No file at all: clearing must not fabricate an owed->satisfied history.
        progress_path = tmp_path / "bootcamp_progress.json"

        clear_first_visualization_owed(
            satisfied_by="module_7_deferred", progress_path=str(progress_path)
        )

        # Absent marker means nothing to clear; the helper writes nothing.
        assert not progress_path.exists()

    def test_clear_on_already_satisfied_leaves_it_unchanged(self, tmp_path):
        progress_path = tmp_path / "bootcamp_progress.json"
        satisfied = {
            "first_visualization": {
                "status": "satisfied",
                "reason": "module_3_opt_out",
                "owed_at": "2025-07-15T10:30:00+00:00",
                "satisfied_by": "standalone_demo",
                "satisfied_at": "2025-07-15T11:00:00+00:00",
            }
        }
        progress_path.write_text(json.dumps(satisfied), encoding="utf-8")

        clear_first_visualization_owed(
            satisfied_by="module_6_deferred", progress_path=str(progress_path)
        )

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        # satisfied_by is not overwritten by a later clear.
        assert data["first_visualization"] == satisfied["first_visualization"]
