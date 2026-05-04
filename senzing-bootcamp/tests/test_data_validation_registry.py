"""Unit tests for the update_registry function in validate_data_files.py.

Verifies new registry creation, existing entry updates, validation fields,
and updated_at timestamp handling.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from data_sources import parse_registry_yaml
from validate_data_files import (
    CheckResult,
    ValidationReport,
    update_registry,
)


# ── Helpers ───────────────────────────────────────────────────────────────


def _make_report(
    file_name: str = "customer_crm.csv",
    overall_status: str = "pass",
    record_count: int | None = 500,
    encoding: str | None = "utf-8",
    checks: list[CheckResult] | None = None,
) -> ValidationReport:
    """Build a ValidationReport with sensible defaults."""
    if checks is None:
        checks = [
            CheckResult("existence", "pass", "File exists", "", {}),
            CheckResult("format", "pass", "Recognized format: csv", "", {}),
            CheckResult("records", "pass", "Found 500 records", "", {}),
            CheckResult("encoding", "pass", "Encoding: utf-8", "", {}),
        ]
    return ValidationReport(
        file_path=f"data/raw/{file_name}",
        file_name=file_name,
        format="csv",
        record_count=record_count,
        encoding=encoding,
        checks=checks,
        overall_status=overall_status,
    )


def _read_registry(path: Path) -> dict:
    """Read and parse a registry YAML file."""
    content = path.read_text(encoding="utf-8")
    return parse_registry_yaml(content)


# ── Tests ─────────────────────────────────────────────────────────────────


class TestRegistryCreation:
    """Test that update_registry creates a new registry when none exists."""

    def test_creates_registry_file_when_missing(self, tmp_path):
        """Requirement 7.6: create registry with version '1' and empty sources."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        assert not registry_path.exists()

        report = _make_report()
        update_registry([report], str(registry_path))

        assert registry_path.exists()

    def test_new_registry_has_version_1(self, tmp_path):
        """Requirement 7.6: new registry has version '1'."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report()
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        assert str(data["version"]) == "1"

    def test_new_registry_has_sources_mapping(self, tmp_path):
        """Requirement 7.6: new registry has sources mapping."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report()
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        assert isinstance(data["sources"], dict)
        assert "CUSTOMER_CRM" in data["sources"]


class TestExistingEntryUpdate:
    """Test that update_registry updates existing entries correctly."""

    def test_updates_existing_entry(self, tmp_path):
        """Requirement 7.1: update existing entry with validation_status."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            'version: "1"\n'
            "sources:\n"
            "  CUSTOMER_CRM:\n"
            "    name: Customer CRM\n"
            '    file_path: "data/raw/customer_crm.csv"\n'
            "    format: csv\n"
            "    record_count: 100\n",
            encoding="utf-8",
        )

        report = _make_report(record_count=500)
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert entry["name"] == "Customer CRM"
        assert entry["validation_status"] == "passed"
        assert entry["record_count"] == 500

    def test_preserves_other_entries(self, tmp_path):
        """Existing entries not in reports are preserved."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            'version: "1"\n'
            "sources:\n"
            "  OTHER_SOURCE:\n"
            "    name: Other\n"
            "    format: json\n",
            encoding="utf-8",
        )

        report = _make_report()
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        assert "OTHER_SOURCE" in data["sources"]
        assert "CUSTOMER_CRM" in data["sources"]


class TestValidationFields:
    """Test that validation fields are written correctly."""

    def test_validation_status_passed(self, tmp_path):
        """Requirement 7.1: validation_status is 'passed' for passing reports."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(overall_status="pass")
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert entry["validation_status"] == "passed"

    def test_validation_status_failed(self, tmp_path):
        """Requirement 7.1: validation_status is 'failed' for failing reports."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        checks = [
            CheckResult("existence", "pass", "File exists", "", {}),
            CheckResult("format", "fail", "Bad format", "Fix it", {}),
        ]
        report = _make_report(overall_status="fail", checks=checks)
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert entry["validation_status"] == "failed"

    def test_validation_checks_mapping(self, tmp_path):
        """Requirement 7.2: validation_checks has correct check names and statuses."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        checks = [
            CheckResult("existence", "pass", "OK", "", {}),
            CheckResult("format", "pass", "OK", "", {}),
            CheckResult("records", "pass", "OK", "", {}),
            CheckResult("encoding", "warn", "Non-UTF8", "", {}),
        ]
        report = _make_report(checks=checks)
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        vc = entry["validation_checks"]
        assert isinstance(vc, dict)
        assert vc["existence"] == "pass"
        assert vc["format"] == "pass"
        assert vc["records"] == "pass"
        assert vc["encoding"] == "warn"

    def test_record_count_set(self, tmp_path):
        """Requirement 7.3: record_count is set from report."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(record_count=42000)
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert entry["record_count"] == 42000

    def test_encoding_set(self, tmp_path):
        """Requirement 7.4: encoding is set from report."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(encoding="utf-8")
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert entry["encoding"] == "utf-8"

    def test_record_count_not_set_when_none(self, tmp_path):
        """record_count is not written when report has None."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(record_count=None)
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert "record_count" not in entry

    def test_encoding_not_set_when_none(self, tmp_path):
        """encoding is not written when report has None."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(encoding=None)
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert "encoding" not in entry


class TestUpdatedAtTimestamp:
    """Test that updated_at timestamp is set correctly."""

    def test_updated_at_is_set(self, tmp_path):
        """Requirement 7.5: updated_at timestamp is set."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report()
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        assert "updated_at" in entry
        assert entry["updated_at"] is not None

    def test_updated_at_is_valid_iso8601(self, tmp_path):
        """Requirement 7.5: updated_at is a valid ISO 8601 timestamp."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report()
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        entry = data["sources"]["CUSTOMER_CRM"]
        ts = entry["updated_at"]
        # Should parse without error
        parsed = datetime.fromisoformat(str(ts))
        assert parsed.tzinfo is not None  # Should have timezone info


class TestDataSourceKeyDerivation:
    """Test that DATA_SOURCE keys are derived correctly from file names."""

    def test_csv_file_key(self, tmp_path):
        """customer_crm.csv → CUSTOMER_CRM"""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(file_name="customer_crm.csv")
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        assert "CUSTOMER_CRM" in data["sources"]

    def test_json_file_key(self, tmp_path):
        """vendor-data.json → VENDOR_DATA"""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(file_name="vendor-data.json")
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        assert "VENDOR_DATA" in data["sources"]

    def test_file_with_dots_in_name(self, tmp_path):
        """my.data.file.csv → MY_DATA_FILE"""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        report = _make_report(file_name="my.data.file.csv")
        update_registry([report], str(registry_path))

        data = _read_registry(registry_path)
        assert "MY_DATA_FILE" in data["sources"]

    def test_multiple_reports(self, tmp_path):
        """Multiple reports create multiple entries."""
        registry_path = tmp_path / "config" / "data_sources.yaml"
        reports = [
            _make_report(file_name="source_a.csv"),
            _make_report(file_name="source_b.json"),
        ]
        update_registry(reports, str(registry_path))

        data = _read_registry(registry_path)
        assert "SOURCE_A" in data["sources"]
        assert "SOURCE_B" in data["sources"]
