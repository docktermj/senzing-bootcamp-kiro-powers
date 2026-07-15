"""Unit tests for the ``setup_summary`` progress schema extension.

Feature: setup-summary-persistence

Covers Task 4 — light validation of the ``setup_summary`` block added to
``validate_progress_schema`` in ``scripts/progress_utils.py``:

- A well-formed ``setup_summary`` block (full and minimal) passes validation.
- A missing block still validates (backward compatible — older projects and
  sessions where the onboarding write was skipped or failed).
- Malformed blocks are rejected: wrong container type, non-string string
  fields, a bad ``preflight_verdict`` enum value, non-boolean flags,
  array fields that are not arrays of strings, a boolean masquerading as the
  ``hooks_installed.count`` integer, a negative count, non-string ``names``
  elements, and any secret-like field.

Requirements: 3.1
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
    """Return a minimal, valid legacy progress dict (no setup_summary)."""
    return {
        "current_module": 3,
        "modules_completed": [1, 2],
        "data_sources": ["customers.csv"],
        "database_type": "sqlite",
    }


def _valid_setup_summary() -> dict:
    """Return a well-formed setup_summary block mirroring the documented example."""
    return {
        "captured_at": "2026-07-14T13:49:00-05:00",
        "power_version": "1.4.0",
        "mcp_reachable": True,
        "directories_created": True,
        "hooks_installed": {
            "count": 3,
            "names": ["ask-bootcamper", "review-bootcamper-input", "code-style-check"],
        },
        "steering_generated": ["product.md", "tech.md", "structure.md"],
        "preflight_verdict": "WARN",
        "preflight_warnings": ["Senzing SDK not installed — Module 2 will cover it"],
        "deferrals": ["runtime install declined (revisit in Module 2)"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# Valid blocks pass
# Requirements: 3.1
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryValid:
    """Well-formed setup_summary blocks validate cleanly."""

    def test_full_block_passes(self):
        """A complete, well-formed block validates with no errors."""
        assert validate_progress_schema({"setup_summary": _valid_setup_summary()}) == []

    def test_full_block_with_pass_verdict_passes(self):
        """preflight_verdict may be PASS."""
        ss = _valid_setup_summary()
        ss["preflight_verdict"] = "PASS"
        assert validate_progress_schema({"setup_summary": ss}) == []

    def test_full_block_with_fail_verdict_passes(self):
        """preflight_verdict may be FAIL."""
        ss = _valid_setup_summary()
        ss["preflight_verdict"] = "FAIL"
        assert validate_progress_schema({"setup_summary": ss}) == []

    def test_empty_block_passes(self):
        """An empty setup_summary dict is valid (all fields optional / light)."""
        assert validate_progress_schema({"setup_summary": {}}) == []

    def test_minimal_block_passes(self):
        """A block with only a subset of fields validates (light validation)."""
        data = {
            "setup_summary": {
                "power_version": "2.0.0",
                "preflight_verdict": "PASS",
            }
        }
        assert validate_progress_schema(data) == []

    def test_empty_lists_and_zero_count_pass(self):
        """Empty arrays and a zero hook count are valid."""
        data = {
            "setup_summary": {
                "hooks_installed": {"count": 0, "names": []},
                "steering_generated": [],
                "preflight_warnings": [],
                "deferrals": [],
            }
        }
        assert validate_progress_schema(data) == []

    def test_block_alongside_full_progress_passes(self):
        """A valid block combined with a full legacy progress dict validates."""
        data = _legacy_progress()
        data["setup_summary"] = _valid_setup_summary()
        assert validate_progress_schema(data) == []


# ═══════════════════════════════════════════════════════════════════════════
# Backward compatibility — a missing block still validates
# Requirements: 3.1
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryBackwardCompat:
    """Legacy progress files without setup_summary validate cleanly."""

    def test_legacy_progress_without_block_validates(self):
        """A full legacy progress dict (no block) validates with no errors."""
        assert validate_progress_schema(_legacy_progress()) == []

    def test_empty_dict_validates(self):
        """An empty dict (no block) validates cleanly."""
        assert validate_progress_schema({}) == []


# ═══════════════════════════════════════════════════════════════════════════
# Malformed blocks are rejected
# Requirements: 3.1
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryRejected:
    """Malformed setup_summary blocks produce clear validation errors."""

    def test_non_dict_block_rejected(self):
        """setup_summary must be a dict."""
        errors = validate_progress_schema({"setup_summary": "done"})
        assert any("setup_summary must be a dict" in e for e in errors)

    def test_non_string_captured_at_rejected(self):
        """captured_at must be a string."""
        errors = validate_progress_schema({"setup_summary": {"captured_at": 12345}})
        assert any("setup_summary.captured_at must be a string" in e for e in errors)

    def test_non_string_power_version_rejected(self):
        """power_version must be a string."""
        errors = validate_progress_schema({"setup_summary": {"power_version": 1.4}})
        assert any("setup_summary.power_version must be a string" in e for e in errors)

    def test_bad_preflight_verdict_rejected(self):
        """An unrecognized preflight_verdict value is rejected."""
        errors = validate_progress_schema(
            {"setup_summary": {"preflight_verdict": "MAYBE"}}
        )
        assert any(
            "setup_summary.preflight_verdict must be one of" in e for e in errors
        )

    def test_non_string_preflight_verdict_rejected(self):
        """A non-string preflight_verdict is rejected as a type error."""
        errors = validate_progress_schema(
            {"setup_summary": {"preflight_verdict": True}}
        )
        assert any("setup_summary.preflight_verdict must be a string" in e for e in errors)

    def test_non_boolean_mcp_reachable_rejected(self):
        """mcp_reachable must be a boolean (a string is not accepted)."""
        errors = validate_progress_schema(
            {"setup_summary": {"mcp_reachable": "true"}}
        )
        assert any("setup_summary.mcp_reachable must be a boolean" in e for e in errors)

    def test_non_boolean_directories_created_rejected(self):
        """directories_created must be a boolean (an int is not accepted)."""
        errors = validate_progress_schema(
            {"setup_summary": {"directories_created": 1}}
        )
        assert any(
            "setup_summary.directories_created must be a boolean" in e for e in errors
        )

    def test_non_list_steering_generated_rejected(self):
        """steering_generated must be a list."""
        errors = validate_progress_schema(
            {"setup_summary": {"steering_generated": "product.md"}}
        )
        assert any("setup_summary.steering_generated must be a list" in e for e in errors)

    def test_non_string_steering_element_rejected(self):
        """steering_generated elements must be strings."""
        errors = validate_progress_schema(
            {"setup_summary": {"steering_generated": ["product.md", 42]}}
        )
        assert any(
            "setup_summary.steering_generated contains non-string element" in e
            for e in errors
        )

    def test_non_string_deferral_element_rejected(self):
        """deferrals elements must be strings."""
        errors = validate_progress_schema(
            {"setup_summary": {"deferrals": [None]}}
        )
        assert any(
            "setup_summary.deferrals contains non-string element" in e for e in errors
        )

    def test_non_dict_hooks_installed_rejected(self):
        """hooks_installed must be a dict."""
        errors = validate_progress_schema(
            {"setup_summary": {"hooks_installed": ["ask-bootcamper"]}}
        )
        assert any("setup_summary.hooks_installed must be a dict" in e for e in errors)

    def test_boolean_hooks_count_rejected(self):
        """A boolean must not be accepted where the integer count is expected."""
        errors = validate_progress_schema(
            {"setup_summary": {"hooks_installed": {"count": True}}}
        )
        assert any(
            "setup_summary.hooks_installed.count must be an int" in e for e in errors
        )

    def test_non_int_hooks_count_rejected(self):
        """hooks_installed.count must be an int."""
        errors = validate_progress_schema(
            {"setup_summary": {"hooks_installed": {"count": "3"}}}
        )
        assert any(
            "setup_summary.hooks_installed.count must be an int" in e for e in errors
        )

    def test_negative_hooks_count_rejected(self):
        """hooks_installed.count must be non-negative."""
        errors = validate_progress_schema(
            {"setup_summary": {"hooks_installed": {"count": -1}}}
        )
        assert any(
            "setup_summary.hooks_installed.count must be non-negative" in e
            for e in errors
        )

    def test_non_string_hooks_name_rejected(self):
        """hooks_installed.names elements must be strings."""
        errors = validate_progress_schema(
            {"setup_summary": {"hooks_installed": {"names": ["ask-bootcamper", 7]}}}
        )
        assert any(
            "setup_summary.hooks_installed.names contains non-string element" in e
            for e in errors
        )

    def test_non_list_hooks_names_rejected(self):
        """hooks_installed.names must be a list."""
        errors = validate_progress_schema(
            {"setup_summary": {"hooks_installed": {"names": "ask-bootcamper"}}}
        )
        assert any(
            "setup_summary.hooks_installed.names must be a list" in e for e in errors
        )

    def test_secret_like_field_rejected(self):
        """A secret-like key (e.g. api_token) is rejected by the secret-free rule."""
        ss = _valid_setup_summary()
        ss["api_token"] = "abc123"
        errors = validate_progress_schema({"setup_summary": ss})
        assert any("secret-like field" in e for e in errors)

    def test_connection_string_field_rejected(self):
        """A connection-string key is rejected by the secret-free rule."""
        errors = validate_progress_schema(
            {"setup_summary": {"db_connection": "postgres://user:pw@host/db"}}
        )
        assert any("secret-like field" in e for e in errors)

    def test_password_field_rejected(self):
        """A password key is rejected by the secret-free rule."""
        errors = validate_progress_schema(
            {"setup_summary": {"password": "hunter2"}}
        )
        assert any("secret-like field" in e for e in errors)

    def test_credential_field_rejected(self):
        """A credentials key is rejected by the secret-free rule."""
        errors = validate_progress_schema(
            {"setup_summary": {"credentials": {"user": "x"}}}
        )
        assert any("secret-like field" in e for e in errors)
